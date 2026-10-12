import types
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from typeguard import TypeCheckError

from pykada import EventsClient
from pykada.endpoints import V2_EVENTS_ENDPOINT
from pykada.events import get_all_events, get_events

RM_GET = "pykada.verkada_requests.VerkadaRequestManager.get"


@patch(RM_GET, return_value={"items": [], "cursor": None})
def test_get_events_no_args(mock_get):
    assert isinstance(get_events(), dict)
    mock_get.assert_called_once_with(V2_EVENTS_ENDPOINT, params={})


@patch(RM_GET, return_value={"items": [], "cursor": None})
def test_get_events_builds_all_filters(mock_get):
    get_events(start_time=datetime(2025, 1, 17, 9, 0, tzinfo=timezone.utc),
               end_time="2025-01-17T17:00:00Z",
               product_types=["camera", "access_control"],
               event_types=["motion", "door_opened"],
               device_ids=["d1", "d2"],
               site_ids=["s1"],
               limit=50,
               cursor="abc")
    mock_get.assert_called_once_with(V2_EVENTS_ENDPOINT, params={
        "start_time": "2025-01-17T09:00:00Z",
        "end_time": "2025-01-17T17:00:00Z",
        "product_types": "camera,access_control",
        "event_types": "motion,door_opened",
        "device_ids": "d1,d2",
        "site_ids": "s1",
        "limit": 50,
        "cursor": "abc",
    })


@patch(RM_GET, return_value={"items": [], "cursor": None})
def test_get_events_empty_lists_omitted(mock_get):
    get_events(product_types=[], event_types=[], device_ids=[], site_ids=[])
    mock_get.assert_called_once_with(V2_EVENTS_ENDPOINT, params={})


@patch(RM_GET, return_value={"items": [], "cursor": None})
@pytest.mark.parametrize("product", ["camera", "access_control", "sensor", "intercom"])
def test_get_events_accepts_each_product_type(mock_get, product):
    get_events(product_types=[product])
    assert mock_get.call_args.kwargs["params"]["product_types"] == product


def test_get_events_unknown_product_type_raises():
    with pytest.raises(ValueError, match="Product types"):
        get_events(product_types=["camera", "doorbell"])


@pytest.mark.parametrize("limit", [0, 201])
def test_get_events_invalid_limit(limit):
    with pytest.raises(ValueError, match="limit must be between 1 and 200"):
        get_events(limit=limit)


def test_get_events_rejects_epoch_ints():
    with pytest.raises(TypeCheckError):
        get_events(start_time=1737104400)


def test_get_events_comma_string_not_accepted_for_lists():
    with pytest.raises(TypeCheckError):
        get_events(device_ids="d1,d2")


@patch(RM_GET)
def test_get_all_events_walks_pages_with_same_filters(mock_get):
    mock_get.side_effect = [
        {"items": [{"event_id": "1", "device_type": "camera"}], "cursor": "c1"},
        {"items": [{"event_id": "2", "device_type": "sensor"}], "cursor": None},
    ]
    result = get_all_events(start_time="2025-01-17T09:00:00Z",
                            end_time="2025-01-17T10:00:00Z",
                            product_types=["camera", "sensor"])
    assert isinstance(result, types.GeneratorType)
    assert [e["event_id"] for e in result] == ["1", "2"]
    first, second = (c.kwargs["params"] for c in mock_get.call_args_list)
    assert first["product_types"] == second["product_types"] == "camera,sensor"
    assert first["end_time"] == second["end_time"] == "2025-01-17T10:00:00Z"
    assert "cursor" not in first and second["cursor"] == "c1"


@patch(RM_GET, return_value={"items": [], "cursor": None})
def test_get_all_events_pins_end_time(mock_get):
    list(get_all_events())
    assert mock_get.call_args.kwargs["params"]["end_time"].endswith("Z")


def test_get_all_events_validates_product_types_eagerly():
    # Raised at call time, not on first iteration
    with pytest.raises(ValueError, match="Product types"):
        get_all_events(product_types=["bogus"])


@patch(RM_GET, return_value={"items": [], "cursor": None})
def test_events_client_oop(mock_get):
    client = EventsClient(api_key="key")
    client.get_events(event_types=["motion"])
    mock_get.assert_called_once_with(V2_EVENTS_ENDPOINT, params={"event_types": "motion"})
