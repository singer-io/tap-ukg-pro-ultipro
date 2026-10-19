from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class EmployeeSecurityUserDetails(FullTableStream):
    tap_stream_id = "employee_security_user_details"
    key_properties = ["userID"]
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/employee-security-user-details"
