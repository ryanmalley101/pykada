Exceptions
==========

.. automodule:: pykada.exceptions
   :no-members:

All pykada exceptions inherit from :class:`~pykada.exceptions.VerkadaError` so
you can catch any API error with a single ``except VerkadaError`` clause, or
handle specific cases precisely:

.. code-block:: python

   from pykada import (
       VerkadaAuthError,
       VerkadaNotFoundError,
       VerkadaRateLimitError,
       VerkadaServerError,
       VerkadaValidationError,
   )

Every exception exposes:

* ``status_code`` — the HTTP status code (``int | None``)
* ``response_body`` — raw response text (``str | None``)
* ``endpoint`` — the URL that was called (``str | None``)
* ``error_code`` — the stable error category from a v2 error response, such as
  ``"object_not_found"``; safe to branch on (``str | None``)
* ``error_id`` — a short support code to quote when contacting Verkada (``str | None``)

:class:`~pykada.exceptions.VerkadaRateLimitError` additionally exposes:

* ``retry_after`` — seconds to wait before retrying, parsed from the
  ``Retry-After`` header (``int | None``)

Exception hierarchy
-------------------

.. code-block:: text

   VerkadaError (base)
   ├── VerkadaAuthError            (401 Unauthorized)
   ├── VerkadaForbiddenError       (403 Forbidden)
   ├── VerkadaNotFoundError        (404 Not Found)
   ├── VerkadaRateLimitError       (429 Too Many Requests)
   ├── VerkadaServerError          (5xx Server Error)
   └── VerkadaAPIError             (other HTTP errors)
       ├── VerkadaBadRequestError  (400 Bad Request)
       ├── VerkadaConflictError    (409 Conflict)
       └── VerkadaValidationError  (422 Unprocessable Entity)

.. autoclass:: pykada.exceptions.VerkadaError
   :members:
   :show-inheritance:

.. autoclass:: pykada.exceptions.VerkadaAuthError
   :show-inheritance:

.. autoclass:: pykada.exceptions.VerkadaForbiddenError
   :show-inheritance:

.. autoclass:: pykada.exceptions.VerkadaNotFoundError
   :show-inheritance:

.. autoclass:: pykada.exceptions.VerkadaRateLimitError
   :members:
   :show-inheritance:

.. autoclass:: pykada.exceptions.VerkadaServerError
   :show-inheritance:

.. autoclass:: pykada.exceptions.VerkadaAPIError
   :show-inheritance:

.. autoclass:: pykada.exceptions.VerkadaBadRequestError
   :show-inheritance:

.. autoclass:: pykada.exceptions.VerkadaConflictError
   :show-inheritance:

.. autoclass:: pykada.exceptions.VerkadaValidationError
   :show-inheritance:
