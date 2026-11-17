from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class TaxGroups(FullTableStream):
    tap_stream_id = "tax_groups"
    key_properties = ["taxCalcGroupIdCode"]
    replication_method = "FULL_TABLE"
    path = "/configuration/v1/tax-groups"
