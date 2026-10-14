from tap_ukg_pro_ultipro.streams.abstracts import IncrementalStream


class OpenEnrollmentEmployeeDeductions(IncrementalStream):
    tap_stream_id = "open_enrollment_employee_deductions"
    key_properties = ["employeeId", "deductionCode"]
    replication_method = "INCREMENTAL"
    replication_keys = ["createDatetime"]
    path = "/personnel/v1/open-enrollment-emp-deductions"
