class UKGProError(Exception):
    """class representing Generic Http error."""

    def __init__(self, message=None, response=None):
        super().__init__(message)
        self.message = message
        self.response = response


class UKGProBackoffError(UKGProError):
    """class representing backoff error handling."""
    pass

class UKGProBadRequestError(UKGProError):
    """class representing 400 status code."""
    pass

class UKGProUnauthorizedError(UKGProError):
    """class representing 401 status code."""
    pass


class UKGProForbiddenError(UKGProError):
    """class representing 403 status code."""
    pass

class UKGProNotFoundError(UKGProError):
    """class representing 404 status code."""
    pass

class UKGProConflictError(UKGProError):
    """class representing 409 status code."""
    pass

class UKGProUnprocessableEntityError(UKGProError):
    """class representing 422 status code."""
    pass

class UKGProRateLimitError(UKGProBackoffError):
    """class representing 429 status code."""
    pass

class UKGProInternalServerError(UKGProBackoffError):
    """class representing 500 status code."""
    pass

class UKGProNotImplementedError(UKGProBackoffError):
    """class representing 501 status code."""
    pass

class UKGProBadGatewayError(UKGProBackoffError):
    """class representing 502 status code."""
    pass

class UKGProServiceUnavailableError(UKGProBackoffError):
    """class representing 503 status code."""
    pass

ERROR_CODE_EXCEPTION_MAPPING = {
    400: {
        "raise_exception": UKGProBadRequestError,
        "message": "A validation exception has occurred."
    },
    401: {
        "raise_exception": UKGProUnauthorizedError,
        "message": "The access token provided is expired, revoked, malformed or invalid for other reasons."
    },
    403: {
        "raise_exception": UKGProForbiddenError,
        "message": "You are missing the following required scopes: read"
    },
    404: {
        "raise_exception": UKGProNotFoundError,
        "message": "The resource you have specified cannot be found."
    },
    409: {
        "raise_exception": UKGProConflictError,
        "message": "The API request cannot be completed because the requested operation would conflict with an existing item."
    },
    422: {
        "raise_exception": UKGProUnprocessableEntityError,
        "message": "The request content itself is not processable by the server."
    },
    429: {
        "raise_exception": UKGProRateLimitError,
        "message": "The API rate limit for your organisation/application pairing has been exceeded."
    },
    500: {
        "raise_exception": UKGProInternalServerError,
        "message": "The server encountered an unexpected condition which prevented" \
            " it from fulfilling the request."
    },
    501: {
        "raise_exception": UKGProNotImplementedError,
        "message": "The server does not support the functionality required to fulfill the request."
    },
    502: {
        "raise_exception": UKGProBadGatewayError,
        "message": "Server received an invalid response."
    },
    503: {
        "raise_exception": UKGProServiceUnavailableError,
        "message": "API service is currently unavailable."
    }
}
