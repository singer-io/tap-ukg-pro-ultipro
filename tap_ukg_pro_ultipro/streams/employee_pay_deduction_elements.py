from tap_ukg_pro_ultipro.streams.abstracts import IncrementalStream


class EmployeePayDeductionElements(IncrementalStream):
    tap_stream_id = "employee_pay_deduction_elements"
    key_properties = ["employeeId", "payDeductionId"]
    replication_method = "INCREMENTAL"
    replication_keys = ["modifiedDate"]
    path = "/personnel/v1/employee-pay-deduction-elements"
