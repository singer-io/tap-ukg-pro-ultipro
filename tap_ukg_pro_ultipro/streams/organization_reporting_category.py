from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class OrganizationReportingCategory(FullTableStream):
    tap_stream_id = "organization_reporting_category"
    key_properties = ["code"]
    replication_method = "FULL_TABLE"
    path = "/configuration/v1/organization-reporting-category"
