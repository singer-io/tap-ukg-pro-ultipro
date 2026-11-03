from tap_tester.base_suite_tests.pagination_test import PaginationTest
from base import ukg_pro_ultiproBaseTest

class ukg_pro_ultiproPaginationTest(PaginationTest, ukg_pro_ultiproBaseTest):
    """
    Ensure tap can replicate multiple pages of data for streams that use pagination.
    """

    @staticmethod
    def name():
        return "tap_tester_ukg_pro_ultipro_pagination_test"

    def streams_to_test(self):
        # Exclude large-data-volume streams to avoid excessively slow test runs.
        streams_to_exclude = self.LARGE_DATA_STREAMS
        return self.expected_stream_names().difference(streams_to_exclude)

