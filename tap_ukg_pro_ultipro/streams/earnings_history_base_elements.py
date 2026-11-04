from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class EarningsHistoryBaseElements(FullTableStream):
    tap_stream_id = "earnings_history_base_elements"
    key_properties = ["companyId", "employeeId"]
    replication_method = "FULL_TABLE"
    path = "/payroll/v1/earnings-history-base-elements"
    # The UKG Pro API accepts per_Page values up to 2147483647 for this endpoint.
    # The default page_size of 100 (BaseStream) results in many sequential round
    # trips for large datasets; raising it reduces the number of requests needed
    # to fully sync this stream.
    page_size = 10000
