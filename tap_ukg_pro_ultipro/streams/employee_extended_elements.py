from tap_ukg_pro_ultipro.streams.abstracts import IncrementalStream


class EmployeeExtendedElements(IncrementalStream):
    tap_stream_id = "employee_extended_elements"
    key_properties = ["personID"]
    replication_method = "INCREMENTAL"
    replication_keys = ["dateTimeCreated"]
    path = "/personnel/v1/employee-extended-elements"
