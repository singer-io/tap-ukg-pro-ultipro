from tap_ukg_pro_ultipro.streams.abstracts import IncrementalStream


class EmployeeMultiPositions(IncrementalStream):
    tap_stream_id = "employee_multi_positions"
    key_properties = []
    replication_method = "INCREMENTAL"
    replication_keys = ["dateTimeCreated"]
    path = "/personnel/v1/empl-multiple-positions"
