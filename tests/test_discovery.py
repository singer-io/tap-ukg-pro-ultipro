"""Test tap discovery mode and metadata."""
from base import ukg_pro_ultiproBaseTest
from tap_tester.base_suite_tests.discovery_test import DiscoveryTest
from tap_tester import menagerie


class ukg_pro_ultiproDiscoveryTest(DiscoveryTest, ukg_pro_ultiproBaseTest):
    """Test tap discovery mode and metadata conforms to standards."""

    @property
    def orphan_streams(self):
        """
        No stream in this tap currently defines a `parent` (see
        tap_ukg_pro_ultipro/streams/abstracts.py BaseStream.parent default of
        ""), i.e. every stream is top-level with no parent/child
        relationship. All streams are therefore legitimately "orphans" and
        are not expected to carry PARENT_TAP_STREAM_ID metadata.

        This is computed dynamically (rather than a hardcoded, easy-to-drift
        literal list) so it always reflects the current full set of expected
        stream names.
        """
        return self.expected_stream_names()

    @staticmethod
    def name():
        return "tap_tester_ukg_pro_ultipro_discovery_test"

    def streams_to_test(self):
        return self.expected_stream_names()

    def test_parent_stream(self):
        """
        Test that each stream's metadata correctly includes the expected parent tap stream ID.

        For each stream in `streams_to_test`, this test:
        - Retrieves the expected parent tap stream ID from test expectations.
        - Retrieves the actual metadata from the found catalog.
        - Verifies that the metadata contains the `PARENT_TAP_STREAM_ID` key (except for the orphans stream).
        - Confirms that the actual parent tap stream ID matches the expected value.
        """
        for stream in self.streams_to_test():
            with self.subTest(stream=stream):

                expected_parent_tap_stream_id = self.expected_parent_tap_stream(stream)


                catalog = [catalog for catalog in self.found_catalogs
                           if catalog["stream_name"] == stream][0]
                metadata = menagerie.get_annotated_schema(
                    self.conn_id, catalog['stream_id'])["metadata"]
                stream_properties = [item for item in metadata if item.get("breadcrumb") == []]
                actual_parent_tap_stream_id = \
                    stream_properties[0].get("metadata", {}).get(self.PARENT_TAP_STREAM_ID, None)


                self.assertIn("metadata", stream_properties[0])
                stream_metadata = stream_properties[0]["metadata"]


                if stream not in self.orphan_streams:
                    self.assertIn(self.PARENT_TAP_STREAM_ID, stream_metadata)
                    self.assertTrue(isinstance(actual_parent_tap_stream_id, str))


                with self.subTest(msg="validating parent tap stream id"):
                    self.assertEqual(expected_parent_tap_stream_id, actual_parent_tap_stream_id,
                                        logging=f"verify {expected_parent_tap_stream_id} "
                                                f"is saved in metadata as a parent-tap-stream-id")

