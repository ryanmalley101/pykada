from datetime import datetime, timezone
from unittest.mock import MagicMock
from urllib.parse import parse_qs, urlparse

import pytest
from typeguard import TypeCheckError

from pykada.api_tokens import VerkadaTokenManager
from pykada.camera_stream import StreamingClient
from pykada.endpoints import V2_STREAM_FOOTAGE_ENDPOINT, V2_STREAMING_TOKEN_ENDPOINT


def _client():
    client = StreamingClient(api_key="key")
    client._streaming_token_manager = MagicMock()
    client._streaming_token_manager.get_token.return_value = "jwt-token"
    return client


def _query(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}", {
        k: v[0] for k, v in parse_qs(parsed.query).items()}


def test_streaming_token_manager_uses_v2_endpoint():
    client = StreamingClient(api_key="key")
    assert client._streaming_token_manager._token_url == V2_STREAMING_TOKEN_ENDPOINT
    assert client._streaming_token_manager._response_json_key == "jwt"


def test_streaming_token_manager_from_token_manager():
    client = StreamingClient(token_manager=VerkadaTokenManager(api_key="key2"))
    assert client._streaming_token_manager.api_key == "key2"
    assert client._streaming_token_manager._token_url == V2_STREAMING_TOKEN_ENDPOINT


def test_live_playlist_url():
    base, query = _query(_client().get_stream_playlist_url("org1", "cam1"))
    assert base == V2_STREAM_FOOTAGE_ENDPOINT
    assert query == {
        "jwt": "jwt-token", "org_id": "org1", "camera_id": "cam1",
        "start_time": "0", "end_time": "0", "codec": "hevc",
        "resolution": "low_res", "type": "stream",
    }


def test_historical_playlist_url():
    url = _client().get_stream_playlist_url(
        "org1", "cam1",
        start_time=datetime(2025, 7, 17, 21, 0, tzinfo=timezone.utc),
        end_time="2025-07-17T21:30:00Z", codec="h264", resolution="high_res")
    _, query = _query(url)
    assert query["start_time"] == "2025-07-17T21:00:00Z"
    assert query["end_time"] == "2025-07-17T21:30:00Z"
    assert query["codec"] == "h264" and query["resolution"] == "high_res"


def test_historical_requires_both_times():
    with pytest.raises(ValueError, match="together"):
        _client().get_stream_playlist_url("org1", "cam1", start_time="2025-07-17T21:00:00Z")


@pytest.mark.parametrize("kwargs, match", [
    ({"codec": "vp9"}, "codec"),
    ({"resolution": "4k"}, "resolution"),
])
def test_invalid_choices(kwargs, match):
    with pytest.raises(ValueError, match=match):
        _client().get_stream_playlist_url("org1", "cam1", **kwargs)


@pytest.mark.parametrize("org_id, camera_id", [("", "cam1"), ("org1", " ")])
def test_empty_ids(org_id, camera_id):
    with pytest.raises(ValueError):
        _client().get_stream_playlist_url(org_id, camera_id)


def test_epoch_ints_rejected():
    with pytest.raises(TypeCheckError):
        _client().get_stream_playlist_url("org1", "cam1", start_time=1700000000,
                                          end_time=1700001000)
