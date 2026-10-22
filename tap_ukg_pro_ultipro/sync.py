import singer
from typing import Dict
from tap_ukg_pro_ultipro.exceptions import UKGProError, UKGProForbiddenError
from tap_ukg_pro_ultipro.streams import STREAMS
from tap_ukg_pro_ultipro.client import Client

LOGGER = singer.get_logger()


def update_currently_syncing(state: Dict, stream_name: str) -> None:
    """
    Update currently_syncing in state and write it.
    """
    if not stream_name:
        state.pop("currently_syncing", None)
    else:
        singer.set_currently_syncing(state, stream_name)
    singer.write_state(state)


def get_stream_object(stream_name: str, client: Client, catalog: singer.Catalog):
    """
    Build the stream object for a stream of the catalog.
    """
    stream_class = STREAMS.get(stream_name)
    if stream_class is None:
        raise UKGProError("Stream '{}' is not supported by this tap.".format(stream_name))

    catalog_entry = catalog.get_stream(stream_name)
    if catalog_entry is None:
        raise UKGProError("Stream '{}' was not found in the catalog.".format(stream_name))

    return stream_class(client, catalog_entry)


def write_schema(stream, client, streams_to_sync, catalog) -> None:
    """
    Write schema for stream and its children
    """
    if stream.is_selected():
        stream.write_schema()

    for child in stream.children:
        child_obj = STREAMS[child](client, catalog.get_stream(child))
        write_schema(child_obj, client, streams_to_sync, catalog)
        if child in streams_to_sync:
            stream.child_to_sync.append(child_obj)


def sync(client: Client, config: Dict, catalog: singer.Catalog, state) -> None:
    """
    Sync selected streams from catalog
    """

    streams_to_sync = []
    for stream in catalog.get_selected_streams(state):
        streams_to_sync.append(stream.tap_stream_id)
    LOGGER.info("selected_streams: {}".format(streams_to_sync))

    last_stream = singer.get_currently_syncing(state)
    LOGGER.info("last/currently syncing stream: {}".format(last_stream))

    with singer.Transformer() as transformer:
        for stream_name in streams_to_sync:
            stream = get_stream_object(stream_name, client, catalog)
            if stream.parent:
                if stream.parent not in streams_to_sync:
                    streams_to_sync.append(stream.parent)
                continue

            write_schema(stream, client, streams_to_sync, catalog)
            LOGGER.info("START Syncing: {}".format(stream_name))
            update_currently_syncing(state, stream_name)
            try:
                total_records = stream.sync(state=state, transformer=transformer)
            except (UKGProForbiddenError, UKGProError) as error:
                LOGGER.warning(
                    "Skipping stream %s: %s",
                    stream_name,
                    str(error)
                )
                update_currently_syncing(state, None)
                continue

            update_currently_syncing(state, None)
            LOGGER.info(
                "FINISHED Syncing: {}, total_records: {}".format(
                    stream_name, total_records
                )
            )
