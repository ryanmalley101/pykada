import pytest
from unittest.mock import MagicMock, patch
import requests as requests_lib

from pykada.verkada_requests import VerkadaRequestManager, _raise_for_status
from pykada.exceptions import (
    VerkadaAuthError,
    VerkadaForbiddenError,
    VerkadaNotFoundError,
    VerkadaRateLimitError,
    VerkadaServerError,
    VerkadaAPIError,
    VerkadaError,
)


# ---------- helpers ----------

def _fake_response(status_code: int, body: str = "", headers: dict = None):
    resp = MagicMock(spec=requests_lib.Response)
    resp.status_code = status_code
    resp.text = body
    resp.headers = headers or {}
    return resp


def _rm():
    mock_tm = MagicMock()
    mock_tm.get_token.return_value = "test-token"
    return VerkadaRequestManager(token_manager=mock_tm)


def _mock_session(json_return=None, content_return=b"", status_ok=True, status_code=200):
    mock_resp = MagicMock()
    mock_resp.ok = status_ok
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_return if json_return is not None else {}
    mock_resp.content = content_return
    mock_resp.text = ""
    mock_resp.headers = {}
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_session.request.return_value = mock_resp
    return mock_session, mock_resp


# ---------- _raise_for_status ----------

def test_raise_401_raises_auth_error():
    with pytest.raises(VerkadaAuthError) as ei:
        _raise_for_status("https://x.com", _fake_response(401, "Unauthorized"))
    assert ei.value.status_code == 401


def test_raise_403_raises_forbidden_error():
    with pytest.raises(VerkadaForbiddenError) as ei:
        _raise_for_status("https://x.com", _fake_response(403))
    assert ei.value.status_code == 403


def test_raise_404_raises_not_found_error():
    with pytest.raises(VerkadaNotFoundError) as ei:
        _raise_for_status("https://x.com", _fake_response(404))
    assert ei.value.status_code == 404


def test_raise_429_no_retry_after():
    with pytest.raises(VerkadaRateLimitError) as ei:
        _raise_for_status("https://x.com", _fake_response(429))
    assert ei.value.status_code == 429
    assert ei.value.retry_after is None


def test_raise_429_with_retry_after_header():
    resp = MagicMock(spec=requests_lib.Response)
    resp.status_code = 429
    resp.text = "rate limited"
    resp.headers = {"Retry-After": "45"}
    with pytest.raises(VerkadaRateLimitError) as ei:
        _raise_for_status("https://x.com", resp)
    assert ei.value.retry_after == 45


def test_raise_429_non_numeric_retry_after():
    resp = MagicMock(spec=requests_lib.Response)
    resp.status_code = 429
    resp.text = ""
    resp.headers = {"Retry-After": "Fri, 01 Jan 2027 00:00:00 GMT"}
    with pytest.raises(VerkadaRateLimitError) as ei:
        _raise_for_status("https://x.com", resp)
    assert ei.value.retry_after is None


def test_raise_500_raises_server_error():
    with pytest.raises(VerkadaServerError) as ei:
        _raise_for_status("https://x.com", _fake_response(500))
    assert ei.value.status_code == 500


def test_raise_503_raises_server_error():
    with pytest.raises(VerkadaServerError):
        _raise_for_status("https://x.com", _fake_response(503))


def test_raise_other_4xx_raises_api_error():
    with pytest.raises(VerkadaAPIError) as ei:
        _raise_for_status("https://x.com", _fake_response(418))
    assert ei.value.status_code == 418


def test_raise_stores_endpoint_on_exception():
    url = "https://api.verkada.com/test/endpoint"
    with pytest.raises(VerkadaAuthError) as ei:
        _raise_for_status(url, _fake_response(401))
    assert ei.value.endpoint == url


# ---------- VerkadaRequestManager.__init__ ----------

def test_init_with_explicit_token_manager():
    mock_tm = MagicMock()
    rm = VerkadaRequestManager(token_manager=mock_tm)
    assert rm.token_manager is mock_tm


def test_init_both_token_manager_and_api_key_raises():
    with pytest.raises(ValueError, match="Cannot provide both"):
        VerkadaRequestManager(token_manager=MagicMock(), api_key="key")


def test_init_whitespace_api_key_raises():
    with pytest.raises(ValueError, match="non-empty"):
        VerkadaRequestManager(api_key="   ")


def test_init_custom_timeout_stored():
    mock_tm = MagicMock()
    rm = VerkadaRequestManager(timeout_seconds=60, token_manager=mock_tm)
    assert rm.timeout == 60


# ---------- _send_request ----------

def test_get_returns_json():
    mock_session, _ = _mock_session(json_return={"key": "val"})
    with patch("pykada.verkada_requests.Session", return_value=mock_session):
        result = _rm().get("https://api.test/ep")
    assert result == {"key": "val"}


