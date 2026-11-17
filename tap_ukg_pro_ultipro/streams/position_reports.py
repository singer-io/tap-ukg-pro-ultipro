from tap_ukg_pro_ultipro.streams.abstracts import IncrementalStream


class PositionReports(IncrementalStream):
    tap_stream_id = "position_reports"
    key_properties = ["positionCode"]
    replication_method = "INCREMENTAL"
    replication_keys = ["dateTimeChanged"]
    path = "/personnel/v1/position-report"
