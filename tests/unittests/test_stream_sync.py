"""
Unit tests for stream level sync behaviour (pagination, bookmarks, transform).
"""
import base64
import copy
import inspect
import itertools
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from singer import Transformer, metadata, metrics
from singer.catalog import CatalogEntry, Schema

from tap_ukg_pro_ultipro.client import Client, raise_for_error
from tap_ukg_pro_ultipro.exceptions import (
    UKGProBadRequestError,
    UKGProError,
    UKGProInternalServerError,
)
from tap_ukg_pro_ultipro.schema import get_schemas
from tap_ukg_pro_ultipro.streams import STREAMS
from tap_ukg_pro_ultipro.streams.abstracts import BaseStream, validate_bookmark_state

START_DATE = "2022-01-01T00:00:00Z"
WRITE_RECORD = "tap_ukg_pro_ultipro.streams.abstracts.write_record"

_SCHEMAS, _FIELD_METADATA = get_schemas()


def make_entry(stream_name, selected=True):
    """Build a catalog entry the way discovery does, with every field selected."""
    mdata = metadata.to_map(_FIELD_METADATA[stream_name])
    mdata = metadata.write(mdata, (), "selected", selected)
    for field in _SCHEMAS[stream_name].get("properties", {}):
        mdata = metadata.write(mdata, ("properties", field), "selected", True)
    return CatalogEntry(
        stream=stream_name,
        tap_stream_id=stream_name,
        key_properties=STREAMS[stream_name].key_properties,
        schema=Schema.from_dict(_SCHEMAS[stream_name]),
        metadata=metadata.to_list(mdata),
    )


def make_client(pages_by_path=None, error_by_path=None):
    """Mocked client serving `pages_by_path[path][page - 1]`; later pages are empty."""
    client = MagicMock()
    client.config = {"start_date": START_DATE}
    client.build_url.side_effect = lambda path: path
    client.requests = []

    def make_request(method, endpoint, params=None, headers=None, body=None, path=None):
        client.requests.append({"method": method, "endpoint": endpoint, "params": dict(params), "body": body})
        if error_by_path and endpoint in error_by_path:
            raise error_by_path[endpoint]
        pages = (pages_by_path or {}).get(endpoint, [])
        page = params["page"]
        return pages[page - 1] if page <= len(pages) else []

    client.make_request.side_effect = make_request
    return client


def make_stream(stream_name, client, selected=True):
    return STREAMS[stream_name](client, make_entry(stream_name, selected))


def position(code, created):
    return {"positionCode": code, "dateTimeChanged": created}


class TestExtractRecords(unittest.TestCase):

    def setUp(self):
        self.stream = make_stream("roles", make_client())

    def test_list_response_is_returned_as_is(self):
        self.assertEqual(self.stream.extract_records([{"a": 1}]), [{"a": 1}])

    def test_empty_responses_yield_no_records(self):
        for response in (None, [], {}, ""):
            self.assertEqual(self.stream.extract_records(response), [])

    def test_mapping_response_uses_data_key(self):
        self.stream.data_key = "items"
        self.assertEqual(self.stream.extract_records({"items": [{"a": 1}]}), [{"a": 1}])
        self.assertEqual(self.stream.extract_records({"items": None}), [])

    def test_unexpected_response_shape_raises(self):
        with self.assertRaises(UKGProError) as ctx:
            self.stream.extract_records({"unexpected": "payload"})
        self.assertIn("roles", str(ctx.exception))


class TestPagination(unittest.TestCase):

    def test_reads_pages_until_an_empty_page(self):
        path = STREAMS["roles"].path
        client = make_client({path: [[{"id": 1}, {"id": 2}], [{"id": 3}]]})
        stream = make_stream("roles", client)
        stream.url_endpoint = path

        records = list(stream.get_records())

        self.assertEqual(records, [{"id": 1}, {"id": 2}, {"id": 3}])
        self.assertEqual([r["params"]["page"] for r in client.requests], [1, 2, 3])
        for request in client.requests:
            self.assertEqual(request["params"]["per_page"], stream.page_size)
            self.assertEqual(request["method"], "GET")

    def test_single_empty_page_stops_immediately(self):
        client = make_client()
        stream = make_stream("roles", client)

        self.assertEqual(list(stream.get_records()), [])
        self.assertEqual(len(client.requests), 1)

    def test_get_request_sends_no_body(self):
        client = make_client({STREAMS["roles"].path: [[{"id": 1}]]})
        stream = make_stream("roles", client)
        stream.url_endpoint = STREAMS["roles"].path
        list(stream.get_records())

        self.assertTrue(all(r["body"] is None for r in client.requests))


