from tap_ukg_pro_ultipro.streams.abstracts import IncrementalStream


class EmployeeContractDetails(IncrementalStream):
    tap_stream_id = "employee_contract_details"
    key_properties = ["employeeId", "contractNumber"]
    replication_method = "INCREMENTAL"
    replication_keys = ["dateTimeCreated"]
    path = "/personnel/v1/employee-contract-details"
