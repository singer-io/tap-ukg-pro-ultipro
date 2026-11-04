from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class OptionRates(FullTableStream):
    tap_stream_id = "option_rates"
    key_properties = []
    replication_method = "FULL_TABLE"
    path = "/configuration/v1/option-rate"
