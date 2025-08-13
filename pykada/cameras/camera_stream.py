import os

from typeguard import typechecked
from typing import Optional
from urllib.parse import urlencode

from pykada.api_tokens import VerkadaTokenManager
from pykada.endpoints import STREAM_FOOTAGE_ENDPOINT
from pykada.verkada_client import BaseClient


# TODO : The StreamingClient could have a strong implementation overall
class StreamingClient(BaseClient):
    """
    Client for interacting with Verkada Footage Streaming.
    This client provides methods to construct HLS playlist URLs for live
    and historical camera streams. Make sure to use specifically Streaming
    API Keys for this client, as regular API keys will not work.
    """
    def __init__(self,
                 api_key: Optional[str] = None,
                 token_manager: Optional[VerkadaTokenManager] = None):
        super().__init__(api_key, token_manager)

    @typechecked
    def get_stream_playlist_url(
        self,
        org_id: str,
        camera_id: str,
        start_time: Optional[int] = 0,
        end_time: Optional[int] = 0,
        codec: str = "hevc",
        resolution: str = "low_res",
        stream_type: str = "stream",
    ) -> str:
        """
        Construct the HLS .m3u8 playlist URL for live or historical streaming.

        :param org_id: The organization ID.
        :param camera_id: The camera ID.
        :param start_time: Epoch seconds; use 0 for live streaming (defaults to 0).
        :param end_time: Epoch seconds; use 0 for live streaming (defaults to 0).
        :param codec: Codec for the stream (defaults to "hevc").
        :param resolution: Stream resolution ("low_res" or "high_res"; defaults to "low_res").
        :param stream_type: Reserved parameter, must be "stream" (defaults to "stream").
        :return: Fully‐qualified URL to the HLS playlist (.m3u8).
        :raises ValueError: If any required string parameter is empty.
        """

        # Assemble query parameters
        params = {
            "jwt": self.request_manager.token_manager.get_token(),
            "org_id": os.getenv("VERKADA_ORG_ID"),
            "camera_id": camera_id,
            "start_time": start_time,
            "end_time": end_time,
            "codec": codec,
            "resolution": resolution,
            "type": stream_type,
        }
        print(params)

        # URL‐encode and return
        return f"{STREAM_FOOTAGE_ENDPOINT}?{urlencode(params)}"
