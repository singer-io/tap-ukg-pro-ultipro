"""Test that with no fields selected for a stream automatic fields are still
replicated."""
from base import ukg_pro_ultiproBaseTest
from tap_tester.base_suite_tests.automatic_fields_test import MinimumSelectionTest


class ukg_pro_ultiproAutomaticFields(MinimumSelectionTest, ukg_pro_ultiproBaseTest):
    """Test that with no fields selected for a stream automatic fields are
    still replicated."""

    @staticmethod
    def name():
        return "tap_tester_ukg_pro_ultipro_automatic_fields_test"

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
            # No unique records available for this stream
            "employee_education",
        })
        return self.expected_stream_names().difference(streams_to_exclude)
