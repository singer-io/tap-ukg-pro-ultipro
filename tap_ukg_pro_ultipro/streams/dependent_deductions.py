from tap_ukg_pro_ultipro.streams.abstracts import IncrementalStream


class DependentDeductions(IncrementalStream):
    tap_stream_id = "dependent_deductions"
    key_properties = ["systemID"]
    replication_method = "INCREMENTAL"
    replication_keys = ["dateTimeChanged"]
    path = "/personnel/v1/dep-deductions"
