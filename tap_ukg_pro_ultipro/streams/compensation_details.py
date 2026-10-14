from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class CompensationDetails(FullTableStream):
    tap_stream_id = "compensation_details"
    key_properties = ["companyID", "employeeID"]
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/compensation-details"
