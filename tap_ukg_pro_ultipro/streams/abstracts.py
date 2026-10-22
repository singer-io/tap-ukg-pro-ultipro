from abc import ABC, abstractmethod
import json
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, List, Iterator
from singer import (
    Transformer,
    get_bookmark,
    get_logger,
    metrics,
    write_bookmark,
    write_record,
    write_schema,
    metadata
)
from singer.utils import strftime, strptime_to_utc

from tap_ukg_pro_ultipro.exceptions import UKGProError, UKGProForbiddenError

LOGGER = get_logger()


def parse_datetime(value: Any) -> Optional[datetime]:
    """Parse a datetime value into a UTC datetime, returning None when it cannot be parsed."""
    try:
        return strptime_to_utc(value)
    except (TypeError, ValueError, OverflowError):
        return None


def validate_bookmark_state(state: Any, stream: str) -> None:
    """
    Confirm the state has the structure `{"bookmarks": {<stream>: {<replication_key>: value}}}`.

    A missing `bookmarks` key, or a missing entry for the stream, is valid (first sync).
    """
    if not isinstance(state, dict):
        raise UKGProError("The state must be a JSON object.")
    bookmarks = state.get("bookmarks", {})
    if not isinstance(bookmarks, dict):
        raise UKGProError("Invalid state: 'bookmarks' must be an object keyed by stream name.")
    if stream in bookmarks and not isinstance(bookmarks[stream], dict):
        raise UKGProError(
            "Invalid state: the bookmark of stream '{}' must be an object keyed by replication key.".format(
                stream
            )
        )


class BaseStream(ABC):
    """
    A Base Class providing structure and boilerplate for generic streams
    and required attributes for any kind of stream
    ~~~
    Provides:
     - Basic Attributes (stream_name,replication_method,key_properties)
     - Helper methods for catalog generation
     - `sync` and `get_records` method for performing sync
    """

    url_endpoint = ""
    path = ""
    page_size = 100
    max_pages = 100000
    page_param = "page"
    page_size_param = "per_page"
    bookmark_query_param = None
    headers = {}
    children = []
    parent = ""
    data_key = ""
    parent_bookmark_key = ""
    http_method = "GET"
    access_check_params = {"per_page": 1, "page": 1}

    def __init__(self, client=None, catalog=None) -> None:
        self.client = client
        self.catalog = catalog
        self.schema = catalog.schema.to_dict()
        self.metadata = metadata.to_map(catalog.metadata)
        self.child_to_sync = []
        self.params = {}
        self.data_payload = {}

    @property
    @abstractmethod
    def tap_stream_id(self) -> str:
        """Unique identifier for the stream.

        This is allowed to be different from the name of the stream, in
        order to allow for sources that have duplicate stream names.
        """

    @property
    @abstractmethod
    def replication_method(self) -> str:
        """Defines the sync mode of a stream."""

    @property
    @abstractmethod
    def replication_keys(self) -> List:
        """Defines the replication key for incremental sync mode of a
        stream."""

    @property
    @abstractmethod
    def key_properties(self) -> Tuple[str, str]:
        """List of key properties for stream."""

    def is_selected(self):
        return metadata.get(self.metadata, (), "selected")

    def check_access(self) -> bool:
        """
        Verify that the credentials can read this stream.

        Sends a single one-record GET to the stream's own endpoint. Returns True when
        the request succeeds and False only when the API answers HTTP 403, meaning the
        credentials lack permission. Every other error is re-raised so that a transient
        or unexpected failure never silently drops a stream from the catalog.
        """
        try:
            self.client.make_request(
                self.http_method,
                self.get_url_endpoint(),
                dict(self.access_check_params),
                self.headers,
            )
            return True
        except UKGProForbiddenError as exc:
            LOGGER.warning(
                "Unauthorized Stream: %s, excluding from catalog. HTTP-Error-Message:'%s'",
                self.tap_stream_id,
                str(exc),
            )
            return False

    @abstractmethod
    def sync(
        self,
        state: Dict,
        transformer: Transformer,
        parent_obj: Dict = None,
    ) -> int:
        """
        Performs a replication sync for the stream.
        ~~~
        Args:
         - state (dict): represents the state file for the tap.
         - transformer (object): A Object of the singer.transformer class.
         - parent_obj (dict): The parent object for the stream.

        Returns:
         - int: The number of records written for the stream.

        Docs:
         - https://github.com/singer-io/getting-started/blob/master/docs/SYNC_MODE.md
        """

    def extract_records(self, response: Any) -> List[Dict]:
        """
        Return the list of records contained in an API response.

        Accepts a bare list of records, or a mapping holding the list under `data_key`.
        An empty response yields no records. Any other shape raises, so an unexpected
        payload is never silently dropped.
        """
        if not response:
            return []
        if isinstance(response, list):
            return response
        if isinstance(response, dict) and self.data_key and self.data_key in response:
            return response[self.data_key] or []
        raise UKGProError(
            "Unexpected response format for stream '{}': expected a list of records.".format(
                self.tap_stream_id
            )
        )

    def get_records(self) -> Iterator:
        """
        Yield every record of the stream, requesting one page at a time.
        """
        page = 1
        previous_page = None
        has_more_pages = True
        while has_more_pages and page <= self.max_pages:
            self.update_params(**{self.page_size_param: self.page_size, self.page_param: page})
            response = self.client.make_request(
                self.http_method,
                self.url_endpoint,
                dict(self.params),
                self.headers,
                body=json.dumps(self.data_payload) if self.data_payload else None,
                path=self.path
            )
            records = self.extract_records(response)
            if not records:
                has_more_pages = False
            elif records == previous_page:
                LOGGER.warning(
                    "Stream %s returned the same page twice; stopping pagination at page %s.",
                    self.tap_stream_id,
                    page,
                )
                has_more_pages = False
            else:
                yield from records
                previous_page = records
                page += 1

        if has_more_pages:
            raise UKGProError(
                "Stream '{}' still returned data after {} pages; stopping to avoid an endless loop.".format(
                    self.tap_stream_id, self.max_pages
                )
            )

    def transform_record(self, transformer: Transformer, record: Dict) -> Dict:
        """
        Transform a record as per the schema and field selection metadata.
        """
        try:
            return transformer.transform(record, self.schema, self.metadata)
        except Exception as err:
            identifiers = (
                {key: record.get(key) for key in self.key_properties}
                if isinstance(record, dict) else {}
            )
            LOGGER.error(
                "Failed to transform record of stream %s (key properties: %s): %s",
                self.tap_stream_id,
                identifiers,
                err,
            )
            raise

    def write_schema(self) -> None:
        """
        Write a schema message.
        """
        try:
            write_schema(self.tap_stream_id, self.schema, self.key_properties)
        except OSError as err:
            LOGGER.error(
                "OS Error while writing schema for: {}".format(self.tap_stream_id)
            )
            raise err

    def update_params(self, **kwargs) -> None:
        """
        Update params for the stream
        """
        self.params.update(kwargs)

    def update_data_payload(self, **kwargs) -> None:
        """
        Update JSON body for the stream
        """
        self.data_payload.update(kwargs)

    def modify_object(self, record: Dict, parent_record: Dict = None) -> Dict:
        """
        Modify the record before writing to the stream
        """
        return record

    def get_url_endpoint(self, parent_obj: Dict = None) -> str:
        """
        Get the URL endpoint for the stream
        """
        return self.url_endpoint or self.client.build_url(self.path)


