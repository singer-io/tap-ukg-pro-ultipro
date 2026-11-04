from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class PayRegister(FullTableStream):
    tap_stream_id = "pay_register"
    key_properties = []
    replication_method = "FULL_TABLE"
    path = "/payroll/v1/pay-register"
    # The UKG Pro API accepts per_Page values up to 2147483647 for this endpoint.
    # The default page_size of 100 (BaseStream) results in many sequential round
    # trips for large datasets; raising it reduces the number of requests needed
    # to fully sync this stream.
    page_size = 1000
