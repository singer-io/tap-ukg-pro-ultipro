from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class EmployeeUserDefinedFields(FullTableStream):
    tap_stream_id = "employee_user_defined_fields"
    key_properties = ["employeeId"]
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/user-defined-fields"
    # Observed sync volume is ~1,490 records.
    page_size = 1000
