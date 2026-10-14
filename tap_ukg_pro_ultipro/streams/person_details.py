from tap_ukg_pro_ultipro.streams.abstracts import IncrementalStream


class PersonDetails(IncrementalStream):
    tap_stream_id = "person_details"
    key_properties = ["employeeId"]
    replication_method = "INCREMENTAL"
    replication_keys = ["datetimeCreated"]
    path = "/personnel/v1/person-details"