def test_get_image_returns_bytes():
    mock_session, _ = _mock_session(content_return=b"\x89PNG")
    with patch("pykada.verkada_requests.Session", return_value=mock_session):
        result = _rm().get_image("https://api.test/img")
    assert result == b"\x89PNG"


def test_token_injected_into_headers():
    mock_session, _ = _mock_session(json_return={})
    with patch("pykada.verkada_requests.Session", return_value=mock_session):
        _rm().get("https://api.test/ep")
    _, kwargs = mock_session.request.call_args
    assert kwargs["headers"]["x-verkada-auth"] == "test-token"


def test_delete_return_json_false_returns_bytes():
    mock_session, mock_resp = _mock_session(content_return=b"")
    with patch("pykada.verkada_requests.Session", return_value=mock_session):
        result = _rm().delete("https://api.test/ep", return_json=False)
    assert isinstance(result, bytes)


def test_timeout_raises_verkada_error():
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_session.request.side_effect = requests_lib.exceptions.Timeout()
    with patch("pykada.verkada_requests.Session", return_value=mock_session):
        with pytest.raises(VerkadaError, match="timed out"):
            _rm().get("https://api.test/ep")


def test_connection_error_raises_verkada_error():
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_session.request.side_effect = requests_lib.exceptions.ConnectionError("refused")
    with patch("pykada.verkada_requests.Session", return_value=mock_session):
        with pytest.raises(VerkadaError):
            _rm().get("https://api.test/ep")


def test_retry_error_raises_server_error():
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_session.request.side_effect = requests_lib.exceptions.RetryError()
    with patch("pykada.verkada_requests.Session", return_value=mock_session):
        with pytest.raises(VerkadaServerError):
            _rm().get("https://api.test/ep")


def test_non_json_response_raises_verkada_error():
    mock_session, mock_resp = _mock_session()
    mock_resp.json.side_effect = ValueError("no JSON")
    mock_resp.text = "not json"
    with patch("pykada.verkada_requests.Session", return_value=mock_session):
        with pytest.raises(VerkadaError, match="not valid JSON"):
            _rm().get("https://api.test/ep")


def test_error_status_raises_typed_exception():
    mock_session, mock_resp = _mock_session(status_ok=False, status_code=401)
    mock_resp.text = "Unauthorized"
    mock_resp.headers = {}
    with patch("pykada.verkada_requests.Session", return_value=mock_session):
        with pytest.raises(VerkadaAuthError):
            _rm().get("https://api.test/ep")


# ---------- iterate_paginated_results ----------

def _pager(pages):
    it = iter(pages)
    def func(**kwargs):
        return next(it)
    return func


def test_iterate_single_page():
    func = _pager([{"items": [1, 2, 3], "next_page_token": None}])
    assert list(VerkadaRequestManager.iterate_paginated_results(
        func, items_key="items", next_token_key="next_page_token"
    )) == [1, 2, 3]


def test_iterate_multi_page():
    func = _pager([
        {"items": [1, 2], "next_page_token": "tok"},
        {"items": [3, 4], "next_page_token": None},
    ])
    assert list(VerkadaRequestManager.iterate_paginated_results(
        func, items_key="items", next_token_key="next_page_token"
    )) == [1, 2, 3, 4]


def test_iterate_empty_page():
    func = _pager([{"items": [], "next_page_token": None}])
    assert list(VerkadaRequestManager.iterate_paginated_results(
        func, items_key="items", next_token_key="next_page_token"
    )) == []


def test_iterate_infers_both_keys():
    func = _pager([{"alerts": ["a", "b"], "page_token": None}])
    assert list(VerkadaRequestManager.iterate_paginated_results(func)) == ["a", "b"]


def test_iterate_no_inferrable_token_key_raises():
    def func(**kwargs):
        return {"items": [], "tok_a": None, "tok_b": None}
    with pytest.raises(ValueError, match="next_token_key"):
        list(VerkadaRequestManager.iterate_paginated_results(func, items_key="items"))


def test_iterate_no_inferrable_items_key_raises():
    def func(**kwargs):
        return {"items_a": [], "items_b": [], "page_token": None}
    with pytest.raises(ValueError, match="items_key"):
        list(VerkadaRequestManager.iterate_paginated_results(
            func, next_token_key="page_token"
        ))


def test_iterate_non_dict_response_stops():
    def func(**kwargs):
        return "not a dict"
    assert list(VerkadaRequestManager.iterate_paginated_results(
        func, items_key="items", next_token_key="page_token"
    )) == []


def test_iterate_initial_params_forwarded():
    received_params = {}

    def func(**kwargs):
        received_params.update(kwargs)
        return {"items": [], "next_page_token": None}

    list(VerkadaRequestManager.iterate_paginated_results(
        func,
        items_key="items",
        next_token_key="next_page_token",
        initial_params={"camera_id": "cam1"},
    ))
    assert received_params.get("camera_id") == "cam1"
