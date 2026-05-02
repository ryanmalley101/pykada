"""
Custom exceptions for pykada.

All exceptions carry ``status_code``, ``response_body``, and ``endpoint``
attributes so callers can inspect what went wrong without parsing message strings.
"""
from typing import Optional


class VerkadaError(Exception):
    """Base exception for all pykada errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        endpoint: Optional[str] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        self.endpoint = endpoint


class VerkadaAuthError(VerkadaError):
    """
    Raised on 401 Unauthorized.
    Usually means the API key is missing, expired, or invalid.
    """


class VerkadaForbiddenError(VerkadaError):
    """
    Raised on 403 Forbidden.
    The API key is valid but lacks permission for this resource.
    """


class VerkadaNotFoundError(VerkadaError):
    """
    Raised on 404 Not Found.
    The requested resource (camera, user, door, etc.) does not exist.
    """


class VerkadaRateLimitError(VerkadaError):
    """
    Raised on 429 Too Many Requests (after all retries are exhausted).
    Check ``retry_after`` for the number of seconds to wait before retrying.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = 429,
        response_body: Optional[str] = None,
        endpoint: Optional[str] = None,
        retry_after: Optional[int] = None,
    ):
        super().__init__(
            message,
            status_code=status_code,
            response_body=response_body,
            endpoint=endpoint,
        )
        self.retry_after = retry_after


class VerkadaServerError(VerkadaError):
    """
    Raised on 5xx responses or when all retries are exhausted on a server error.
    """


class VerkadaAPIError(VerkadaError):
    """
    Raised for any other HTTP error not covered by a more specific exception.
    """
