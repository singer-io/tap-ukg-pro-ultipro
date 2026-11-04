import singer
from singer import metadata
from singer.catalog import Catalog, CatalogEntry, Schema
from tap_ukg_pro_ultipro.exceptions import UKGProForbiddenError
from tap_ukg_pro_ultipro.schema import get_schemas
from tap_ukg_pro_ultipro.streams import STREAMS

LOGGER = singer.get_logger()


def _apply_access_checks(stream_instances):
    """
    Probe each stream for read access and return only the accessible ones.

    Streams whose probe returns HTTP 403 are excluded and a single warning lists them.
    Any other error raised by a probe propagates, so an unexpected failure never
    silently removes a stream. Raises UKGProForbiddenError when no stream is
    accessible, since discovery would otherwise emit an empty catalog.

    Args:
        stream_instances: list of stream objects exposing `tap_stream_id` and `check_access()`.

    Returns:
        list of the stream objects that are accessible.
    """
    accessible_streams = []
    inaccessible_streams = []

    for stream in stream_instances:
        if stream.check_access():
            accessible_streams.append(stream)
        else:
            inaccessible_streams.append(stream.tap_stream_id)

    if not accessible_streams:
        raise UKGProForbiddenError(
            "HTTP-error-code: 403, Error: The credentials do not have 'read' access to any supported streams."
        )

    if inaccessible_streams:
        LOGGER.warning(
            "Unauthorized streams have been excluded: %s",
            ", ".join(inaccessible_streams),
        )

    return accessible_streams


def discover(client) -> Catalog:
    """
    Run the discovery mode, prepare the catalog file and return the catalog.

    Streams the credentials cannot read (HTTP 403) are left out of the catalog.
    """
    schemas, field_metadata = get_schemas()
    entries = []

    for stream_name, schema_dict in schemas.items():
        try:
            schema = Schema.from_dict(schema_dict)
            mdata = field_metadata[stream_name]
        except Exception as err:
            LOGGER.error(err)
            LOGGER.error("stream_name: {}".format(stream_name))
            LOGGER.error("type schema_dict: {}".format(type(schema_dict)))
            raise err

        key_properties = metadata.to_map(mdata).get((), {}).get("table-key-properties")

        entries.append(
            CatalogEntry(
                stream=stream_name,
                tap_stream_id=stream_name,
                key_properties=key_properties,
                schema=schema,
                metadata=mdata,
            )
        )

    stream_instances = [STREAMS[entry.tap_stream_id](client, entry) for entry in entries]
    accessible_ids = {s.tap_stream_id for s in _apply_access_checks(stream_instances)}

    return Catalog([entry for entry in entries if entry.tap_stream_id in accessible_ids])
