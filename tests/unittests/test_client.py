import base64
import unittest
import requests
from unittest.mock import patch, MagicMock
from parameterized import parameterized
from requests.exceptions import Timeout, ConnectionError, ChunkedEncodingError
from tap_ukg_pro_ultipro import REQUIRED_CONFIG_KEYS
from tap_ukg_pro_ultipro.client import Client, normalize_hostname, raise_for_error
from tap_ukg_pro_ultipro.exceptions import (
    UKGProError,
    UKGProBadRequestError,
    UKGProUnauthorizedError,
    UKGProForbiddenError,
    UKGProNotFoundError,
    UKGProConflictError,
    UKGProUnprocessableEntityError,
    UKGProRateLimitError,
    UKGProInternalServerError,
    UKGProNotImplementedError,
    UKGProBadGatewayError,
    UKGProServiceUnavailableError,
)


default_config = {
    "username": "dummy_user",
    "password": "dummy_password",
    "api_key": "dummy_api_key",
    "hostname": "servicet.ultipro.com",
    "start_date": "2022-01-01T00:00:00Z",
    "request_timeout": 30,
}

DEFAULT_REQUEST_TIMEOUT = 300


class MockResponse:
    """Mocked standard HTTPResponse to test error handling."""

    def __init__(
        self, status_code, resp=None, content=None, headers=None, raise_error=True, text=None
    ):
        self.json_data = {} if resp is None else resp
        self.status_code = status_code
        self.content = [""] if content is None else content
        self.headers = {} if headers is None else headers
        self.raise_error = raise_error
        self.text = "" if text is None else text
        self.reason = "error"

    def raise_for_status(self):
        """If an error occur, this method returns a HTTPError object.

        Raises:
            requests.HTTPError: Mock http error.

        Returns:
            int: Returns status code if not error occurred.
        """
        if not self.raise_error:
            return self.status_code

        raise requests.HTTPError("mock sample message")

    def json(self):
        """Returns a JSON object of the result."""
        return self.json_data

