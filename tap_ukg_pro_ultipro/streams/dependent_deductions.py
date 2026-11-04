from tap_ukg_pro_ultipro.streams.abstracts import IncrementalStream


class DependentDeductions(IncrementalStream):
    tap_stream_id = "dependent_deductions"
    key_properties = []
    replication_method = "INCREMENTAL"
    replication_keys = ["dateTimeCreated"]
    path = "/personnel/v1/dep-deductions"
