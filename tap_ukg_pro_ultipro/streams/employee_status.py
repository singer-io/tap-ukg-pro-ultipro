from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class EmployeeStatus(FullTableStream):
    tap_stream_id = "employee_status"
    key_properties = []
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/integration/kronos/employee-status"