class TestClient(unittest.TestCase):

    def setUp(self):
        """Set up the client with default configuration."""
        self.client = Client(default_config)

    @parameterized.expand([
        ["empty value", "", DEFAULT_REQUEST_TIMEOUT],
        ["string value", "12", 12.0],
        ["integer value", 10, 10.0],
        ["float value", 20.0, 20.0],
        ["zero value", 0, DEFAULT_REQUEST_TIMEOUT]
    ])
    @patch("tap_ukg_pro_ultipro.client.session")
    def test_client_initialization(self, test_name, input_value, expected_value, mock_session):
        config = dict(default_config, request_timeout=input_value)
        client = Client(config)
        assert client.request_timeout == expected_value
        assert isinstance(client._session, mock_session().__class__)

    def test_required_config_keys(self):
        self.assertEqual(
            REQUIRED_CONFIG_KEYS, ["username", "password", "api_key", "hostname", "start_date"]
        )

    @parameterized.expand([
        ["username"], ["password"], ["api_key"], ["hostname"],
    ])
    def test_missing_or_blank_auth_config_raises(self, key):
        missing = {k: v for k, v in default_config.items() if k != key}
        blank = dict(default_config, **{key: "  "})
        for config in (missing, blank):
            with self.assertRaises(UKGProError) as ctx:
                Client(config)
            self.assertIn(key, str(ctx.exception))
            # only key names may appear in the message, never secret values
            for secret in ("dummy_password", "dummy_api_key"):
                self.assertNotIn(secret, str(ctx.exception))

    @parameterized.expand([
        ["bare host", "servicet.ultipro.com", "https://servicet.ultipro.com"],
        ["https scheme", "https://servicet.ultipro.com", "https://servicet.ultipro.com"],
        ["trailing slash", "https://servicet.ultipro.com/", "https://servicet.ultipro.com"],
        ["surrounding spaces", "  servicet.ultipro.com  ", "https://servicet.ultipro.com"],
        ["mixed case", "ServiceT.UltiPro.com", "https://servicet.ultipro.com"],
        ["ultipro.ca", "service.ultipro.ca", "https://service.ultipro.ca"],
        ["ukg.com", "tenant.ukg.com", "https://tenant.ukg.com"],
    ])
    def test_normalize_hostname(self, test_name, value, expected):
        self.assertEqual(normalize_hostname(value), expected)

    @parameterized.expand([
        ["plain http", "http://servicet.ultipro.com"],
        ["only scheme", "https://"],
        ["inner space", "service t.ultipro.com"],
        ["query string", "servicet.ultipro.com?x=1"],
        ["host with path", "servicet.ultipro.com/services/"],
        ["metadata ip", "169.254.169.254"],
        ["loopback", "localhost"],
        ["loopback ip with port", "127.0.0.1:8443"],
        ["unapproved domain", "servicet.example.com"],
        ["suffix lookalike", "servicet.evilultipro.com"],
        ["approved domain as subdomain of attacker", "servicet.ultipro.com.evil.com"],
        ["approved domain in path", "evil.com/servicet.ultipro.com"],
        ["userinfo", "servicet.ultipro.com@evil.com"],
        ["userinfo prefix", "evil.com@servicet.ultipro.com"],
        ["port", "servicet.ultipro.com:8443"],
        ["backslash", "evil.com\\@servicet.ultipro.com"],
        ["bare approved domain", "ultipro.com"],
    ])
    def test_normalize_hostname_rejects_invalid(self, test_name, value):
        with self.assertRaises(UKGProError):
            normalize_hostname(value)

    @parameterized.expand([["169.254.169.254"], ["attacker.example.net"]])
    def test_client_rejects_untrusted_hostname_without_sending_anything(self, hostname):
        with patch("requests.Session.request") as mock_request:
            with self.assertRaises(UKGProError):
                Client(dict(default_config, hostname=hostname))
        mock_request.assert_not_called()

    def test_build_url_uses_tenant_host_and_path(self):
        self.assertEqual(
            self.client.build_url("/personnel/v1/compensation-details"),
            "https://servicet.ultipro.com/personnel/v1/compensation-details",
        )
        # no double slashes and the trailing slash of the documented path is preserved
        self.assertEqual(
            self.client.build_url("/configuration/v1/locations/"),
            "https://servicet.ultipro.com/configuration/v1/locations/",
        )
        self.assertNotIn("developer.ukg.com", self.client.base_url)

    def test_authenticate_sets_basic_auth_and_api_key_headers(self):
        headers, params = self.client.authenticate({}, {"page": 1})
        expected = base64.b64encode(b"dummy_user:dummy_password").decode()
        self.assertEqual(headers["Authorization"], f"Basic {expected}")
        self.assertEqual(headers["US-Customer-Api-Key"], "dummy_api_key")
        self.assertEqual(params, {"page": 1})

    @patch("tap_ukg_pro_ultipro.client.Client._Client__make_request")
    def test_make_request_builds_url_and_does_not_mutate_shared_headers(self, mock_make_request):
        mock_make_request.return_value = []
        shared_headers = {}
        self.client.make_request("GET", "", params={}, headers=shared_headers, path="/roles")
        args, kwargs = mock_make_request.call_args
        self.assertEqual(args, ("GET", "https://servicet.ultipro.com/roles"))
        self.assertIn("Authorization", kwargs["headers"])
        self.assertEqual(shared_headers, {})

    @parameterized.expand([
        ["other host", "https://attacker.example.net/resource"],
        ["metadata ip", "https://169.254.169.254/latest/meta-data"],
        ["plain http", "http://servicet.ultipro.com/resource"],
        ["other port", "https://servicet.ultipro.com:8443/resource"],
        ["userinfo", "https://servicet.ultipro.com@attacker.example.net/resource"],
        ["suffix lookalike", "https://servicet.ultipro.com.attacker.example.net/resource"],
        ["other approved tenant", "https://service4.ultipro.com/resource"],
    ])
    def test_make_request_rejects_untrusted_destination_without_sending_credentials(self, test_name, url):
        with patch.object(self.client._session, "request") as mock_request:
            with self.assertRaises(UKGProError):
                self.client.make_request("GET", url)
            with self.assertRaises(UKGProError):
                self.client._Client__make_request("GET", url, headers={"Authorization": "secret"})
        mock_request.assert_not_called()

    def test_make_request_disables_redirects(self):
        response = MockResponse(200, resp=[])
        with patch.object(self.client._session, "request", return_value=response) as mock_request:
            self.client.make_request("GET", "", path="/roles")
        self.assertIs(mock_request.call_args.kwargs["allow_redirects"], False)

    @parameterized.expand([[301], [302], [303], [307], [308]])
    def test_redirect_response_is_not_followed(self, status_code):
        redirect = MockResponse(
            status_code, headers={"Location": "https://attacker.example.net/"}
        )
        with patch.object(self.client._session, "request", return_value=redirect) as mock_request:
            with self.assertRaises(UKGProError) as ctx:
                self.client.make_request("GET", "", path="/roles")
        # a single request was made; the Location target was never contacted
        self.assertEqual(mock_request.call_count, 1)
        self.assertNotIn("attacker", str(ctx.exception))
        for secret in self._secrets():
            self.assertNotIn(secret, str(ctx.exception))

    @staticmethod
    def _secrets():
        encoded = base64.b64encode(b"dummy_user:dummy_password").decode()
        return ("dummy_user", "dummy_password", "dummy_api_key", encoded)

    def test_credentials_only_sent_to_configured_origin(self):
        response = MockResponse(200, resp=[])
        with patch.object(self.client._session, "request", return_value=response) as mock_request:
            self.client.make_request("GET", "", path="/roles")
        mock_request.assert_called_once()
        method, url = mock_request.call_args.args
        self.assertEqual(url, "https://servicet.ultipro.com/roles")
        headers = mock_request.call_args.kwargs["headers"]
        expected = base64.b64encode(b"dummy_user:dummy_password").decode()
        self.assertEqual(headers["Authorization"], f"Basic {expected}")
        self.assertEqual(headers["US-Customer-Api-Key"], "dummy_api_key")

    @patch("tap_ukg_pro_ultipro.client.LOGGER")
    def test_error_logging_does_not_leak_response_body_or_secrets(self, mock_logger):
        body = {
            "message": "bad request",
            "ssn": "123-45-6789",
            "token": "dummy-bearer-token",
            "employee": "Jane Sensitive",
        }
        response = MockResponse(400, resp=body, text=str(body))
        with patch.object(self.client._session, "request", return_value=response):
            with self.assertRaises(UKGProBadRequestError):
                self.client.make_request("GET", "", params={"page": 1}, path="/roles")

        mock_logger.error.assert_called_once()
        logged = " ".join(
            str(a) for call in mock_logger.mock_calls for a in call.args
        )
        self.assertIn("400", logged)
        for secret in (
            "123-45-6789", "dummy-bearer-token", "Jane Sensitive", "servicet.ultipro.com",
            *self._secrets(),
        ):
            self.assertNotIn(secret, logged)

    @parameterized.expand([
        ["list", [{"message": "x"}]],
        ["null", None],
        ["string", "oops"],
        ["number", 42],
    ])
    def test_non_dict_error_json_is_tolerated(self, test_name, payload):
        response = MagicMock(status_code=400)
        response.json.return_value = payload
        with self.assertRaises(UKGProBadRequestError) as ctx:
            raise_for_error(response)
        self.assertIn("A validation exception has occurred.", str(ctx.exception))

    def test_invalid_json_error_body_is_tolerated(self):
        response = MagicMock(status_code=404)
        response.json.side_effect = ValueError("not json")
        with self.assertRaises(UKGProNotFoundError):
            raise_for_error(response)

    def test_mock_response_returns_json_data_and_has_no_shared_state(self):
        self.assertEqual(MockResponse(400, resp={"message": "m"}).json(), {"message": "m"})
        first, second = MockResponse(200), MockResponse(200)
        first.headers["x"] = "y"
        first.content.append("z")
        self.assertEqual(second.headers, {})
        self.assertEqual(second.content, [""])

    def test_api_error_message_is_used_and_bounded(self):
        response = MockResponse(400, resp={"message": "m" * 5000})
        with self.assertRaises(UKGProBadRequestError) as ctx:
            raise_for_error(response)
        self.assertLess(len(str(ctx.exception)), 600)

    @parameterized.expand([
        ["400 error", 400, MockResponse(400), UKGProBadRequestError, "A validation exception has occurred."],
        ["401 error", 401, MockResponse(401), UKGProUnauthorizedError, "The access token provided is expired, revoked, malformed or invalid for other reasons."],
        ["403 error", 403, MockResponse(403), UKGProForbiddenError, "You are missing the following required scopes: read"],
        ["404 error", 404, MockResponse(404), UKGProNotFoundError, "The resource you have specified cannot be found."],
        ["409 error", 409, MockResponse(409), UKGProConflictError, "The API request cannot be completed because the requested operation would conflict with an existing item."],
        ["422 error", 422, MockResponse(422), UKGProUnprocessableEntityError, "The request content itself is not processable by the server."],
    ])
    def test_make_request_http_failure_without_retry(self, test_name, error_code, mock_response, error, error_message):

        with patch.object(self.client._session, "request", return_value=mock_response):
            with self.assertRaises(error) as e:
                self.client._Client__make_request("GET", self.client.build_url("/resource"))
        expected_error_message = (f"HTTP-error-code: {error_code}, Error: {error_message}")
        self.assertEqual(str(e.exception), expected_error_message)

    @parameterized.expand([
        ["429 error", 429, MockResponse(429), UKGProRateLimitError, "The API rate limit for your organisation/application pairing has been exceeded."],
        ["500 error", 500, MockResponse(500), UKGProInternalServerError, "The server encountered an unexpected condition which prevented it from fulfilling the request."],
        ["501 error", 501, MockResponse(501), UKGProNotImplementedError, "The server does not support the functionality required to fulfill the request."],
        ["502 error", 502, MockResponse(502), UKGProBadGatewayError, "Server received an invalid response."],
        ["503 error", 503, MockResponse(503), UKGProServiceUnavailableError, "API service is currently unavailable."],
    ])
    @patch("time.sleep")
    def test_make_request_http_failure_with_retry(self, test_name, error_code, mock_response, error, error_message, mock_sleep):

        with patch.object(self.client._session, "request", return_value=mock_response) as mock_request:
            with self.assertRaises(error) as e:
                self.client._Client__make_request("GET", self.client.build_url("/resource"))

            expected_error_message = (f"HTTP-error-code: {error_code}, Error: {error_message}")
            self.assertEqual(str(e.exception), expected_error_message)
            self.assertEqual(mock_request.call_count, 5)

    @parameterized.expand([
        ["ConnectionResetError", ConnectionResetError],
        ["ConnectionError", ConnectionError],
        ["ChunkedEncodingError", ChunkedEncodingError],
        ["Timeout", Timeout],
    ])
    @patch("time.sleep")
    def test_make_request_other_failure_with_retry(self, test_name, error, mock_sleep):

        with patch.object(self.client._session, "request", side_effect=error) as mock_request:
            with self.assertRaises(error) as e:
                self.client._Client__make_request("GET", self.client.build_url("/resource"))

            self.assertEqual(mock_request.call_count, 5)
