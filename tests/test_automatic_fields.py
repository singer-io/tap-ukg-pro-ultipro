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
        streams_to_exclude = {}
        return self.expected_stream_names().difference(streams_to_exclude)