class TestReturnedRecordCount(unittest.TestCase):
    """sync() must return the real total, not the metrics counter value, which resets on every log."""

    def test_total_survives_metrics_counter_resets(self):
        path = STREAMS["roles"].path
        client = make_client({path: [[{"id": 1}, {"id": 2}], [{"id": 3}]]})
        stream = make_stream("roles", client)

        # A log interval of -1 makes the counter log (and reset to 0) on every increment.
        real_counter = metrics.record_counter
        with patch(
            "tap_ukg_pro_ultipro.streams.abstracts.metrics.record_counter",
            side_effect=lambda stream_name: real_counter(stream_name, log_interval=-1),
        ), patch(WRITE_RECORD):
            total = stream.sync(state={}, transformer=Transformer())

        self.assertEqual(total, 3)

    def test_endpoint_ignoring_paging_raises_instead_of_ending_successfully(self):
        client = MagicMock()
        client.make_request.return_value = [{"id": 1}, {"id": 2}]
        stream = make_stream("roles", client)

        with self.assertRaises(UKGProError) as ctx:
            list(stream.get_records())

        self.assertIn("roles", str(ctx.exception))
        self.assertEqual(client.make_request.call_count, 2)

    def test_repeated_page_followed_by_new_data_is_an_error(self):
        client = MagicMock()
        client.make_request.side_effect = [[{"id": "A"}], [{"id": "A"}], [{"id": "B"}], []]
        stream = make_stream("roles", client)

        with self.assertRaises(UKGProError):
            list(stream.get_records())

    def test_params_are_not_shared_between_requests(self):
        path = STREAMS["roles"].path
        client = make_client({path: [[{"id": 1}], [{"id": 2}]]})
        stream = make_stream("roles", client)
        stream.url_endpoint = path
        list(stream.get_records())

        # each recorded request keeps the page it was made with
        self.assertEqual([r["params"]["page"] for r in client.requests], [1, 2, 3])

    def test_error_on_later_page_propagates_after_earlier_records(self):
        client = MagicMock()
        client.make_request.side_effect = [
            [{"id": 1}],
            UKGProInternalServerError("HTTP-error-code: 500"),
        ]
        stream = make_stream("roles", client)
        seen = []

        with self.assertRaises(UKGProInternalServerError):
            for record in stream.get_records():
                seen.append(record)

        self.assertEqual(seen, [{"id": 1}])

    def test_unexpected_response_shape_fails_the_sync(self):
        client = MagicMock()
        client.make_request.return_value = {"unexpected": "payload"}
        stream = make_stream("roles", client)

        with self.assertRaises(UKGProError):
            list(stream.get_records())


class TestFullTableSync(unittest.TestCase):

    @patch(WRITE_RECORD)
    def test_writes_every_record_and_leaves_state_untouched(self, mock_write_record):
        path = STREAMS["roles"].path
        client = make_client({path: [[{"roleId": "1"}, {"roleId": "2"}], [{"roleId": "3"}]]})
        stream = make_stream("roles", client)
        state = {}

        with Transformer() as transformer:
            count = stream.sync(state, transformer)

        self.assertEqual(count, 3)
        self.assertEqual(mock_write_record.call_count, 3)
        self.assertEqual(state, {})

    @patch(WRITE_RECORD)
    def test_unselected_stream_writes_nothing(self, mock_write_record):
        path = STREAMS["roles"].path
        client = make_client({path: [[{"roleId": "1"}]]})
        stream = make_stream("roles", client, selected=False)

        with Transformer() as transformer:
            count = stream.sync({}, transformer)

        self.assertEqual(count, 0)
        mock_write_record.assert_not_called()

    @patch(WRITE_RECORD)
    def test_transform_error_logs_key_properties_not_record_content_and_raises(self, mock_write_record):
        path = STREAMS["roles"].path
        client = make_client({path: [[{"rolID": "R-1", "name": "secret-value"}]]})
        stream = make_stream("roles", client)
        transformer = MagicMock()
        transformer.transform.side_effect = ValueError("schema mismatch")

        with patch("tap_ukg_pro_ultipro.streams.abstracts.LOGGER") as mock_logger:
            with self.assertRaises(ValueError):
                stream.sync({}, transformer)

        mock_logger.error.assert_called_once()
        args = mock_logger.error.call_args.args
        logged = args[0] % args[1:]
        self.assertIn("roles", logged)
        self.assertIn("R-1", logged)
        self.assertIn("schema mismatch", logged)
        self.assertNotIn("secret-value", logged)
        mock_write_record.assert_not_called()


