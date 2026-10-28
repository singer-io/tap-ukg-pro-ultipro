from base import ukg_pro_ultiproBaseTest
from tap_tester.base_suite_tests.all_fields_test import AllFieldsTest

KNOWN_MISSING_FIELDS = {

}


class ukg_pro_ultiproAllFields(AllFieldsTest, ukg_pro_ultiproBaseTest):
    """Ensure running the tap with all streams and fields selected results in
    the replication of all fields."""

    @staticmethod
    def name():
        return "tap_tester_ukg_pro_ultipro_all_fields_test"

    def streams_to_test(self):
        # Exclude large-data-volume streams to avoid excessively slow test runs.
        streams_to_exclude = self.LARGE_DATA_STREAMS
        return self.expected_stream_names().difference(streams_to_exclude)
