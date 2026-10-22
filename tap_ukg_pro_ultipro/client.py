import base64
from typing import Any, Dict, Mapping, Optional, Tuple

import backoff
import requests
from requests import session
from requests.exceptions import Timeout, ConnectionError, ChunkedEncodingError
from singer import get_logger, metrics

from tap_ukg_pro_ultipro.exceptions import (
    ERROR_CODE_EXCEPTION_MAPPING,
    UKGProError,
    UKGProBackoffError
)

LOGGER = get_logger()
REQUEST_TIMEOUT = 300

# Config keys needed to authenticate and build request URLs.
AUTH_CONFIG_KEYS = ("username", "password", "api_key", "hostname")
API_KEY_HEADER = "US-Customer-Api-Key"


def validate_auth_config(config: Mapping[str, Any]) -> None:
    """
    Raise a descriptive error when a required auth setting is missing or blank.
    """
    invalid = [
        key for key in AUTH_CONFIG_KEYS
        if not isinstance(config.get(key), str) or not config.get(key).strip()
    ]
    if invalid:
        raise UKGProError(
            "Config is missing or has empty values for required keys: {}".format(", ".join(invalid))
        )


def normalize_hostname(hostname: str) -> str:
    """Return the HTTPS base URL for the tenant host supplied by the user.

    UKG Pro hosts differ per tenant/environment. The value may be given as a bare host
    (``servicet.ultipro.com``) or with an ``https://`` scheme; a trailing slash is ignored.
    Plain ``http://`` is rejected because credentials are sent with every request.
    """
    host = hostname.strip()
    if host.lower().startswith("http://"):
        raise UKGProError("'hostname' must use HTTPS; remove the 'http://' prefix.")
    if host.lower().startswith("https://"):
        host = host[len("https://"):]
    host = host.rstrip("/")
    if not host or any(char in host for char in (" ", "?", "#")):
        raise UKGProError(
            "'hostname' must be the tenant host, for example 'servicet.ultipro.com'."
        )
    return f"https://{host}"

def raise_for_error(response: requests.Response) -> None:
    """Raises the associated response exception. Takes in a response object,
    checks the status code, and throws the associated exception based on the
    status code.

    :param resp: requests.Response object
    """
    try:
        response_json = response.json()
    except Exception:
        response_json = {}
    if response.status_code not in [200, 201, 204]:
        if response_json.get("error"):
            message = f"HTTP-error-code: {response.status_code}, Error: {response_json.get('error')}"
        else:
            error_message = ERROR_CODE_EXCEPTION_MAPPING.get(
                response.status_code, {}
            ).get("message", "Unknown Error")
            message = f"HTTP-error-code: {response.status_code}, Error: {response_json.get('message', error_message)}"

        # For 5xx errors, use backoff exception if not specifically mapped
        if 500 <= response.status_code < 600:
            exc = ERROR_CODE_EXCEPTION_MAPPING.get(response.status_code, {}).get(
                "raise_exception", UKGProBackoffError
            )
        else:
            exc = ERROR_CODE_EXCEPTION_MAPPING.get(response.status_code, {}).get(
                "raise_exception", UKGProError
            )
        raise exc(message, response) from None

class Client:
    """
    A Wrapper class.
    ~~~
    Performs:
     - Authentication
     - Response parsing
     - HTTP Error handling and retry
    """

    def __init__(self, config: Mapping[str, Any]) -> None:
        validate_auth_config(config)
        self.config = config
        self._session = session()
        self.base_url = normalize_hostname(config["hostname"])
        config_request_timeout = config.get("request_timeout")
        self.request_timeout = float(config_request_timeout) if config_request_timeout else REQUEST_TIMEOUT

    def __enter__(self):
        self.check_api_credentials()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._session.close()

    def check_api_credentials(self) -> None:
        pass

    def build_url(self, path: str) -> str:
        """Build a request URL from the configured tenant host and an endpoint path."""
        return f"{self.base_url}/{path.lstrip('/')}"

    def authenticate(self, headers: Dict, params: Dict) -> Tuple[Dict, Dict]:
        """Adds HTTP Basic credentials and the customer API key to the request."""
        credentials = f"{self.config['username']}:{self.config['password']}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("ascii")

        headers['Authorization'] = f"Basic {encoded_credentials}"
        headers[API_KEY_HEADER] = self.config['api_key']

        return headers, params

    def make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        path: Optional[str] = None
    ) -> Any:
        """
        Sends an HTTP request to the specified API endpoint.
        """
        params = params or {}
        headers = dict(headers or {})
        body = body or {}
        endpoint = endpoint or self.build_url(path)
        headers, params = self.authenticate(headers, params)
        return self.__make_request(
            method, endpoint,
            headers=headers,
            params=params,
            data=body,
            timeout=self.request_timeout
        )

    @backoff.on_exception(
        wait_gen=backoff.expo,
        exception=(
            ConnectionResetError,
            ConnectionError,
            ChunkedEncodingError,
            Timeout,
            UKGProBackoffError
        ),
        max_tries=5,
        factor=2,
    )
    def __make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Optional[Mapping[Any, Any]]:
        """Performs HTTP Operations."""
        method = method.upper()
        with metrics.http_request_timer(endpoint):
            if method in ("GET", "POST"):
                if method == "GET":
                    kwargs.pop("data", None)
                response = self._session.request(method, endpoint, **kwargs)
                raise_for_error(response)
            else:
                raise ValueError(f"Unsupported method: {method}")

        return response.json()
