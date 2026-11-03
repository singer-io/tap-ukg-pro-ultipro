from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class EmployeeCobraDetails(FullTableStream):
    tap_stream_id = "employee_cobra_details"
    key_properties = ["personID"]
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/employee-cobra-details"
    # Observed sync volume is ~1,490 records.
    page_size = 1000
