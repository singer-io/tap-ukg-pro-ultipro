import base64
import re
from typing import Any, Dict, Mapping, Optional, Tuple
from urllib.parse import urlsplit

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
MAX_ERROR_MESSAGE_LENGTH = 500

# Config keys needed to authenticate and build request URLs.
AUTH_CONFIG_KEYS = ("username", "password", "api_key", "hostname")
API_KEY_HEADER = "US-Customer-Api-Key"

# Credentials are only ever sent to UKG-owned domains. A configured hostname must be a
# subdomain of one of these suffixes (for example ``servicet.ultipro.com``).
ALLOWED_HOST_SUFFIXES = ("ultipro.com", "ultipro.ca", "ukg.com")
HOST_LABEL_RE = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")


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


def is_allowed_host(host: str) -> bool:
    """True when ``host`` is a plain DNS name under an approved UKG domain.

    Rejects IP addresses, ports, userinfo, paths, queries and any other character that
    could change the destination of a request.
    """
    host = host.lower()
    if not all(HOST_LABEL_RE.fullmatch(label) for label in host.split(".")):
        return False
    return any(host.endswith("." + suffix) for suffix in ALLOWED_HOST_SUFFIXES)


def normalize_hostname(hostname: str) -> str:
    """Return the HTTPS base URL for the tenant host supplied by the user.

    The value may be given as a bare host (``servicet.ultipro.com``) or with an ``https://``
    scheme; a trailing slash is ignored. Plain ``http://`` is rejected because credentials
    are sent with every request, and only hosts under the approved UKG domains
    (``ALLOWED_HOST_SUFFIXES``) are accepted.
    """
    host = hostname.strip()
    if host.lower().startswith("http://"):
        raise UKGProError("'hostname' must use HTTPS; remove the 'http://' prefix.")
    if host.lower().startswith("https://"):
        host = host[len("https://"):]
    host = host.rstrip("/")
    if not host or not is_allowed_host(host):
        raise UKGProError(
            "'hostname' must be a UKG tenant host (a subdomain of {}), for example "
            "'servicet.ultipro.com'.".format(", ".join(ALLOWED_HOST_SUFFIXES))
        )
    return f"https://{host.lower()}"

def _bounded(value: Any) -> str:
    return str(value)[:MAX_ERROR_MESSAGE_LENGTH]


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
    if not isinstance(response_json, dict):
        response_json = {}
    if response.status_code not in [200, 201, 204]:
        LOGGER.error(
            "API request failed with HTTP-error-code: %s", response.status_code
        )
        if response_json.get("error"):
            message = f"HTTP-error-code: {response.status_code}, Error: {_bounded(response_json.get('error'))}"
        else:
            error_message = ERROR_CODE_EXCEPTION_MAPPING.get(
                response.status_code, {}
            ).get("message", "Unknown Error")
            api_message = response_json.get("message", error_message)
            message = f"HTTP-error-code: {response.status_code}, Error: {_bounded(api_message)}"
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

    def validate_destination(self, url: str) -> None:
        """Ensure ``url`` points at the configured tenant origin before credentials are sent."""
        parsed = urlsplit(url)
        expected = urlsplit(self.base_url)
        # netloc comparison also rules out userinfo and non-default ports
        if parsed.scheme.lower() != "https" or parsed.netloc.lower() != expected.netloc:
            raise UKGProError(
                "Refusing to send credentials to a destination other than the configured tenant host."
            )

    def authenticate(self, headers: Dict, params: Dict) -> Tuple[Dict, Dict]:
        """Adds HTTP Basic credentials and the customer API key to the request."""
        credentials = f"{self.config['username']}:{self.config['password']}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
        headers['Accept'] = 'application/json'
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
        self.validate_destination(endpoint)
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
        self.validate_destination(endpoint)
        with metrics.http_request_timer(endpoint):
            if method in ("GET", "POST"):
                if method == "GET":
                    kwargs.pop("data", None)
                # Never follow redirects: they could forward credentials to another origin.
                kwargs["allow_redirects"] = False
                response = self._session.request(method, endpoint, **kwargs)
                if 300 <= response.status_code < 400:
                    raise UKGProError(
                        f"HTTP-error-code: {response.status_code}, Error: "
                        "Redirect responses are not followed."
                    )
                raise_for_error(response)
            else:
                raise ValueError(f"Unsupported method: {method}")

        if response.status_code == 204:
            return None
        return response.json()
