from tap_ukg_pro_ultipro.streams.abstracts import IncrementalStream


class Positions(IncrementalStream):
    tap_stream_id = "positions"
    key_properties = ["integrationRecordId"]
    replication_method = "INCREMENTAL"
    replication_keys = ["dateTimeChanged"]
    path = "/configuration/v1/positions"
