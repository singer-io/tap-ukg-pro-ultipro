from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class CompanyDetails(FullTableStream):
    tap_stream_id = "company_details"
    key_properties = ["companyId"]
    replication_method = "FULL_TABLE"
    path = "/configuration/v1/company-details"
