from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class PayrollDeductionsHistory(FullTableStream):
    tap_stream_id = "payroll_deductions_history"
    key_properties = ["recordId"]
    replication_method = "FULL_TABLE"
    path = "/payroll/v1/payroll-deductions-history"
    # The UKG Pro API accepts per_Page values up to 2147483647 for this endpoint.
    # Observed sync volume is ~1.56M records; raising page_size further reduces
    # the number of requests needed to fully sync this stream.
    page_size = 20000
