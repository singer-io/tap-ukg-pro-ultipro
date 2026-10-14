from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class PositionReports(FullTableStream):
    tap_stream_id = "position_reports"
    key_properties = ["positionCode"]
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/position-report"
