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
   )

Every exception exposes:

* ``status_code`` — the HTTP status code (``int | None``)
* ``response_body`` — raw response text (``str | None``)
* ``endpoint`` — the URL that was called (``str | None``)

:class:`~pykada.exceptions.VerkadaRateLimitError` additionally exposes:

* ``retry_after`` — seconds to wait before retrying, parsed from the
  ``Retry-After`` header (``int | None``)

Exception hierarchy
-------------------

.. code-block:: text

   VerkadaError (base)
   ├── VerkadaAuthError       (401 Unauthorized)
   ├── VerkadaForbiddenError  (403 Forbidden)
   ├── VerkadaNotFoundError   (404 Not Found)
   ├── VerkadaRateLimitError  (429 Too Many Requests)
   ├── VerkadaServerError     (5xx Server Error)
   └── VerkadaAPIError        (other HTTP errors)

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
