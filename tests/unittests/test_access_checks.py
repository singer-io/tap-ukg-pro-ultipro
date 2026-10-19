import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

from parameterized import parameterized
from requests.exceptions import JSONDecodeError
from singer.catalog import Catalog, CatalogEntry, Schema

from tap_ukg_pro_ultipro import do_discover
from tap_ukg_pro_ultipro.client import Client
from tap_ukg_pro_ultipro.discover import _apply_access_checks, discover
from tap_ukg_pro_ultipro.exceptions import (
    UKGProBadRequestError,
    UKGProForbiddenError,
    UKGProInternalServerError,
    UKGProNotFoundError,
    UKGProRateLimitError,
    UKGProUnauthorizedError,
)
from tap_ukg_pro_ultipro.schema import get_schemas
from tap_ukg_pro_ultipro.streams import STREAMS
from tap_ukg_pro_ultipro.streams.abstracts import BaseStream

CONFIG = {
    "username": "dummy_user",
    "password": "dummy_password",
    "api_key": "dummy_api_key",
    "hostname": "servicet.example.com",
    "start_date": "2022-01-01T00:00:00Z",
}
SECRETS = ("dummy_user", "dummy_password", "dummy_api_key", "servicet.example.com")

# Endpoints that need query parameters and answer HTTP 400 without them.
REQUIRED_PARAM_STREAMS = ("employee_deductions", "open_enrollment_employee_deductions")


class FakeResponse:
    """Minimal stand-in for requests.Response used by the real Client."""

    def __init__(self, status_code, body=None):
        self.status_code = status_code
        self._body = body

    def json(self):
        if self._body is None:
            raise JSONDecodeError("Expecting value", "", 0)
        return self._body


def make_stream(stream_name, client=None):
    """Build a real stream object from its generated catalog entry."""
    schemas, field_metadata = get_schemas()
    entry = CatalogEntry(
        stream=stream_name,
        tap_stream_id=stream_name,
        schema=Schema.from_dict(schemas[stream_name]),
        metadata=field_metadata[stream_name],
    )
    return STREAMS[stream_name](client or MagicMock(), entry)


def fake_stream(stream_name, accessible=True, error=None):
    stream = MagicMock()
    stream.tap_stream_id = stream_name
    stream.check_access.return_value = accessible
    if error:
        stream.check_access.side_effect = error
    return stream


class TestStreamCheckAccess(unittest.TestCase):
    """BaseStream.check_access with the client mocked."""

    def test_accessible_stream_returns_true_with_one_record_probe(self):
        client = MagicMock()
        client.make_request.return_value = [{"roleId": "1"}]
        stream = make_stream("roles", client)

        self.assertTrue(stream.check_access())

        args = client.make_request.call_args.args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], client.build_url.return_value)
        client.build_url.assert_called_once_with(stream.path)
        self.assertEqual(args[2], {"per_page": 1, "page": 1})

    def test_probe_params_are_not_shared_between_calls(self):
        client = MagicMock()
        client.make_request.return_value = []
        stream = make_stream("roles", client)
        stream.check_access()
        client.make_request.call_args.args[2]["page"] = 99
        self.assertEqual(stream.access_check_params, {"per_page": 1, "page": 1})

    @parameterized.expand([
        ["empty list", []],
        ["empty dict", {}],
        ["none", None],
    ])
    def test_empty_successful_response_is_accessible(self, name, response):
        client = MagicMock()
        client.make_request.return_value = response
        self.assertTrue(make_stream("roles", client).check_access())

    def test_forbidden_returns_false_and_warns_without_sensitive_data(self):
        client = MagicMock()
        client.make_request.side_effect = UKGProForbiddenError(
            "HTTP-error-code: 403, Error: Authorization has been denied for this request."
        )
        stream = make_stream("roles", client)

        with patch("tap_ukg_pro_ultipro.streams.abstracts.LOGGER") as mock_logger:
            self.assertFalse(stream.check_access())

        mock_logger.warning.assert_called_once()
        logged = " ".join(str(a) for a in mock_logger.warning.call_args.args)
        self.assertIn("roles", logged)
        self.assertIn("403", logged)
        for secret in SECRETS:
            self.assertNotIn(secret, logged)

    @parameterized.expand([
        ["400", UKGProBadRequestError],
        ["401", UKGProUnauthorizedError],
        ["404", UKGProNotFoundError],
        ["429", UKGProRateLimitError],
        ["500", UKGProInternalServerError],
    ])
    def test_non_403_errors_propagate_for_regular_streams(self, name, error):
        client = MagicMock()
        client.make_request.side_effect = error("HTTP-error")
        with self.assertRaises(error):
            make_stream("roles", client).check_access()

    @parameterized.expand([[name] for name in REQUIRED_PARAM_STREAMS])
    def test_400_from_required_param_endpoint_is_not_treated_as_403(self, stream_name):
        client = MagicMock()
        client.make_request.side_effect = UKGProBadRequestError("HTTP-error-code: 400")
        with patch("tap_ukg_pro_ultipro.streams.abstracts.LOGGER") as mock_logger:
            with self.assertRaises(UKGProBadRequestError):
                make_stream(stream_name, client).check_access()
        # not classified as an access failure, so no exclusion warning is logged
        mock_logger.warning.assert_not_called()

    @parameterized.expand([[name] for name in REQUIRED_PARAM_STREAMS])
    def test_403_from_required_param_endpoint_is_excluded(self, stream_name):
        client = MagicMock()
        client.make_request.side_effect = UKGProForbiddenError("HTTP-error-code: 403")
        self.assertFalse(make_stream(stream_name, client).check_access())

    @parameterized.expand([[name] for name in REQUIRED_PARAM_STREAMS])
    def test_other_errors_from_required_param_endpoint_still_propagate(self, stream_name):
        client = MagicMock()
        client.make_request.side_effect = UKGProInternalServerError("HTTP-error-code: 500")
        with self.assertRaises(UKGProInternalServerError):
            make_stream(stream_name, client).check_access()


