from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class Roles(FullTableStream):
    tap_stream_id = "roles"
    key_properties = ["rolID"]
    replication_method = "FULL_TABLE"
    path = "/configuration/v1/roles"