class TestIncrementalSync(unittest.TestCase):
    path = STREAMS["positions"].path

    def run_sync(self, pages, state=None, selected=True, client=None):
        client = client or make_client({self.path: pages})
        stream = make_stream("positions", client, selected)
        state = {} if state is None else state
        with patch(WRITE_RECORD) as mock_write_record:
            with Transformer() as transformer:
                count = stream.sync(state, transformer)
        written = [call.args[1] for call in mock_write_record.call_args_list]
        return count, written, state, client

    @staticmethod
    def bookmark(state):
        return state.get("bookmarks", {}).get("positions", {}).get("dateTimeChanged")

    def test_first_sync_uses_start_date_and_sets_bookmark_to_max_value(self):
        count, written, state, _ = self.run_sync([[
            position("OLD", "2021-12-31T23:59:59Z"),
            position("A", "2022-03-01T00:00:00Z"),
            position("B", "2022-05-01T10:00:00Z"),
            position("C", "2022-04-01T00:00:00Z"),
        ]])

        self.assertEqual(count, 3)
        self.assertEqual([r["positionCode"] for r in written], ["A", "B", "C"])
        self.assertEqual(self.bookmark(state), "2022-05-01T10:00:00.000000Z")

    def test_record_at_start_date_is_included_despite_different_string_formats(self):
        # the start date has no fractional seconds, transformed records do
        count, written, state, _ = self.run_sync([[position("EDGE", START_DATE)]])

        self.assertEqual(count, 1)
        self.assertEqual(written[0]["positionCode"], "EDGE")
        # nothing is newer than the start date, so no bookmark is written
        self.assertIsNone(self.bookmark(state))

    def test_existing_bookmark_filters_older_records(self):
        state = {"bookmarks": {"positions": {"dateTimeChanged": "2022-06-01T00:00:00.000000Z"}}}
        count, written, state, _ = self.run_sync([[
            position("OLD", "2022-05-31T23:59:59Z"),
            position("SAME", "2022-06-01T00:00:00Z"),
            position("NEW", "2022-06-02T00:00:00Z"),
        ]], state)

        self.assertEqual([r["positionCode"] for r in written], ["SAME", "NEW"])
        self.assertEqual(count, 2)
        self.assertEqual(self.bookmark(state), "2022-06-02T00:00:00.000000Z")

    def test_bookmark_does_not_move_when_no_newer_records(self):
        original = {"bookmarks": {"positions": {"dateTimeChanged": "2022-06-01T00:00:00.000000Z"}}}
        state = copy.deepcopy(original)
        _, written, state, _ = self.run_sync([[position("OLD", "2022-01-02T00:00:00Z")]], state)

        self.assertEqual(written, [])
        self.assertEqual(state, original)

    def test_record_without_replication_value_is_written_but_keeps_bookmark(self):
        count, written, state, _ = self.run_sync([[
            position("NULL", None),
            {"positionCode": "MISSING"},
            position("A", "2022-03-01T00:00:00Z"),
        ]])

        self.assertEqual(count, 3)
        self.assertEqual([r["positionCode"] for r in written], ["NULL", "MISSING", "A"])
        self.assertEqual(self.bookmark(state), "2022-03-01T00:00:00.000000Z")

    def test_bookmark_is_saved_only_after_all_pages_are_read(self):
        client = MagicMock()
        client.config = {"start_date": START_DATE}
        client.build_url.side_effect = lambda path: path
        client.make_request.side_effect = [
            [position("A", "2022-03-01T00:00:00Z")],
            UKGProInternalServerError("HTTP-error-code: 500"),
        ]
        state = {}

        with self.assertRaises(UKGProInternalServerError):
            self.run_sync(None, state, client=client)

        self.assertEqual(state, {})

    def test_unselected_stream_writes_no_records(self):
        count, written, _, _ = self.run_sync([[position("A", "2022-03-01T00:00:00Z")]], selected=False)

        self.assertEqual(count, 0)
        self.assertEqual(written, [])

    def test_invalid_start_date_raises(self):
        client = make_client({self.path: [[position("A", "2022-03-01T00:00:00Z")]]})
        client.config = {"start_date": "not-a-date"}

        with self.assertRaises(UKGProError):
            self.run_sync(None, client=client)

    def test_no_server_side_filter_is_sent_until_one_is_verified(self):
        _, _, _, client = self.run_sync([[position("A", "2022-03-01T00:00:00Z")]])

        for request in client.requests:
            self.assertEqual(set(request["params"]), {"page", "per_page"})

    def test_configured_bookmark_query_param_is_sent(self):
        client = make_client({self.path: [[position("A", "2022-03-01T00:00:00Z")]]})
        with patch.object(STREAMS["positions"], "bookmark_query_param", "createdSince"):
            self.run_sync(None, client=client)

        self.assertEqual(client.requests[0]["params"]["createdSince"], START_DATE)

    def test_position_reports_follows_its_incremental_catalog_metadata(self):
        stream_class = STREAMS["position_reports"]
        self.assertEqual(stream_class.replication_method, "INCREMENTAL")

        client = make_client({stream_class.path: [[position("A", "2022-03-01T00:00:00Z")]]})
        stream = make_stream("position_reports", client)
        state = {}
        with patch(WRITE_RECORD):
            with Transformer() as transformer:
                stream.sync(state, transformer)

        self.assertEqual(
            state["bookmarks"]["position_reports"]["dateTimeChanged"],
            "2022-03-01T00:00:00.000000Z",
        )


class TestWriteBookmark(unittest.TestCase):

    def setUp(self):
        self.stream = make_stream("positions", make_client())

    def test_bookmark_never_moves_backwards(self):
        state = {"bookmarks": {"positions": {"dateTimeChanged": "2022-06-01T00:00:00.000000Z"}}}
        self.stream.write_bookmark(state, "positions", value="2022-05-01T00:00:00.000000Z")

        self.assertEqual(state["bookmarks"]["positions"]["dateTimeChanged"], "2022-06-01T00:00:00.000000Z")

    def test_formats_are_compared_as_datetimes(self):
        # '.' sorts before 'Z', so a string comparison would wrongly keep the start date
        state = self.stream.write_bookmark({}, "positions", value="2022-01-01T00:00:00.500000Z")

        self.assertEqual(state["bookmarks"]["positions"]["dateTimeChanged"], "2022-01-01T00:00:00.500000Z")

    def test_unparseable_values_fall_back_to_plain_comparison(self):
        state = self.stream.write_bookmark({}, "positions", "dateTimeChanged", value="zzz")

        self.assertEqual(state["bookmarks"]["positions"]["dateTimeChanged"], "zzz")


class TestLoopSafety(unittest.TestCase):

    def test_exceeding_max_pages_raises_instead_of_looping_or_truncating(self):
        client = MagicMock()
        counter = itertools.count()
        # every page is different and never empty, so only the page limit can stop the loop
        client.make_request.side_effect = lambda *args, **kwargs: [{"id": next(counter)}]
        stream = make_stream("roles", client)
        stream.max_pages = 3
        seen = []

        with self.assertRaises(UKGProError) as ctx:
            for record in stream.get_records():
                seen.append(record)

        self.assertEqual(client.make_request.call_count, 3)
        self.assertEqual(len(seen), 3)
        self.assertIn("roles", str(ctx.exception))

    def test_data_ending_before_max_pages_is_not_an_error(self):
        path = STREAMS["roles"].path
        client = make_client({path: [[{"id": 1}], [{"id": 2}]]})
        stream = make_stream("roles", client)
        stream.url_endpoint = path
        stream.max_pages = 3

        self.assertEqual(list(stream.get_records()), [{"id": 1}, {"id": 2}])

    def test_pagination_loop_has_an_explicit_condition(self):
        self.assertNotIn("while True", inspect.getsource(BaseStream.get_records))


class TestSkippedRecordLogging(unittest.TestCase):

    def test_records_older_than_the_bookmark_are_counted_and_logged(self):
        path = STREAMS["positions"].path
        client = make_client({path: [[
            position("OLD1", "2021-01-01T00:00:00Z"),
            position("OLD2", "2021-02-01T00:00:00Z"),
            position("NEW", "2022-03-01T00:00:00Z"),
        ]]})
        stream = make_stream("positions", client)

        with patch(WRITE_RECORD):
            with patch("tap_ukg_pro_ultipro.streams.abstracts.LOGGER") as mock_logger:
                with Transformer() as transformer:
                    count = stream.sync({}, transformer)

        self.assertEqual(count, 1)
        messages = [call.args[0] % call.args[1:] for call in mock_logger.info.call_args_list]
        self.assertTrue(any("skipped 2 record(s)" in message for message in messages), messages)

    def test_nothing_is_logged_when_no_record_is_skipped(self):
        path = STREAMS["positions"].path
        client = make_client({path: [[position("NEW", "2022-03-01T00:00:00Z")]]})
        stream = make_stream("positions", client)

        with patch(WRITE_RECORD):
            with patch("tap_ukg_pro_ultipro.streams.abstracts.LOGGER") as mock_logger:
                with Transformer() as transformer:
                    stream.sync({}, transformer)

        mock_logger.info.assert_not_called()


class TestBookmarkStateValidation(unittest.TestCase):

    def setUp(self):
        self.stream = make_stream("positions", make_client())

    def test_valid_states_are_accepted(self):
        for state in (
            {},
            {"bookmarks": {}},
            {"bookmarks": {"other": {"x": 1}}},
            {"bookmarks": {"positions": {"dateTimeChanged": "2022-06-01T00:00:00.000000Z"}}},
            {"currently_syncing": "positions"},
        ):
            validate_bookmark_state(state, "positions")

    def test_malformed_states_raise_a_clear_error(self):
        for state in (
            [],
            "state",
            {"bookmarks": []},
            {"bookmarks": "x"},
            {"bookmarks": {"positions": "2022-06-01T00:00:00Z"}},
            {"bookmarks": {"positions": None}},
        ):
            with self.assertRaises(UKGProError, msg=repr(state)):
                validate_bookmark_state(state, "positions")

    def test_get_bookmark_rejects_a_malformed_state(self):
        with self.assertRaises(UKGProError):
            self.stream.get_bookmark({"bookmarks": {"positions": "2022-06-01T00:00:00Z"}}, "positions")

    def test_write_bookmark_rejects_a_malformed_state_without_changing_it(self):
        state = {"bookmarks": []}
        with self.assertRaises(UKGProError):
            self.stream.write_bookmark(state, "positions", value="2022-06-01T00:00:00.000000Z")
        self.assertEqual(state, {"bookmarks": []})

    def test_sync_fails_before_requesting_data_when_state_is_malformed(self):
        client = make_client({STREAMS["positions"].path: [[position("A", "2022-03-01T00:00:00Z")]]})
        stream = make_stream("positions", client)

        with self.assertRaises(UKGProError):
            with Transformer() as transformer:
                stream.sync({"bookmarks": {"positions": "bad"}}, transformer)

        self.assertEqual(client.requests, [])


class TestClientLogging(unittest.TestCase):

    def setUp(self):
        self.client = Client({
            "username": "dummy_user", "password": "dummy_password", "api_key": "dummy_api_key",
            "hostname": "servicet.ultipro.com", "start_date": START_DATE,
        })

    @staticmethod
    def logged(mock_logger):
        return [call.args[0] % call.args[1:] for call in mock_logger.mock_calls if call.args]

    def test_requests_do_not_log_the_customer_hostname_or_credentials(self):
        response = MagicMock(status_code=200)
        response.json.return_value = []

        with patch("tap_ukg_pro_ultipro.client.LOGGER") as mock_logger:
            with patch.object(self.client._session, "request", return_value=response):
                self.client.make_request("GET", "", {"page": 2, "per_page": 100}, path="/configuration/v1/roles")

        text = " ".join(self.logged(mock_logger))
        encoded = base64.b64encode(b"dummy_user:dummy_password").decode()
        for secret in ("servicet.ultipro.com", "dummy_user", "dummy_password", "dummy_api_key", encoded):
            self.assertNotIn(secret, text)

    def test_api_error_logs_status_code_but_not_body(self):
        response = MagicMock(status_code=400)
        response.json.return_value = {"message": "dedCode is required"}

        with patch("tap_ukg_pro_ultipro.client.LOGGER") as mock_logger:
            with self.assertRaises(UKGProBadRequestError) as ctx:
                raise_for_error(response)

        text = " ".join(self.logged(mock_logger))
        self.assertIn("400", text)
        self.assertNotIn("dedCode is required", text)
        self.assertIn("dedCode is required", str(ctx.exception))

    def test_long_error_bodies_are_never_logged(self):
        response = MagicMock(status_code=500)
        response.json.side_effect = ValueError("not json")
        response.text = "x" * 5000

        with patch("tap_ukg_pro_ultipro.client.LOGGER") as mock_logger:
            with self.assertRaises(UKGProInternalServerError):
                raise_for_error(response)

        text = " ".join(self.logged(mock_logger))
        self.assertNotIn("xxx", text)
        self.assertLess(len(text), 200)

    def test_successful_response_logs_no_error(self):
        response = MagicMock(status_code=200)
        response.json.return_value = []

        with patch("tap_ukg_pro_ultipro.client.LOGGER") as mock_logger:
            raise_for_error(response)

        mock_logger.error.assert_not_called()


