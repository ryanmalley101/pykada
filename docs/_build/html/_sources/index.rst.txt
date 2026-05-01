pykada
======

A Python SDK for the `Verkada API <https://apidocs.verkada.com>`_.

pykada covers cameras, access control, environmental sensors, classic alarms,
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

   import os, pykada.cameras as cam

   os.environ["VERKADA_API_KEY"] = "YOUR_KEY"
   for camera in cam.get_all_camera_data():
       print(camera["camera_id"])

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
       data = client.get_camera_data()
   except VerkadaAuthError:
       print("Invalid API key")
   except VerkadaRateLimitError as e:
       time.sleep(e.retry_after or 60)
   except VerkadaNotFoundError as e:
       print(f"Not found: {e.endpoint}")

API Reference
-------------

.. toctree::
   :maxdepth: 2
   :caption: Clients

   api/cameras
   api/access_control
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
