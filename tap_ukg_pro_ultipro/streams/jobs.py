from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class Jobs(FullTableStream):
    tap_stream_id = "jobs"
    key_properties = ["jobCode"]
    replication_method = "FULL_TABLE"
    path = "/configuration/v2/jobs"