class IncrementalStream(BaseStream):
    """Base Class for Incremental Stream."""


    def get_bookmark(self, state: dict, stream: str, key: Any = None) -> int:
        """A wrapper for singer.get_bookmark to deal with compatibility for
        bookmark values or start values."""
        validate_bookmark_state(state, stream)
        return get_bookmark(
            state,
            stream,
            key or self.replication_keys[0],
            self.client.config["start_date"],
        )

    def write_bookmark(self, state: dict, stream: str, key: Any = None, value: Any = None) -> Dict:
        """A wrapper for singer.get_bookmark to deal with compatibility for
        bookmark values or start values."""
        if not (key or self.replication_keys):
            return state

        validate_bookmark_state(state, stream)
        current_bookmark = get_bookmark(
            state, stream, key or self.replication_keys[0], self.client.config["start_date"]
        )
        # Compare as datetimes: the start date and the stored bookmark may use different
        # string formats, which makes a plain string comparison unreliable.
        current_dttm = parse_datetime(current_bookmark)
        value_dttm = parse_datetime(value)
        if current_dttm and value_dttm:
            value = value if value_dttm > current_dttm else current_bookmark
        else:
            value = max(current_bookmark, value)
        return write_bookmark(
            state, stream, key or self.replication_keys[0], value
        )

    def get_record_bookmark(self, record: Dict) -> Optional[datetime]:
        """
        Return the replication key value of a transformed record as a UTC datetime.
        """
        value = record.get(self.replication_keys[0])
        if not value:
            return None
        record_dttm = parse_datetime(value)
        if record_dttm is None:
            LOGGER.warning(
                "Stream %s: replication key '%s' holds a value that is not a valid datetime.",
                self.tap_stream_id,
                self.replication_keys[0],
            )
        return record_dttm

    def sync(
        self,
        state: Dict,
        transformer: Transformer,
        parent_obj: Dict = None,
    ) -> int:
        """
        Implementation for `type: Incremental` stream.

        Records older than the bookmark are the only records skipped (replication key
        filtering); their number is logged. A record without a usable replication
        key value cannot be compared, so it is written but does not move the bookmark.
        The bookmark is only advanced once every page has been read, because the API does
        not guarantee ordering by the replication key; an interrupted sync therefore
        restarts from the previously saved bookmark.
        """
        bookmark_date = self.get_bookmark(state, self.tap_stream_id)
        bookmark_dttm = parse_datetime(bookmark_date)
        if bookmark_dttm is None:
            raise UKGProError(
                "Stream '{}': bookmark or start_date '{}' is not a valid datetime.".format(
                    self.tap_stream_id, bookmark_date
                )
            )
        max_bookmark_dttm = bookmark_dttm

        if self.bookmark_query_param:
            self.update_params(**{self.bookmark_query_param: bookmark_date})
        if parent_obj is not None:
            self.update_data_payload(parent_obj=parent_obj)
        self.url_endpoint = self.get_url_endpoint(parent_obj)

        skipped_records = 0
        with metrics.record_counter(self.tap_stream_id) as counter:
            for record in self.get_records():
                record = self.modify_object(record, parent_obj)
                transformed_record = self.transform_record(transformer, record)

                record_dttm = self.get_record_bookmark(transformed_record)
                if record_dttm is not None and record_dttm < bookmark_dttm:
                    # Replication key filtering: the record is older than the bookmark, so
                    # it was already replicated by an earlier sync.
                    skipped_records += 1
                else:
                    if record_dttm is not None:
                        max_bookmark_dttm = max(max_bookmark_dttm, record_dttm)

                    if self.is_selected():
                        write_record(self.tap_stream_id, transformed_record)
                        counter.increment()

                    for child in self.child_to_sync:
                        child.sync(state=state, transformer=transformer, parent_obj=record)

            if skipped_records:
                LOGGER.info(
                    "Stream %s: skipped %s record(s) older than the bookmark %s.",
                    self.tap_stream_id,
                    skipped_records,
                    bookmark_date,
                )

            if max_bookmark_dttm > bookmark_dttm:
                state = self.write_bookmark(
                    state, self.tap_stream_id, value=strftime(max_bookmark_dttm)
                )
            return counter.value


