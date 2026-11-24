from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

from singer import Transformer, get_bookmark, get_logger, metrics, write_bookmark, write_record
from singer.utils import strftime

from tap_ukg_pro_ultipro.exceptions import UKGProError
from tap_ukg_pro_ultipro.streams.abstracts import (
    IncrementalStream,
    parse_datetime,
    validate_bookmark_state,
)

LOGGER = get_logger()

# Date format sent to the API (RFC 3339, UTC, whole seconds).
DATE_PARAM_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def utc_now() -> datetime:
    """Current UTC time truncated to whole seconds"""
    return datetime.now(timezone.utc).replace(microsecond=0)


def format_date_param(value: datetime) -> str:
    """Format a datetime as the RFC 3339 UTC string sent in `startDate` / `endDate`."""
    return value.astimezone(timezone.utc).strftime(DATE_PARAM_FORMAT)


class EmployeeChanges(IncrementalStream):
    """
    Employee changes by date.

    Without `startDate` / `endDate` the API answers with "everything since the last API
    call (3 hour minimum)", so any other call, including a discovery probe, can consume
    changes that a later sync then never sees. Every request of this stream therefore
    carries explicit bounds:

     - `endDate` is captured once per extraction and reused by every page.
     - `startDate` is the `start_date` config value for the first extraction, then the previous `emplStatusStartDate` bookmark.

    The bookmark is the greatest `emplStatusStartDate` seen, capped at the extraction's
    `endDate`, and is written only after every page has been read.
    """

    tap_stream_id = "employee_changes"
    key_properties = ["employeeId", "companyId"]
    replication_method = "INCREMENTAL"
    replication_keys = ["emplStatusStartDate"]
    path = "/personnel/v1/employee-changes"
    page_size = 200

    start_date_param = "startDate"
    end_date_param = "endDate"
    # Width of the explicit window used by the discovery access probe.
    access_check_window = timedelta(hours=3)

    @property
    def access_check_params(self) -> Dict:
        """Discovery probe parameters with an explicit window instead of the implicit one."""
        end = utc_now()
        return {
            "per_page": 1,
            "page": 1,
            self.start_date_param: format_date_param(end - self.access_check_window),
            self.end_date_param: format_date_param(end),
        }

    def get_extraction_window(self, state: Dict) -> Tuple[datetime, datetime, Optional[datetime]]:
        """
        Return `(start, end, previous_bookmark)` for one extraction.

        `end` is read from the clock exactly once, here.
        """
        validate_bookmark_state(state, self.tap_stream_id)
        end = utc_now()
        bookmark = get_bookmark(state, self.tap_stream_id, self.replication_keys[0])
        previous_bookmark = None
        if bookmark is None:
            source, value = "start_date", self.client.config.get("start_date")
        else:
            source, value = "bookmark", bookmark

        start = parse_datetime(value)
        if start is None:
            raise UKGProError(
                "Stream '{}': {} '{}' is not a valid datetime.".format(
                    self.tap_stream_id, source, value
                )
            )
        if bookmark is not None:
            previous_bookmark = start
        if start >= end:
            raise UKGProError(
                "Stream '{}': {} '{}' is not before the extraction end date {}.".format(
                    self.tap_stream_id, source, value, format_date_param(end)
                )
            )
        return start, end, previous_bookmark

    def sync(self, state: Dict, transformer: Transformer) -> int:
        """
        Extract the changes of one fixed window.

        Records are not filtered by the bookmark: the API window is the only filter, so a
        record is never dropped on the strength of a field the API may not filter on.
        An error on any page propagates before the bookmark is touched.
        """
        start, end, previous_bookmark = self.get_extraction_window(state)
        self.url_endpoint = self.get_url_endpoint()

        self.update_params(**{
            self.start_date_param: format_date_param(start),
            self.end_date_param: format_date_param(end),
        })
        LOGGER.info(
            "Stream %s: extracting changes from %s to %s",
            self.tap_stream_id, self.params[self.start_date_param], self.params[self.end_date_param],
        )

        max_dttm = None
        total_records = 0
        with metrics.record_counter(self.tap_stream_id) as counter:
            for record in self.get_records():
                record = self.modify_object(record)
                transformed_record = self.transform_record(transformer, record)

                record_dttm = self.get_record_bookmark(transformed_record)
                if record_dttm is not None and (max_dttm is None or record_dttm > max_dttm):
                    max_dttm = record_dttm

                if self.is_selected():
                    write_record(self.tap_stream_id, transformed_record)
                    counter.increment()
                    total_records += 1

        # Reached only when every page was read.
        if max_dttm is not None:
            new_bookmark = min(max_dttm, end)
            if previous_bookmark is None or new_bookmark > previous_bookmark:
                write_bookmark(
                    state, self.tap_stream_id, self.replication_keys[0], strftime(new_bookmark)
                )
        return total_records
