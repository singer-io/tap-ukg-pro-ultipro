from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class EmployeeGlobalLocalizationElements(FullTableStream):
    tap_stream_id = "employee_global_localization_elements"
    key_properties = ["employeeId", "fieldId"]
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/employee-global-localization-elements"
