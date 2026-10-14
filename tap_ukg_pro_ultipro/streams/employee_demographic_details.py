from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class EmployeeDemographicDetails(FullTableStream):
    tap_stream_id = "employee_demographic_details"
    key_properties = ["employeeId"]
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/employee-demographic-details"
