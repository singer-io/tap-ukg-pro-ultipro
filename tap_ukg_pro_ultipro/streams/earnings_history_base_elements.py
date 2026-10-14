from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class EarningsHistoryBaseElements(FullTableStream):
    tap_stream_id = "earnings_history_base_elements"
    key_properties = ["companyId", "employeeId"]
    replication_method = "FULL_TABLE"
    path = "/payroll/v1/earnings-history-base-elements"
