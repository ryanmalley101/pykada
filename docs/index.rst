pykada
======

A Python SDK for the `Verkada API <https://apidocs.verkada.com>`_ (v2).

pykada covers cameras, access control, a unified event feed, environmental sensors, classic alarms,
core command (users & audit logs), Helix video events, and workplace (guest &
mailroom) — with automatic token management, built-in retry/backoff, and
transparent pagination.

.. code-block:: bash

   pip install pykada

Quick start
-----------

**OOP style** (recommended for multiple calls — tokens and connections are reused):

.. code-block:: python

   from pykada import CamerasClient

   client = CamerasClient(api_key="YOUR_KEY")
   for camera in client.get_all_camera_data():
       print(camera["camera_id"], camera["name"])

**Functional style** (convenient for one-off scripts):

.. code-block:: python

   # Reads VERKADA_API_KEY from the environment or a .env file
   import pykada.cameras as cam

   for camera in cam.get_all_camera_data():
       print(camera["camera_id"])

Times are timezone-aware ``datetime`` objects or ISO 8601 strings, and every
paged endpoint has a ``get_X(limit=..., cursor=...)`` method for one page and a
``get_all_X()`` generator for all of them.

Upgrading from 1.x? See :doc:`migration`.

Error handling
--------------

All API errors are raised as typed exceptions so you can handle specific
failure modes without parsing message strings:

.. code-block:: python

   from pykada import CamerasClient
   from pykada import VerkadaAuthError, VerkadaRateLimitError, VerkadaNotFoundError
   import time

   client = CamerasClient(api_key="YOUR_KEY")

   try:
       settings = client.get_cloud_backup_settings("CAMERA_ID")
   except VerkadaAuthError:
       print("Invalid API key")
   except VerkadaRateLimitError as e:
       time.sleep(e.retry_after or 60)
   except VerkadaNotFoundError as e:
       # error_code is a stable category from the v2 API, e.g. "object_not_found"
       print(f"Not found ({e.error_code}): {e.endpoint}")

API Reference
-------------

.. toctree::
   :maxdepth: 1
   :caption: Guides

   migration

.. toctree::
   :maxdepth: 2
   :caption: Clients

   api/cameras
   api/access_control
   api/events
   api/sensors
   api/classic_alarms
   api/core_command
   api/helix
   api/workplace
   api/streaming

.. toctree::
   :maxdepth: 1
   :caption: Internals

   api/exceptions
   api/requests
   api/tokens
   api/helpers
