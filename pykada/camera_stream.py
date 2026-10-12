"""
Footage streaming client for pykada.

:class:`StreamingClient` builds HLS (``.m3u8``) playlist URLs for live and
historical camera footage. Pass the URL to any HLS-capable player (e.g.
hls.js, VLC); the player fetches the segments, whose URLs inside the playlist
already carry everything they need.
"""
from datetime import datetime
from typing import Optional, Union
from urllib.parse import urlencode

from typeguard import typechecked

from pykada.api_tokens import VerkadaTokenManager, get_default_streaming_token_manager
from pykada.endpoints import V2_STREAM_FOOTAGE_ENDPOINT, V2_STREAMING_TOKEN_ENDPOINT
from pykada.enums import STREAM_CODEC_ENUM, STREAM_RESOLUTION_ENUM
from pykada.helpers import require_choice, require_non_empty_str, to_iso8601
from pykada.verkada_client import BaseClient

Timestamp = Union[datetime, str]


class StreamingClient(BaseClient):
    """
    Client for interacting with Verkada Footage Streaming.
    This client provides methods to construct HLS playlist URLs for live
    and historical camera streams.

    The streaming endpoint does not accept the standard ``x-verkada-auth``
    session token used by every other client. It requires a short-lived
    JWT fetched separately from the "Get Streaming Token" endpoint
    (``GET /v2/cameras/footage/token``), passed as the ``jwt`` query
    parameter on the playlist URL. This client fetches and caches that
    JWT independently of ``self.request_manager``'s token.
    """
    def __init__(self,
                 api_key: Optional[str] = None,
                 token_manager: Optional[VerkadaTokenManager] = None):
        super().__init__(api_key, token_manager)

        # Build a dedicated token manager pointed at the streaming JWT
        # endpoint, using the same underlying API key as the regular
        # session token — the two token types are not interchangeable.
        if api_key:
            self._streaming_token_manager = VerkadaTokenManager(
                api_key=api_key,
                token_url=V2_STREAMING_TOKEN_ENDPOINT,
                response_json_key="jwt",
                token_lifetime_minutes=30,
            )
        elif token_manager:
            self._streaming_token_manager = VerkadaTokenManager(
                api_key=token_manager.api_key,
                token_url=V2_STREAMING_TOKEN_ENDPOINT,
                response_json_key="jwt",
                token_lifetime_minutes=30,
            )
        else:
            self._streaming_token_manager = get_default_streaming_token_manager()

    @typechecked
    def get_stream_playlist_url(
        self,
        org_id: str,
        camera_id: str,
        start_time: Optional[Timestamp] = None,
        end_time: Optional[Timestamp] = None,
        codec: str = "hevc",
        resolution: str = "low_res",
    ) -> str:
        """
        Construct the HLS .m3u8 playlist URL for live or historical streaming.

        Omit ``start_time`` and ``end_time`` for a live stream. For historical
        footage pass both; the range may span at most one hour and must be
        within the camera's retention.

        :param org_id: The organization ID.
        :param camera_id: The camera ID.
        :param start_time: Start of historical footage, as a timezone-aware
            ``datetime`` or ISO 8601 string. Requires ``end_time``.
        :param end_time: End of historical footage. Requires ``start_time``.
        :param codec: ``"hevc"`` (default) or ``"h264"``
            (see :data:`pykada.enums.STREAM_CODEC_ENUM`).
        :param resolution: ``"low_res"`` (default) or ``"high_res"``
            (see :data:`pykada.enums.STREAM_RESOLUTION_ENUM`). For historical
            footage ``"high_res"`` mixes in low resolution where high isn't available.
        :return: Fully qualified URL to the HLS playlist (.m3u8).
        :raises ValueError: If ``org_id`` or ``camera_id`` is empty, ``codec``
            or ``resolution`` is invalid, only one of ``start_time``/``end_time``
            is given, or a timestamp is invalid.
        """
        require_non_empty_str(org_id, "org_id")
        require_non_empty_str(camera_id, "camera_id")
        require_choice(codec, STREAM_CODEC_ENUM, "codec")
        require_choice(resolution, STREAM_RESOLUTION_ENUM, "resolution")
        if (start_time is None) != (end_time is None):
            raise ValueError(
                "start_time and end_time must be given together for historical "
                "footage, or both omitted for a live stream."
            )

        params = {
            "jwt": self._streaming_token_manager.get_token(),
            "org_id": org_id,
            "camera_id": camera_id,
            # The API uses 0 for both to mean "live"
            "start_time": to_iso8601(start_time, "start_time") or "0",
            "end_time": to_iso8601(end_time, "end_time") or "0",
            "codec": codec,
            "resolution": resolution,
            "type": "stream",
        }
        return f"{V2_STREAM_FOOTAGE_ENDPOINT}?{urlencode(params)}"
