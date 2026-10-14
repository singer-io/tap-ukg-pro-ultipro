from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class EmployeeMultipleJobs(FullTableStream):
    tap_stream_id = "employee_multiple_jobs"
    key_properties = ["employeeId", "jobCode"]
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/empl-multiple-jobs"
