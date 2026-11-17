from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class EmployeeChanges(FullTableStream):
    tap_stream_id = "employee_changes"
    key_properties = []
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/employee-changes"
    # The API limits Per_Page to a maximum of 200.
    page_size = 200
