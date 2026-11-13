from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class EmployeeMultiPositions(FullTableStream):
    tap_stream_id = "employee_multi_positions"
    key_properties = []
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/empl-multiple-positions"
