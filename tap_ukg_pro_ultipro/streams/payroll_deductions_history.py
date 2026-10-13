from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class PayrollDeductionsHistory(FullTableStream):
    tap_stream_id = "payroll_deductions_history"
    key_properties = ["recordId"]
    replication_method = "FULL_TABLE"
    path = "/payroll/v1/payroll-deductions-history"
