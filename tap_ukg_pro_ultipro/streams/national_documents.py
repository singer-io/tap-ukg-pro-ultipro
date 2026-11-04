from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class NationalDocuments(FullTableStream):
    tap_stream_id = "national_documents"
    key_properties = ["employeeId", "nationalDocumentId"]
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/national-documents"
