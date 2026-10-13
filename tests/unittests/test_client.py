import base64
import unittest
import requests
from unittest.mock import patch
from parameterized import parameterized
from requests.exceptions import Timeout, ConnectionError, ChunkedEncodingError
from tap_ukg_pro_ultipro import REQUIRED_CONFIG_KEYS
from tap_ukg_pro_ultipro.client import Client, normalize_hostname
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
    "hostname": "servicet.example.com",
    "start_date": "2022-01-01T00:00:00Z",
    "request_timeout": 30,
}

DEFAULT_REQUEST_TIMEOUT = 300


class MockResponse:
    """Mocked standard HTTPResponse to test error handling."""

    def __init__(
        self, status_code, resp = "", content=[""], headers=None, raise_error=True, text={}
    ):
        self.json_data = resp
        self.status_code = status_code
        self.content = content
        self.headers = headers
        self.raise_error = raise_error
        self.text = text
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
        return self.text

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
        ["bare host", "servicet.example.com", "https://servicet.example.com"],
        ["https scheme", "https://servicet.example.com", "https://servicet.example.com"],
        ["trailing slash", "https://servicet.example.com/", "https://servicet.example.com"],
        ["surrounding spaces", "  servicet.example.com  ", "https://servicet.example.com"],
        ["host with path", "servicet.example.com/services/", "https://servicet.example.com/services"],
    ])
    def test_normalize_hostname(self, test_name, value, expected):
        self.assertEqual(normalize_hostname(value), expected)

    @parameterized.expand([
        ["plain http", "http://servicet.example.com"],
        ["only scheme", "https://"],
        ["inner space", "service t.example.com"],
        ["query string", "servicet.example.com?x=1"],
    ])
    def test_normalize_hostname_rejects_invalid(self, test_name, value):
        with self.assertRaises(UKGProError):
            normalize_hostname(value)

    def test_build_url_uses_tenant_host_and_path(self):
        self.assertEqual(
            self.client.build_url("/personnel/v1/compensation-details"),
            "https://servicet.example.com/personnel/v1/compensation-details",
        )
        # no double slashes and the trailing slash of the documented path is preserved
        self.assertEqual(
            self.client.build_url("/configuration/v1/locations/"),
            "https://servicet.example.com/configuration/v1/locations/",
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
        self.assertEqual(args, ("GET", "https://servicet.example.com/roles"))
        self.assertIn("Authorization", kwargs["headers"])
        self.assertEqual(shared_headers, {})

    @patch("tap_ukg_pro_ultipro.client.LOGGER")
    @patch("tap_ukg_pro_ultipro.client.Client._Client__make_request")
    def test_request_logging_does_not_leak_secrets(self, mock_make_request, mock_logger):
        mock_make_request.return_value = []
        self.client.make_request("GET", "", params={"page": 1}, path="/roles")
        logged = " ".join(str(a) for call in mock_logger.mock_calls for a in call.args)
        encoded = base64.b64encode(b"dummy_user:dummy_password").decode()
        for secret in ("dummy_password", "dummy_api_key", encoded):
            self.assertNotIn(secret, logged)

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
                self.client._Client__make_request("GET", "https://api.example.com/resource")

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
                self.client._Client__make_request("GET", "https://api.example.com/resource")

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
                self.client._Client__make_request("GET", "https://api.example.com/resource")

            self.assertEqual(mock_request.call_count, 5)
