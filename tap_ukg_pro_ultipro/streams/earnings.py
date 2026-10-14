from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class Earnings(FullTableStream):
    tap_stream_id = "earnings"
    key_properties = ["earningCode"]
    replication_method = "FULL_TABLE"
    path = "/configuration/v1/earnings"
