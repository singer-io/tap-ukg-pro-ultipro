from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class ShiftCodes(FullTableStream):
    tap_stream_id = "shift_codes"
    key_properties = ["shiftCode"]
    replication_method = "FULL_TABLE"
    path = "/configuration/v1/shift-codes"
