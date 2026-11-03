from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class DirectDeposits(FullTableStream):
    tap_stream_id = "direct_deposits"
    key_properties = ["accountRecordId"]
    replication_method = "FULL_TABLE"
    path = "/payroll/v1/direct-deposit"
    # Observed sync volume is ~1,776 records.
    page_size = 1000
