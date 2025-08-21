import pytest
from typeguard import TypeCheckError
from unittest.mock import patch

# Adjust this to wherever you’ve placed get_access_events
import access_events as ae
from pykada.access_control import get_access_events
from pykada.enums import VALID_ACCESS_EVENT_TYPES_ENUM


# 1. Type‐checking rejects wrong types for each parameter
@pytest.mark.parametrize("kwargs", [
    {"start_time": "abc"},
    {"end_time": "xyz"},
    {"page_token": 123},
    {"page_size": "big"},
    {"event_type": "notalist"},
    {"site_id": 999},
    {"device_id": 888},
    {"user_id": []},  # should be str if provided
])
def test_type_errors(kwargs):
    with pytest.raises(TypeCheckError):
        get_access_events(**kwargs)


# 2. page_size out of allowed range raises ValueError
@pytest.mark.parametrize("size", [-5, 201])
def test_page_size_value_error(size):
    with pytest.raises(ValueError) as exc:
        get_access_events(page_size=size)
    assert "page_size must be between 0 and 200" in str(exc.value)


# 3. invalid event_type values raise ValueError listing both the bad and the allowed set
def test_invalid_event_types():
    # Pick one clearly invalid and one valid
    valid = list(VALID_ACCESS_EVENT_TYPES_ENUM.values())[0]
    bads = ["not_an_event", valid]
    with pytest.raises(ValueError) as exc:
        get_access_events(event_type=bads)
    msg = str(exc.value)
    assert "not_an_event" in msg
    # should mention the list of all valid types
    for v in VALID_ACCESS_EVENT_TYPES_ENUM.values():
        assert v in msg


# 4. default start_time/end_time computed off time.time()
@patch("access_events.get_request", return_value={"ok": True})
@patch("access_events.time")
def test_defaults_use_current_time(mock_time, mock_get):
    # freeze time
    mock_time.time.return_value = 10_000
    result = get_access_events()
    # default window: [10000-3600, 10000]
    expected = {
        "start_time": 10_000 - 3600,
        "end_time": 10_000,
        "page_size": 100
    }
    mock_get.assert_called_once_with(ae.ACCESS_EVENTS_ENDPOINT, params=expected)
    assert result == {"ok": True}


# 5. all parameters passed and formatted correctly
@patch("access_events.get_request", return_value={"events": ["e1"]})
def test_all_params_forwarded(mock_get):
    et = list(VALID_ACCESS_EVENT_TYPES_ENUM.values())[0:3]
    kwargs = {
        "start_time": 1_000,
        "end_time": 2_000,
        "page_token": "ABC",
        "page_size": 50,
        "event_type": et,
        "site_id": "siteX",
        "device_id": "devY",
        "user_id": "userZ"
    }
    res = get_access_events(**kwargs)
    mock_get.assert_called_once_with(
        ae.ACCESS_EVENTS_ENDPOINT,
        params={
            "start_time": 1_000,
            "end_time": 2_000,
            "page_token": "ABC",
            "page_size": 50,
            "event_type": ",".join(et),
            "site_id": "siteX",
            "device_id": "devY",
            "user_id": "userZ"
        }
    )
    assert res == {"events": ["e1"]}


# 6. None or empty optionals are dropped
@patch("access_events.get_request", return_value={"empty": True})
def test_none_and_empty_dropped(mock_get):
    res = get_access_events(
        start_time=111,
        end_time=222,
        page_size=20,
        event_type=None,
        site_id=None,
        device_id=None,
        user_id=None
    )
    mock_get.assert_called_once_with(
        ae.ACCESS_EVENTS_ENDPOINT,
        params={
            "start_time": 111,
            "end_time": 222,
            "page_size": 20
        }
    )
    assert res == {"empty": True}
