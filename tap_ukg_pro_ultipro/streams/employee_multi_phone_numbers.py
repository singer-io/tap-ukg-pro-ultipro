from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class EmployeeMultiPhoneNumbers(FullTableStream):
    tap_stream_id = "employee_multi_phone_numbers"
    key_properties = ["employeeId", "auditKey"]
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/employee-multi-phone-numbers"
