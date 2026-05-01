Streaming
=========

.. automodule:: pykada.camera_stream
   :no-members:

.. note::

   The :class:`~pykada.camera_stream.StreamingClient` constructs HLS playlist
   URLs for live and historical camera streams.  It does **not** handle the
   HTTP stream itself — pass the returned URL to a media player (e.g. VLC,
   ffmpeg) or embed it in an ``<video>`` tag.  Requires a **Streaming API Key**,
   not a standard API key.

Client
------

.. autoclass:: pykada.camera_stream.StreamingClient
   :members:
   :show-inheritance:
