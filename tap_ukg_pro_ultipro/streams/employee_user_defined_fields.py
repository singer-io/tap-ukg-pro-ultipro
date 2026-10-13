from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class EmployeeUserDefinedFields(FullTableStream):
    tap_stream_id = "employee_user_defined_fields"
    key_properties = ["employeeId"]
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/user-defined-fields"