class TestCheckAccessWithRealClient(unittest.TestCase):
    """check_access through the real Client, so status-code mapping is exercised."""

    def setUp(self):
        self.client = Client(CONFIG)

    def _check(self, stream_name, response):
        with patch.object(self.client._session, "request", return_value=response) as req:
            return make_stream(stream_name, self.client).check_access(), req

    def test_http_403_marks_stream_inaccessible_without_retry(self):
        result, req = self._check(
            "roles", FakeResponse(403, {"message": "Authorization has been denied for this request."})
        )
        self.assertFalse(result)
        self.assertEqual(req.call_count, 1)

    def test_http_200_with_empty_list_is_accessible(self):
        result, _ = self._check("roles", FakeResponse(200, []))
        self.assertTrue(result)

    def test_http_400_on_required_param_stream_is_not_treated_as_403(self):
        with self.assertRaises(UKGProBadRequestError):
            self._check(
                "employee_deductions", FakeResponse(400, {"message": "dedCode is required"})
            )

    def test_http_400_on_regular_stream_raises(self):
        with self.assertRaises(UKGProBadRequestError):
            self._check("roles", FakeResponse(400, {"message": "bad"}))

    def test_http_401_raises(self):
        with self.assertRaises(UKGProUnauthorizedError):
            self._check("roles", FakeResponse(401, {}))

    def test_request_is_sent_to_stream_path_with_auth_and_probe_params(self):
        _, req = self._check("roles", FakeResponse(200, []))
        method, url = req.call_args.args
        kwargs = req.call_args.kwargs
        self.assertEqual(method, "GET")
        self.assertEqual(url, "https://servicet.example.com/configuration/v1/roles")
        self.assertEqual(kwargs["params"], {"per_page": 1, "page": 1})
        self.assertIn("Authorization", kwargs["headers"])
        self.assertEqual(kwargs["headers"]["US-Customer-Api-Key"], "dummy_api_key")

    def test_forbidden_error_message_has_no_credentials(self):
        with patch.object(
            self.client._session, "request", return_value=FakeResponse(403, {})
        ):
            with self.assertRaises(UKGProForbiddenError) as ctx:
                self.client.make_request("GET", "", {}, {}, path="/configuration/v1/roles")
        for secret in SECRETS:
            self.assertNotIn(secret, str(ctx.exception))


