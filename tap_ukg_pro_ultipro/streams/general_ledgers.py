from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class GeneralLedgers(FullTableStream):
    tap_stream_id = "general_ledgers"
    key_properties = []
    replication_method = "FULL_TABLE"
    path = "/payroll/v2/general-ledger"