class FullTableStream(BaseStream):
    """Base Class for Incremental Stream."""

    replication_keys = []

    def sync(
        self,
        state: Dict,
        transformer: Transformer,
        parent_obj: Dict = None,
    ) -> int:
        """Abstract implementation for `type: Fulltable` stream."""
        if parent_obj is not None:
            self.update_data_payload(parent_obj=parent_obj)
        self.url_endpoint = self.get_url_endpoint(parent_obj)
        with metrics.record_counter(self.tap_stream_id) as counter:
            for record in self.get_records():
                record = self.modify_object(record, parent_obj)
                transformed_record = self.transform_record(transformer, record)
                if self.is_selected():
                    write_record(self.tap_stream_id, transformed_record)
                    counter.increment()

                for child in self.child_to_sync:
                    child.sync(state=state, transformer=transformer, parent_obj=record)

            return counter.value


class ParentBaseStream(IncrementalStream):
    """Base Class for Parent Stream."""

    def get_bookmark(self, state: Dict, stream: str, key: Any = None) -> int:
        """A wrapper for singer.get_bookmark to deal with compatibility for
        bookmark values or start values."""

        min_parent_bookmark = (
            super().get_bookmark(state, stream) if self.is_selected() else None
        )
        for child in self.child_to_sync:
            bookmark_key = f"{self.tap_stream_id}_{self.replication_keys[0]}"
            child_bookmark = super().get_bookmark(
                state, child.tap_stream_id, key=bookmark_key
            )
            min_parent_bookmark = (
                min(min_parent_bookmark, child_bookmark)
                if min_parent_bookmark
                else child_bookmark
            )

        return min_parent_bookmark

    def write_bookmark(
        self, state: Dict, stream: str, key: Any = None, value: Any = None
    ) -> Dict:
        """A wrapper for singer.get_bookmark to deal with compatibility for
        bookmark values or start values."""
        if self.is_selected():
            super().write_bookmark(state, stream, value=value)

        for child in self.child_to_sync:
            bookmark_key = f"{self.tap_stream_id}_{self.replication_keys[0]}"
            super().write_bookmark(
                state, child.tap_stream_id, key=bookmark_key, value=value
            )

        return state


class ChildBaseStream(IncrementalStream):
    """Base Class for Child Stream."""

    def __init__(self, client=None, catalog=None, config=None) -> None:
        """Initialize ChildBaseStream."""
        super().__init__(client, catalog, config)
        self.bookmark_value = None

    def get_url_endpoint(self, parent_obj=None):
        """Prepare URL endpoint for child streams."""
        return self.client.build_url(self.path.format(parent_obj['id']))

    def get_bookmark(self, state: Dict, stream: str, key: Any = None) -> int:
        """Singleton bookmark value for child streams."""
        if not self.bookmark_value:
            self.bookmark_value = super().get_bookmark(state, stream)

        return self.bookmark_value
