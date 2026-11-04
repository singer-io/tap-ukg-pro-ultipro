from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class CareerProvider(FullTableStream):
    tap_stream_id = "career_provider"
    key_properties = ["code"]
    replication_method = "FULL_TABLE"
    path = "/configuration/v1/code-tables/careerProvider/"
