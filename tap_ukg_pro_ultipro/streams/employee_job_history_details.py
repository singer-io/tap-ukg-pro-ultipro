from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class EmployeeJobHistoryDetails(FullTableStream):
    tap_stream_id = "employee_job_history_details"
    key_properties = ["systemId"]
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/employee-job-history-details"
