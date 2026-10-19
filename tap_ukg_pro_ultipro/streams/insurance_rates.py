from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class InsuranceRates(FullTableStream):
    tap_stream_id = "insurance_rates"
    key_properties = ["deductionCode"]
    replication_method = "FULL_TABLE"
    path = "/configuration/v1/insurance-rate"
