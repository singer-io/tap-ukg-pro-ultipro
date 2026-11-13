from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class Locations(FullTableStream):
    tap_stream_id = "locations"
    key_properties = ["locationCode"]
    replication_method = "FULL_TABLE"
    pagination_enabled = False
    access_check_params = {}
    path = "/configuration/v1/locations/"
