from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class EmployeeChanges(FullTableStream):
    tap_stream_id = "employee_changes"
    key_properties = []
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/employee-changes"
