from tap_ukg_pro_ultipro.streams.abstracts import IncrementalStream


class EmploymentDetails(IncrementalStream):
    tap_stream_id = "employment_details"
    key_properties = ["companyID", "employeeID"]
    replication_method = "INCREMENTAL"
    replication_keys = ["dateTimeCreated"]
    path = "/personnel/v1/employment-details"
