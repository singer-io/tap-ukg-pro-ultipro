import unittest
from unittest.mock import patch, MagicMock
from tap_ukg_pro_ultipro.sync import write_schema, sync, update_currently_syncing
from tap_ukg_pro_ultipro.streams import STREAMS


class TestSync(unittest.TestCase):

    def test_write_schema_only_parent_selected(self):
        mock_stream = MagicMock()
        mock_stream.is_selected.return_value = True
        mock_stream.children = ["roles", "earnings"]
        mock_stream.child_to_sync = []

        client = MagicMock()
        catalog = MagicMock()
        catalog.get_stream.return_value = MagicMock()

        write_schema(mock_stream, client, [], catalog)

        mock_stream.write_schema.assert_called_once()
        self.assertEqual(len(mock_stream.child_to_sync), 0)

    def test_write_schema_parent_child_both_selected(self):
        mock_stream = MagicMock()
        mock_stream.is_selected.return_value = True
        mock_stream.children = ["roles", "earnings"]
        mock_stream.child_to_sync = []

        client = MagicMock()
        catalog = MagicMock()
        catalog.get_stream.return_value = MagicMock()

        write_schema(mock_stream, client, ["roles"], catalog)

        mock_stream.write_schema.assert_called_once()
        self.assertEqual(len(mock_stream.child_to_sync), 1)

    def test_write_schema_child_selected(self):
        mock_stream = MagicMock()
        mock_stream.is_selected.return_value = False
        mock_stream.children = ["roles", "earnings"]
        mock_stream.child_to_sync = []

        client = MagicMock()
        catalog = MagicMock()
        catalog.get_stream.return_value = MagicMock()

        write_schema(mock_stream, client, ["roles", "earnings"], catalog)

        self.assertEqual(mock_stream.write_schema.call_count, 0)
        self.assertEqual(len(mock_stream.child_to_sync), 2)

    @patch("singer.write_schema")
    @patch("singer.get_currently_syncing")
    @patch("singer.Transformer")
    @patch("singer.write_state")
    @patch("tap_ukg_pro_ultipro.streams.abstracts.IncrementalStream.sync")
    def test_sync_stream1_called(self, mock_sync, mock_write_state, mock_transformer, mock_get_currently_syncing, mock_write_schema):
        mock_catalog = MagicMock()
        first_stream = MagicMock()
        first_stream.stream = "positions"
        second_stream = MagicMock()
        second_stream.stream = "person_details"
        mock_catalog.get_selected_streams.return_value = [
            first_stream,
            second_stream
        ]
        state = {}

        client = MagicMock()
        config = {}

        sync(client, config, mock_catalog, state)

        self.assertEqual(mock_sync.call_count, 2)

    @patch("singer.write_schema")
    @patch("singer.get_currently_syncing")
    @patch("singer.Transformer")
    @patch("singer.write_state")
    @patch("tap_ukg_pro_ultipro.streams.abstracts.IncrementalStream.sync")
    def test_sync_child_selected(self, mock_sync, mock_write_state, mock_transformer, mock_get_currently_syncing, mock_write_schema):
        mock_catalog = MagicMock()
        parent_stream = MagicMock()
        parent_stream.stream = "positions"
        child_stream = MagicMock()
        child_stream.stream = "person_details"
        mock_catalog.get_selected_streams.return_value = [
            parent_stream,
            child_stream
        ]
        state = {}

        client = MagicMock()
        config = {}

        # Mark one stream as the child of the other; only the parent is synced directly.
        with patch.object(STREAMS["person_details"], "parent", "positions"):
            sync(client, config, mock_catalog, state)

        self.assertEqual(mock_sync.call_count, 1)

    @patch("singer.get_currently_syncing")
    @patch("singer.set_currently_syncing")
    @patch("singer.write_state")
    def test_remove_currently_syncing(self, mock_write_state, mock_set_currently_syncing, mock_get_currently_syncing):
        mock_get_currently_syncing.return_value = "some_stream"
        state = {"currently_syncing": "some_stream"}

        update_currently_syncing(state, None)

        mock_get_currently_syncing.assert_called_once_with(state)
        mock_set_currently_syncing.assert_not_called()
        mock_write_state.assert_called_once_with(state)
        self.assertNotIn("currently_syncing", state)

    @patch("singer.get_currently_syncing")
    @patch("singer.set_currently_syncing")
    @patch("singer.write_state")
    def test_set_currently_syncing(self, mock_write_state, mock_set_currently_syncing, mock_get_currently_syncing):
        mock_get_currently_syncing.return_value = None
        state = {}

        update_currently_syncing(state, "new_stream")

        mock_get_currently_syncing.assert_not_called()
        mock_set_currently_syncing.assert_called_once_with(state, "new_stream")
        mock_write_state.assert_called_once_with(state)
        self.assertNotIn("currently_syncing", state)
