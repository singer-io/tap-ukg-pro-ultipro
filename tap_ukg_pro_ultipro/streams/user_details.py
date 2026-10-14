from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class UserDetails(FullTableStream):
    tap_stream_id = "user_details"
    key_properties = ["userId"]
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/user-details"