class TestApplyAccessChecks(unittest.TestCase):

    def test_forbidden_stream_excluded_and_others_kept(self):
        streams = [fake_stream("a"), fake_stream("b", accessible=False), fake_stream("c")]
        result = _apply_access_checks(streams)
        self.assertEqual([s.tap_stream_id for s in result], ["a", "c"])

    def test_all_accessible_kept_in_order(self):
        streams = [fake_stream("a"), fake_stream("b")]
        self.assertEqual(_apply_access_checks(streams), streams)

    def test_warning_names_every_excluded_stream(self):
        streams = [fake_stream("a"), fake_stream("b", False), fake_stream("c", False)]
        with patch("tap_ukg_pro_ultipro.discover.LOGGER") as mock_logger:
            _apply_access_checks(streams)
        mock_logger.warning.assert_called_once()
        message = mock_logger.warning.call_args.args[0] % mock_logger.warning.call_args.args[1:]
        self.assertTrue(message.endswith(": b, c"), message)

    def test_no_warning_when_all_accessible(self):
        with patch("tap_ukg_pro_ultipro.discover.LOGGER") as mock_logger:
            _apply_access_checks([fake_stream("a")])
        mock_logger.warning.assert_not_called()

    def test_all_forbidden_raises(self):
        streams = [fake_stream("a", False), fake_stream("b", False)]
        with self.assertRaises(UKGProForbiddenError) as ctx:
            _apply_access_checks(streams)
        self.assertIn("403", str(ctx.exception))

    def test_unexpected_error_is_not_swallowed_as_exclusion(self):
        streams = [fake_stream("a"), fake_stream("b", error=UKGProInternalServerError("boom"))]
        with self.assertRaises(UKGProInternalServerError):
            _apply_access_checks(streams)


class TestDiscover(unittest.TestCase):

    @staticmethod
    def _patch_access(forbidden=()):
        return patch.object(
            BaseStream,
            "check_access",
            autospec=True,
            side_effect=lambda self: self.tap_stream_id not in forbidden,
        )

    def test_catalog_unchanged_for_accessible_streams(self):
        schemas, field_metadata = get_schemas()
        with self._patch_access():
            catalog = discover(MagicMock())

        self.assertEqual([s.tap_stream_id for s in catalog.streams], list(schemas))
        for entry in catalog.streams:
            expected_mdata = field_metadata[entry.tap_stream_id]
            expected_keys = STREAMS[entry.tap_stream_id].key_properties
            self.assertEqual(entry.stream, entry.tap_stream_id)
            self.assertEqual(entry.metadata, expected_mdata)
            self.assertEqual(entry.key_properties, expected_keys)
            self.assertEqual(entry.schema.to_dict(), Schema.from_dict(schemas[entry.tap_stream_id]).to_dict())

    def test_forbidden_streams_excluded_without_touching_others(self):
        forbidden = {"roles", "earnings"}
        with self._patch_access(forbidden):
            catalog = discover(MagicMock())

        ids = {s.tap_stream_id for s in catalog.streams}
        self.assertFalse(ids & forbidden)
        self.assertEqual(ids, set(STREAMS) - forbidden)

    def test_retained_entries_identical_when_other_streams_are_excluded(self):
        with self._patch_access():
            full = {s.tap_stream_id: s.to_dict() for s in discover(MagicMock()).streams}
        with self._patch_access({"roles"}):
            partial = {s.tap_stream_id: s.to_dict() for s in discover(MagicMock()).streams}

        self.assertNotIn("roles", partial)
        for stream_id, entry in partial.items():
            self.assertEqual(entry, full[stream_id])

    def test_discovery_end_to_end_with_forbidden_endpoint(self):
        """Real streams and check_access; only the roles endpoint answers 403."""
        client = MagicMock()
        roles_path = STREAMS["roles"].path

        def make_request(method, endpoint, params=None, headers=None, **kwargs):
            if endpoint == roles_path:
                raise UKGProForbiddenError("HTTP-error-code: 403")
            return []

        client.build_url.side_effect = lambda path: path
        client.make_request.side_effect = make_request

        catalog = discover(client)
        ids = {s.tap_stream_id for s in catalog.streams}

        self.assertNotIn("roles", ids)
        self.assertEqual(ids, set(STREAMS) - {"roles"})

    def test_discovery_fails_when_every_stream_is_forbidden(self):
        with self._patch_access(set(STREAMS)):
            with self.assertRaises(UKGProForbiddenError):
                discover(MagicMock())

    def test_discovery_propagates_unexpected_errors(self):
        with patch.object(
            BaseStream, "check_access", side_effect=UKGProUnauthorizedError("HTTP-error-code: 401")
        ):
            with self.assertRaises(UKGProUnauthorizedError):
                discover(MagicMock())

    def test_do_discover_emits_filtered_catalog(self):
        client = MagicMock()
        entry = CatalogEntry(stream="roles", tap_stream_id="roles", schema=Schema(type="object"))
        with patch("tap_ukg_pro_ultipro.discover", return_value=Catalog([entry])) as mock_discover:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                do_discover(client)

        mock_discover.assert_called_once_with(client)
        emitted = json.loads(buffer.getvalue())
        self.assertEqual([s["tap_stream_id"] for s in emitted["streams"]], ["roles"])
