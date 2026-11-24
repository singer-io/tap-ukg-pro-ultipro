from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class AwardType(FullTableStream):
    tap_stream_id = "award_type"
    key_properties = ["code"]
    replication_method = "FULL_TABLE"
    path = "/configuration/v1/code-tables/awardType/"
