import unittest
from unittest.mock import patch, MagicMock
from tap_ukg_pro_ultipro.sync import sync, update_currently_syncing


class TestSync(unittest.TestCase):

    @patch("singer.write_schema")
    @patch("singer.get_currently_syncing")
    @patch("singer.Transformer")
    @patch("singer.write_state")
    @patch("tap_ukg_pro_ultipro.streams.abstracts.IncrementalStream.sync")
    def test_sync_stream1_called(self, mock_sync, mock_write_state, mock_transformer, mock_get_currently_syncing, mock_write_schema):
        mock_catalog = MagicMock()
        first_stream = MagicMock()
        first_stream.tap_stream_id = "positions"
        second_stream = MagicMock()
        second_stream.tap_stream_id = "person_details"
        mock_catalog.get_selected_streams.return_value = [
            first_stream,
            second_stream
        ]
        state = {}

        client = MagicMock()
        config = {}

        sync(client, config, mock_catalog, state)

        self.assertEqual(mock_sync.call_count, 2)

    @patch("singer.get_currently_syncing")
    @patch("singer.set_currently_syncing")
    @patch("singer.write_state")
    def test_remove_currently_syncing(self, mock_write_state, mock_set_currently_syncing, mock_get_currently_syncing):
        state = {"currently_syncing": "some_stream"}

        update_currently_syncing(state, None)

        mock_set_currently_syncing.assert_not_called()
        mock_write_state.assert_called_once_with(state)
        self.assertNotIn("currently_syncing", state)

    @patch("singer.write_state")
    def test_remove_currently_syncing_when_not_set(self, mock_write_state):
        state = {"bookmarks": {}}

        update_currently_syncing(state, None)

        self.assertEqual(state, {"bookmarks": {}})
        mock_write_state.assert_called_once_with(state)

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
