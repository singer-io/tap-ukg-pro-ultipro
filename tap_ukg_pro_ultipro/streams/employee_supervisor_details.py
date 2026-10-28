from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class EmployeeSupervisorDetails(FullTableStream):
    tap_stream_id = "employee_supervisor_details"
    key_properties = ["employeeID"]
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/employee-supervisor-details"
    # Observed sync volume is ~1,490 records.
    page_size = 1000
