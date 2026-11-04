from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class JobGroups(FullTableStream):
    tap_stream_id = "job_groups"
    key_properties = ["jobGroupCode"]
    replication_method = "FULL_TABLE"
    path = "/configuration/v1/jobgroup"
