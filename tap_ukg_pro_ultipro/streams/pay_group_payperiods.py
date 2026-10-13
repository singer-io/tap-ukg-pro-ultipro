from tap_ukg_pro_ultipro.streams.abstracts import IncrementalStream


class PayGroupPayperiods(IncrementalStream):
    tap_stream_id = "pay_group_payperiods"
    key_properties = []
    replication_method = "INCREMENTAL"
    replication_keys = ["dateTimeCreated"]
    path = "/payroll/v1/paygroup-payperiods"