class TestClientNoContent(unittest.TestCase):

    def test_204_response_returns_none_instead_of_parsing_a_body(self):
        from tap_ukg_pro_ultipro.client import Client

        client = Client({
            "username": "u", "password": "p", "api_key": "k",
            "hostname": "servicet.ultipro.com", "start_date": START_DATE,
        })
        response = MagicMock(status_code=204)
        response.json.side_effect = ValueError("no body")

        with patch.object(client._session, "request", return_value=response):
            self.assertIsNone(client.make_request("GET", "", path="/configuration/v1/roles"))


class TestEmployeeChangesSync(unittest.TestCase):
    """employee_changes: explicit extraction window and bookmarking on emplStatusStartDate."""
    stream_name = "employee_changes"
    path = STREAMS["employee_changes"].path
    now = datetime(2026, 11, 20, 12, 0, 0, tzinfo=timezone.utc)
    now_param = "2026-11-20T12:00:00Z"
    write_record = "tap_ukg_pro_ultipro.streams.employee_changes.write_record"
    utc_now = "tap_ukg_pro_ultipro.streams.employee_changes.utc_now"

    @staticmethod
    def change(employee_id, status_start, company_id="C1"):
        return {"employeeId": employee_id, "companyId": company_id, "emplStatusStartDate": status_start}

    @staticmethod
    def state_with(value):
        return {"bookmarks": {"employee_changes": {"emplStatusStartDate": value}}}

    @staticmethod
    def bookmark(state):
        return state.get("bookmarks", {}).get("employee_changes", {}).get("emplStatusStartDate")

    def run_sync(self, pages=None, state=None, client=None):
        client = client or make_client({self.path: pages})
        stream = make_stream(self.stream_name, client)
        state = {} if state is None else state
        with patch(self.utc_now, return_value=self.now), patch(self.write_record) as mock_write:
            with Transformer() as transformer:
                count = stream.sync(state, transformer)
        written = [call.args[1] for call in mock_write.call_args_list]
        return count, written, state, client

    def failing_client(self, first_page):
        client = make_client({self.path: [first_page]})
        original = client.make_request.side_effect

        def make_request(method, endpoint, params=None, *args, **kwargs):
            if params["page"] == 2:
                raise UKGProInternalServerError("HTTP-error-code: 500")
            return original(method, endpoint, params, *args, **kwargs)

        client.make_request.side_effect = make_request
        return client

    def test_stream_definition(self):
        stream_class = STREAMS[self.stream_name]
        self.assertEqual(stream_class.key_properties, ["employeeId", "companyId"])
        self.assertEqual(stream_class.replication_method, "INCREMENTAL")
        self.assertEqual(stream_class.replication_keys, ["emplStatusStartDate"])
        self.assertEqual(stream_class.page_size, 200)

    def test_first_run_uses_config_start_date_and_a_fixed_end_date(self):
        _, _, _, client = self.run_sync([[self.change("E1", "2024-01-01T00:00:00Z")]])

        self.assertEqual(client.requests[0]["endpoint"], self.path)
        self.assertEqual(client.requests[0]["params"], {
            "startDate": START_DATE, "endDate": self.now_param, "per_page": 200, "page": 1,
        })

    def test_initial_start_date_follows_the_config_value(self):
        client = make_client({self.path: [[]]})
        client.config = {"start_date": "2000-01-01T00:00:00Z"}

        self.run_sync(client=client)

        self.assertEqual(client.requests[0]["params"]["startDate"], "2000-01-01T00:00:00Z")

    def test_missing_invalid_or_future_start_date_fails_before_any_request(self):
        for config in ({}, {"start_date": "not-a-date"}, {"start_date": "2027-01-01T00:00:00Z"}):
            client = make_client({self.path: [[]]})
            client.config = config

            with self.assertRaises(UKGProError, msg=repr(config)):
                self.run_sync(client=client)

            self.assertEqual(client.requests, [])

    def test_later_runs_use_the_previous_bookmark_as_start_date(self):
        _, _, _, client = self.run_sync([[]], self.state_with("2025-06-15T08:30:00.000000Z"))

        self.assertEqual(client.requests[0]["params"], {
            "startDate": "2025-06-15T08:30:00Z", "endDate": self.now_param, "per_page": 200, "page": 1,
        })

    def test_end_date_is_captured_once_and_reused_by_every_page(self):
        client = make_client({self.path: [
            [self.change("E1", "2024-01-01T00:00:00Z")],
            [self.change("E2", "2024-01-02T00:00:00Z")],
            [self.change("E3", "2024-01-03T00:00:00Z")],
        ]})
        stream = make_stream(self.stream_name, client)
        clock = [self.now + timedelta(minutes=10 * i) for i in range(20)]

        with patch(self.utc_now, side_effect=clock) as mock_now, patch(self.write_record):
            with Transformer() as transformer:
                stream.sync({}, transformer)

        self.assertEqual(mock_now.call_count, 1)
        self.assertEqual([r["params"]["page"] for r in client.requests], [1, 2, 3, 4])
        self.assertEqual({r["params"]["endDate"] for r in client.requests}, {self.now_param})
        self.assertEqual({r["params"]["startDate"] for r in client.requests}, {START_DATE})

    def test_bookmark_is_the_greatest_status_date_and_records_are_not_filtered(self):
        state = self.state_with("2025-06-15T08:30:00.000000Z")
        count, written, state, _ = self.run_sync([[
            self.change("OLDER", "2025-06-15T08:00:00Z"),
            self.change("NEWER", "2025-06-16T00:00:00Z"),
            self.change("NULL", None),
            {"employeeId": "MISSING"},
        ]], state)

        self.assertEqual(count, 4)
        self.assertEqual([r["employeeId"] for r in written], ["OLDER", "NEWER", "NULL", "MISSING"])
        self.assertEqual(self.bookmark(state), "2025-06-16T00:00:00.000000Z")

    def test_bookmark_is_capped_at_end_date_and_never_moves_backwards(self):
        _, _, state, _ = self.run_sync([[self.change("E1", "2027-05-01T00:00:00Z")]])
        self.assertEqual(self.bookmark(state), "2026-11-20T12:00:00.000000Z")

        original = self.state_with("2025-06-15T08:30:00.000000Z")
        state = copy.deepcopy(original)
        self.run_sync([[self.change("E1", "2025-06-10T00:00:00Z")]], state)
        self.assertEqual(state, original)

    def test_no_records_and_unrelated_state(self):
        _, written, state, _ = self.run_sync([[]])
        self.assertEqual((written, state), ([], {}))

        state = self.state_with("2025-06-15T08:30:00.000000Z")
        state["bookmarks"]["positions"] = {"dateTimeChanged": "2025-01-01T00:00:00.000000Z"}
        state["currently_syncing"] = self.stream_name
        expected = copy.deepcopy(state)
        expected["bookmarks"][self.stream_name]["emplStatusStartDate"] = "2025-07-01T00:00:00.000000Z"

        self.run_sync([[self.change("E1", "2025-07-01T00:00:00Z")]], state)

        self.assertEqual(state, expected)

    def test_bad_bookmark_state_fails_before_any_request(self):
        for state in (
            {"bookmarks": {self.stream_name: "2025-06-15T08:30:00Z"}},
            self.state_with("not-a-date"),
            self.state_with("2027-01-01T00:00:00.000000Z"),
        ):
            client = make_client({self.path: [[]]})

            with self.assertRaises(UKGProError, msg=repr(state)):
                self.run_sync(state=state, client=client)

            self.assertEqual(client.requests, [])

    def test_failure_on_a_later_page_leaves_state_untouched(self):
        for original in ({}, self.state_with("2025-06-15T08:30:00.000000Z")):
            state = copy.deepcopy(original)
            client = self.failing_client([self.change("E1", "2025-08-01T00:00:00Z")])

            with self.assertRaises(UKGProInternalServerError):
                self.run_sync(state=state, client=client)

            self.assertEqual(state, original)

    def test_looping_pagination_fails_instead_of_saving_a_bookmark(self):
        client = MagicMock()
        client.config = {"start_date": START_DATE}
        client.build_url.side_effect = lambda path: path
        client.make_request.return_value = [self.change("E1", "2025-08-01T00:00:00Z")]
        state = {}

        with self.assertRaises(UKGProError):
            self.run_sync(state=state, client=client)

        self.assertEqual(state, {})

    def test_repeated_identities_are_all_written(self):
        count, written, _, _ = self.run_sync([[
            self.change("E1", "2024-01-01T00:00:00Z"),
            self.change("E1", "2024-02-01T00:00:00Z"),
            self.change("E1", "2024-03-01T00:00:00Z", company_id="C2"),
        ]])

        self.assertEqual(count, 3)
        self.assertEqual(
            [(r["employeeId"], r["companyId"], r["emplStatusStartDate"][:10]) for r in written],
            [("E1", "C1", "2024-01-01"), ("E1", "C1", "2024-02-01"), ("E1", "C2", "2024-03-01")],
        )


