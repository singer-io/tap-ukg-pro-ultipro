from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class Contacts(FullTableStream):
    tap_stream_id = "contacts"
    key_properties = ["contactId"]
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/contacts"
