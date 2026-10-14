from tap_ukg_pro_ultipro.streams.abstracts import FullTableStream


class PtoPlans(FullTableStream):
    tap_stream_id = "pto_plans"
    key_properties = ["employeeId", "companyId", "ptoPlan"]
    replication_method = "FULL_TABLE"
    path = "/personnel/v1/pto-plans"
