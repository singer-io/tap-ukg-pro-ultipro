from base import ukg_pro_ultiproBaseTest
from tap_tester.base_suite_tests.all_fields_test import AllFieldsTest


class ukg_pro_ultiproAllFields(AllFieldsTest, ukg_pro_ultiproBaseTest):
    """Ensure running the tap with all streams and fields selected results in
    the replication of all fields."""
    MISSING_FIELDS = {
        'company_details': {'orgLevel1Code', 'orgLevel2Code', 'orgLevel3Code', 'orgLevel4Code'},
        'employee_changes': {'workLocation'},
        'user_details': {'userLastLogonDate'},
    }

    @staticmethod
    def name():
        return "tap_tester_ukg_pro_ultipro_all_fields_test"

    def streams_to_test(self):
        # Exclude large-data-volume streams to avoid excessively slow test runs.
        streams_to_exclude = self.LARGE_DATA_STREAMS.union({
            # No data available for these streams
            "employee_contract_details",
            "employee_global_banks",
            "employee_global_localization_elements",
            "employee_multi_positions",
            "employee_pay_deduction_elements",
            "employee_status",
            "general_ledgers",
            "job_groups",
            "national_documents",
            "position_reports",
            "positions",
        })
        return self.expected_stream_names().difference(streams_to_exclude)
