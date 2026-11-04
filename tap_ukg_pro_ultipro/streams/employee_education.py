from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class EmployeeEducation(FullTableStream):
    tap_stream_id = "employee_education"
    key_properties = ["employeeId"]
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/employee-education"
    # Observed sync volume is ~505 records.
    page_size = 500
