import os

from dotenv import load_dotenv

from typeguard import typechecked
from typing import Optional
from urllib.parse import urlencode

from pykada.api_tokens import get_streaming_token
from pykada.endpoints import STREAM_FOOTAGE_ENDPOINT


@typechecked
def get_stream_playlist_url(
    camera_id: str,
    start_time: Optional[int] = 0,
    end_time: Optional[int] = 0,
    codec: str = "hevc",
    resolution: str = "low_res",
    type: str = "stream",
) -> str:
    """
    Construct the HLS .m3u8 playlist URL for live or historical streaming.

    :param region: Verkada region (e.g. "us", "eu").
    :param jwt: JSON Web Token obtained from the streaming token endpoint.
    :param org_id: The organization ID.
    :param camera_id: The camera ID.
    :param start_time: Epoch seconds; use 0 for live streaming (defaults to 0).
    :param end_time: Epoch seconds; use 0 for live streaming (defaults to 0).
    :param codec: Codec for the stream (defaults to "hevc").
    :param resolution: Stream resolution ("low_res" or "high_res"; defaults to "low_res").
    :param type: Reserved parameter, must be "stream" (defaults to "stream").
    :return: Fully‐qualified URL to the HLS playlist (.m3u8).
    :raises ValueError: If any required string parameter is empty.
    """
    load_dotenv(override=True)

    # Assemble query parameters
    params = {
        "jwt": get_streaming_token(),
        "org_id": os.getenv("VERKADA_ORG_ID"),
        "camera_id": camera_id,
        "start_time": start_time,
        "end_time": end_time,
        "codec": codec,
        "resolution": resolution,
        "type": type,
    }
    print(params)

    # URL‐encode and return
    return f"{STREAM_FOOTAGE_ENDPOINT}?{urlencode(params)}"
