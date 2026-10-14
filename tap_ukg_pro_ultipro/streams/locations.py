from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class Locations(FullTableStream):
    tap_stream_id = "locations"
    key_properties = ["locationCode"]
    replication_method = "FULL_TABLE"
    path = "/configuration/v1/locations/"
