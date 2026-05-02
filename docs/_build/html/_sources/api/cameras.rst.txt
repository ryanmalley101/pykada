Cameras
=======

.. automodule:: pykada.cameras
   :no-members:

Client
------

.. autoclass:: pykada.cameras.CamerasClient
   :members:
   :inherited-members:
   :show-inheritance:

Functional wrappers
-------------------

The functions below share a single lazily-initialized :class:`~pykada.cameras.CamerasClient`
so token caching is preserved across calls.

.. automodule:: pykada.cameras
   :members:
   :no-index:
   :exclude-members: CamerasClient