class TestDailyPayDateStreams(unittest.TestCase):
    """earnings_history_base_elements and payroll_deductions_history: one payDate request series per day."""
    today = datetime(2025, 6, 3, 15, 0, tzinfo=timezone.utc)
    clock = "tap_ukg_pro_ultipro.streams.{}.datetime"
    names = ("earnings_history_base_elements", "payroll_deductions_history")

    @staticmethod
    def record(name, n, day):
        row = {"employeeId": "E%d" % n, "companyId": "C", "payDate": "%sT00:00:00Z" % day}
        if name == "payroll_deductions_history":
            row["recordId"] = n
        return row

    def run_sync(self, name, data, state=None, start_date=START_DATE, entry=None, **config):
        client = MagicMock()
        client.config = {"start_date": start_date, **config}
        client.build_url.side_effect = lambda path: path
        client.requests = []

        def make_request(method, endpoint, params=None, headers=None, body=None, path=None):
            client.requests.append(dict(params))
            rows = data.get(params["payDate"], [])
            start = (params["page"] - 1) * params["per_page"]
            return rows[start:start + params["per_page"]]

        client.make_request.side_effect = make_request
        today = self.today

        class FakeDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return today

        stream = STREAMS[name](client, entry or make_entry(name))
        state = {} if state is None else state
        with patch(self.clock.format(name), FakeDatetime), patch(WRITE_RECORD) as mock_write:
            with Transformer() as transformer:
                stream.sync(state, transformer)
        return [call.args[1] for call in mock_write.call_args_list], client.requests, state

    def test_stream_definitions(self):
        self.assertEqual(STREAMS["earnings_history_base_elements"].key_properties, [])
        self.assertEqual(STREAMS["payroll_deductions_history"].key_properties, ["recordId"])
        for name in self.names:
            self.assertEqual(STREAMS[name].replication_method, "INCREMENTAL")
            self.assertEqual(STREAMS[name].replication_keys, ["payDate"])

    def test_one_request_series_per_day_from_the_start_day_to_today(self):
        for name in self.names:
            with self.subTest(name):
                data = {"2025-06-01": [self.record(name, n, "2025-06-01") for n in range(1500)]}
                written, requests, state = self.run_sync(name, data, start_date="2025-05-31T00:00:00Z")

                self.assertEqual(len(written), 1500)
                self.assertEqual(
                    [(r["payDate"], r["page"]) for r in requests],
                    [("2025-05-31", 1), ("2025-06-01", 1), ("2025-06-01", 2), ("2025-06-01", 3),
                     ("2025-06-02", 1), ("2025-06-03", 1)],
                )
                self.assertEqual(state["bookmarks"][name]["payDate"], "2025-06-01T00:00:00.000000Z")

    def test_start_date_with_a_time_of_day_still_reads_that_days_records(self):
        for name in self.names:
            with self.subTest(name):
                data = {"2025-06-01": [self.record(name, 1, "2025-06-01")]}
                written, requests, _ = self.run_sync(name, data, start_date="2025-06-01T12:00:00Z")

                self.assertEqual(requests[0]["payDate"], "2025-06-01")
                self.assertEqual(len(written), 1)

    def test_bookmark_with_a_time_of_day_still_reads_that_days_records(self):
        for name in self.names:
            with self.subTest(name):
                state = {"bookmarks": {name: {"payDate": "2025-06-01T12:00:00.000000Z"}}}
                data = {
                    "2025-06-01": [self.record(name, 1, "2025-06-01")],
                    "2025-06-02": [self.record(name, 2, "2025-06-02")],
                }
                written, requests, state = self.run_sync(name, data, state)

                self.assertEqual(requests[0]["payDate"], "2025-06-01")
                self.assertEqual(len(written), 2)
                self.assertEqual(state["bookmarks"][name]["payDate"], "2025-06-02T00:00:00.000000Z")

    def test_non_utc_and_naive_bookmarks_are_converted_to_utc_before_truncating(self):
        cases = (
            ("2025-06-01T02:00:00+05:30", "2025-05-31"),
            ("2025-06-01T23:00:00-05:00", "2025-06-02"),
            ("2025-06-01T12:00:00", "2025-06-01"),
        )
        for name in self.names:
            for value, expected_day in cases:
                with self.subTest(stream=name, bookmark=value):
                    state = {"bookmarks": {name: {"payDate": value}}}
                    _, requests, _ = self.run_sync(name, {}, state)

                    self.assertEqual(requests[0]["payDate"], expected_day)

    def test_lookback_days_rereads_the_last_days_before_the_bookmark(self):
        for name in self.names:
            with self.subTest(name):
                original = {"bookmarks": {name: {"payDate": "2025-06-02T00:00:00.000000Z"}}}
                state = copy.deepcopy(original)
                data = {
                    "2025-05-30": [self.record(name, 1, "2025-05-30")],
                    "2025-06-02": [self.record(name, 2, "2025-06-02")],
                }
                written, requests, state = self.run_sync(name, data, state, lookback_days=3)

                self.assertEqual(requests[0]["payDate"], "2025-05-30")
                self.assertEqual(len(written), 2)
                self.assertEqual(state, original)

    def test_lookback_never_goes_before_start_date_or_applies_to_the_first_run(self):
        for name in self.names:
            with self.subTest(name):
                state = {"bookmarks": {name: {"payDate": "2025-06-02T00:00:00.000000Z"}}}
                _, requests, _ = self.run_sync(name, {}, state, start_date="2025-06-01T00:00:00Z", lookback_days=10)
                self.assertEqual(requests[0]["payDate"], "2025-06-01")

                _, requests, _ = self.run_sync(name, {}, start_date="2025-06-01T00:00:00Z", lookback_days=5)
                self.assertEqual(requests[0]["payDate"], "2025-06-01")

    def test_lookback_days_accepts_a_numeric_string(self):
        for name in self.names:
            with self.subTest(name):
                state = {"bookmarks": {name: {"payDate": "2025-06-02T00:00:00.000000Z"}}}
                _, requests, _ = self.run_sync(name, {}, state, lookback_days="1")
                self.assertEqual(requests[0]["payDate"], "2025-06-01")

    def test_a_bookmark_before_start_date_is_never_moved_forward(self):
        for name in self.names:
            for lookback in (0, 5):
                with self.subTest(stream=name, lookback_days=lookback):
                    state = {"bookmarks": {name: {"payDate": "2025-06-02T00:00:00.000000Z"}}}
                    _, requests, _ = self.run_sync(
                        name, {}, state, start_date="2025-06-10T00:00:00Z", lookback_days=lookback
                    )
                    self.assertEqual(requests[0]["payDate"], "2025-06-02")

    def test_a_huge_lookback_is_capped_at_start_date(self):
        for name in self.names:
            with self.subTest(name):
                state = {"bookmarks": {name: {"payDate": "2025-06-02T00:00:00.000000Z"}}}
                _, requests, _ = self.run_sync(
                    name, {}, state, start_date="2025-05-20T00:00:00Z", lookback_days=10 ** 12
                )
                self.assertEqual(requests[0]["payDate"], "2025-05-20")

    def test_bookmark_advances_with_lookback_and_replayed_days_do_not_lower_it(self):
        for name in self.names:
            with self.subTest(name):
                state = {"bookmarks": {name: {"payDate": "2025-06-02T00:00:00.000000Z"}}}
                data = {
                    "2025-05-30": [self.record(name, 1, "2025-05-30")],
                    "2025-06-02": [self.record(name, 2, "2025-06-02")],
                    "2025-06-03": [self.record(name, 3, "2025-06-03")],
                }
                written, _, state = self.run_sync(name, data, state, lookback_days=3)

                self.assertEqual(len(written), 3)
                self.assertEqual(state["bookmarks"][name]["payDate"], "2025-06-03T00:00:00.000000Z")

    def test_replayed_days_keep_a_stored_bookmark_that_has_a_time_of_day(self):
        for name in self.names:
            with self.subTest(name):
                original = {"bookmarks": {name: {"payDate": "2025-06-02T12:00:00.000000Z"}}}
                state = copy.deepcopy(original)
                data = {"2025-06-01": [self.record(name, 1, "2025-06-01")]}
                written, _, state = self.run_sync(name, data, state, lookback_days=2)

                self.assertEqual(len(written), 1)
                self.assertEqual(state, original)

    def test_invalid_lookback_days_fails_before_any_request(self):
        for name in self.names:
            for value in (-1, "abc", 1.5, True):
                with self.subTest(stream=name, value=value):
                    client = MagicMock()
                    client.config = {"start_date": START_DATE, "lookback_days": value}
                    client.build_url.side_effect = lambda path: path
                    stream = STREAMS[name](client, make_entry(name))

                    with patch(WRITE_RECORD), Transformer() as transformer:
                        with self.assertRaises(UKGProError):
                            stream.sync({}, transformer)

                    client.make_request.assert_not_called()

    def test_bookmark_day_is_read_again_and_earlier_days_are_not_requested(self):
        for name in self.names:
            with self.subTest(name):
                state = {"bookmarks": {name: {"payDate": "2025-06-02T00:00:00.000000Z"}}}
                data = {"2025-06-02": [self.record(name, 2, "2025-06-02")]}
                written, requests, _ = self.run_sync(name, data, state)

                self.assertEqual(sorted({r["payDate"] for r in requests}), ["2025-06-02", "2025-06-03"])
                self.assertEqual(len(written), 1)

    def test_payDate_is_kept_and_bookmarked_when_a_saved_catalog_deselects_it(self):
        for name in self.names:
            with self.subTest(name):
                entry = make_entry(name)
                mdata = metadata.to_map(entry.metadata)
                mdata = metadata.write(mdata, ("properties", "payDate"), "inclusion", "available")
                mdata = metadata.write(mdata, ("properties", "payDate"), "selected", False)
                entry.metadata = metadata.to_list(mdata)
                data = {"2025-06-02": [self.record(name, 2, "2025-06-02")]}

                written, _, state = self.run_sync(name, data, entry=entry)

                self.assertEqual(written[0]["payDate"], "2025-06-02T00:00:00.000000Z")
                self.assertEqual(state["bookmarks"][name]["payDate"], "2025-06-02T00:00:00.000000Z")

    def test_failure_on_a_later_day_leaves_state_untouched(self):
        for name in self.names:
            with self.subTest(name):
                client = MagicMock()
                client.config = {"start_date": "2025-06-01T00:00:00Z"}
                client.build_url.side_effect = lambda path: path

                def make_request(method, endpoint, params=None, *args, **kwargs):
                    if params["payDate"] == "2025-06-02":
                        raise UKGProInternalServerError("HTTP-error-code: 500")
                    return [self.record(name, 1, "2025-06-01")] if params["page"] == 1 else []

                client.make_request.side_effect = make_request
                stream = STREAMS[name](client, make_entry(name))
                state = {}
                today = self.today

                class FakeDatetime(datetime):
                    @classmethod
                    def now(cls, tz=None):
                        return today

                with patch(self.clock.format(name), FakeDatetime), patch(WRITE_RECORD):
                    with Transformer() as transformer:
                        with self.assertRaises(UKGProInternalServerError):
                            stream.sync(state, transformer)

                self.assertEqual(state, {})

    def test_other_incremental_streams_keep_their_bookmark_handling(self):
        stream = make_stream("positions", make_client())

        self.assertEqual(stream.get_bookmark({}, "positions"), START_DATE)
        self.assertFalse(hasattr(stream, "_start_bookmark"))
