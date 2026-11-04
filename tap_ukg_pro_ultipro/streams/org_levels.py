from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class OrgLevels(FullTableStream):
    tap_stream_id = "org_levels"
    key_properties = ["code", "level"]
    replication_method = "FULL_TABLE"
    path = "/configuration/v1/org-levels"
