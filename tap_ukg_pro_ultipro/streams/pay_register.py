from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class PayRegister(FullTableStream):
    tap_stream_id = "pay_register"
    key_properties = []
    replication_method = "FULL_TABLE"
    path = "/payroll/v1/pay-register"
