from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class InternationalEmployees(FullTableStream):
    tap_stream_id = "international_employees"
    key_properties = []
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/international-employees"
