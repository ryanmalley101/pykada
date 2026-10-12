"""
Custom exceptions for pykada.

All exceptions carry ``status_code``, ``response_body``, and ``endpoint``
attributes so callers can inspect what went wrong without parsing message strings.

Errors from v2 endpoints also carry ``error_code`` (a stable, customer-facing
category such as ``"object_not_found"`` that is safe to branch on) and
``error_id`` (a short support code to quote when contacting Verkada).  Both
are ``None`` when the API did not return them.
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
        error_code: Optional[str] = None,
        error_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        self.endpoint = endpoint
        self.error_code = error_code
        self.error_id = error_id


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
        error_code: Optional[str] = None,
        error_id: Optional[str] = None,
        retry_after: Optional[int] = None,
    ):
        super().__init__(
            message,
            status_code=status_code,
            response_body=response_body,
            endpoint=endpoint,
            error_code=error_code,
            error_id=error_id,
        )
        self.retry_after = retry_after


class VerkadaServerError(VerkadaError):
    """
    Raised on 5xx responses or when all retries are exhausted on a server error.
    """


class VerkadaAPIError(VerkadaError):
    """
    Raised for any other HTTP error not covered by a more specific exception.
    Also the base class of the 400/409/422 errors below, so existing
    ``except VerkadaAPIError`` handlers keep catching them.
    """


class VerkadaBadRequestError(VerkadaAPIError):
    """
    Raised on 400 Bad Request.
    The request was malformed or failed parameter validation.
    """


class VerkadaConflictError(VerkadaAPIError):
    """
    Raised on 409 Conflict.
    The request collides with existing state, e.g. a duplicate name or ID.
    """


class VerkadaValidationError(VerkadaAPIError):
    """
    Raised on 422 Unprocessable Entity.
    The request was well-formed but violates a business rule, e.g.
    overlapping schedule windows.
    """
