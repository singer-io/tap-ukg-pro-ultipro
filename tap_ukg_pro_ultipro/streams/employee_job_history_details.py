from tap_ukg_pro_ultipro.streams.abstracts import IncrementalStream


class EmployeeJobHistoryDetails(IncrementalStream):
    tap_stream_id = "employee_job_history_details"
    key_properties = ["employeeId", "jobEffectiveDate"]
    replication_method = "INCREMENTAL"
    replication_keys = ["dateTimeCreated"]
    path = "/personnel/v1/employee-job-history-details"
