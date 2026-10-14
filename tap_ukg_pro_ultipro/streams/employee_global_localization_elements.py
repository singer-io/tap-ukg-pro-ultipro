from tap_ukg_pro_ultipro.streams.abstracts import IncrementalStream


class EmployeeGlobalLocalizationElements(IncrementalStream):
    tap_stream_id = "employee_global_localization_elements"
    key_properties = ["employeeId", "fieldId"]
    replication_method = "INCREMENTAL"
    replication_keys = ["created"]
    path = "/personnel/v1/employee-global-localization-elements"
