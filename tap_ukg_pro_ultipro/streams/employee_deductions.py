from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class EmployeeDeductions(FullTableStream):
    tap_stream_id = "employee_deductions"
    key_properties = ["employeeId", "dedCode"]
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/emp-deductions"
