import types
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from typeguard import TypeCheckError

from pykada.endpoints import V2_SENSOR_ALERTS_ENDPOINT, V2_SENSORS_ENDPOINT
from pykada.sensors import (
    check_sensor_fields,
    get_all_sensor_alerts,
    get_all_sensor_data,
    get_all_sensors,
    get_sensor_alerts,
    get_sensor_data,
    list_sensors,
)

RM_GET = "pykada.verkada_requests.VerkadaRequestManager.get"


# ----------------------------
# list_sensors / get_all_sensors
# ----------------------------

@patch(RM_GET, return_value={"items": [], "cursor": None})
def test_list_sensors_no_args(mock_get):
    assert isinstance(list_sensors(), dict)
    mock_get.assert_called_once_with(V2_SENSORS_ENDPOINT, params={})


@patch(RM_GET, return_value={"items": [], "cursor": None})
def test_list_sensors_paging(mock_get):
    list_sensors(limit=50, cursor="MTAw")
    mock_get.assert_called_once_with(V2_SENSORS_ENDPOINT,
                                     params={"limit": 50, "cursor": "MTAw"})


@pytest.mark.parametrize("limit", [0, 201])
def test_list_sensors_invalid_limit(limit):
    with pytest.raises(ValueError, match="limit must be between 1 and 200"):
        list_sensors(limit=limit)


@patch(RM_GET)
def test_get_all_sensors_walks_pages(mock_get):
    mock_get.side_effect = [
        {"items": [{"device_id": "a"}], "cursor": "c1"},
        {"items": [{"device_id": "b"}], "cursor": None},
    ]
    result = get_all_sensors()
    assert isinstance(result, types.GeneratorType)
    assert [s["device_id"] for s in result] == ["a", "b"]
    assert mock_get.call_args_list[1].kwargs["params"] == {"limit": 100, "cursor": "c1"}


# ----------------------------
# get_sensor_alerts
# ----------------------------

def test_get_sensor_alerts_empty_device_ids_raises():
    with pytest.raises(ValueError, match="device_ids"):
        get_sensor_alerts([])


def test_get_sensor_alerts_invalid_fields_raises():
    with pytest.raises(ValueError, match="not in the.*valid types"):
        get_sensor_alerts(["123"], fields=["invalid_field"])


@patch(RM_GET, return_value={"items": [], "cursor": None})
def test_get_sensor_alerts_builds_v2_params(mock_get):
    start = datetime(2025, 7, 17, 20, 0, tzinfo=timezone.utc)
    result = get_sensor_alerts(["d1", "d2"], start_time=start,
                               end_time="2025-07-17T21:06:20Z",
                               fields=["temperature", "humidity"], limit=10, cursor="c")
    assert isinstance(result, dict)
    mock_get.assert_called_once_with(V2_SENSOR_ALERTS_ENDPOINT, params={
        "device_ids": "d1,d2",
        "start_time": "2025-07-17T20:00:00Z",
        "end_time": "2025-07-17T21:06:20Z",
        "fields": "temperature,humidity",
        "limit": 10,
        "cursor": "c",
    })


def test_get_sensor_alerts_rejects_epoch_ints():
    with pytest.raises(TypeCheckError):
        get_sensor_alerts(["d1"], start_time=1)


def test_get_sensor_alerts_invalid_limit():
    with pytest.raises(ValueError, match="limit"):
        get_sensor_alerts(["d1"], limit=500)


def test_get_all_sensor_alerts_empty_device_ids_raises():
    with pytest.raises(ValueError, match="device_ids"):
        get_all_sensor_alerts([])


def test_get_all_sensor_alerts_invalid_fields_raises():
    with pytest.raises(ValueError, match="not in the.*valid types"):
        get_all_sensor_alerts(["dev1"], fields=["bad_field"])


@patch(RM_GET)
def test_get_all_sensor_alerts_walks_pages(mock_get):
    mock_get.side_effect = [
        {"items": [{"alert_event_id": "1"}], "cursor": "c1"},
        {"items": [{"alert_event_id": "2"}], "cursor": None},
    ]
    result = get_all_sensor_alerts(["dev1"], fields=["temperature"])
    assert isinstance(result, types.GeneratorType)
    assert [a["alert_event_id"] for a in result] == ["1", "2"]
    second = mock_get.call_args_list[1].kwargs["params"]
    assert second["device_ids"] == "dev1"
    assert second["fields"] == "temperature"
    assert second["cursor"] == "c1"


# ----------------------------
# get_sensor_data
# ----------------------------

def test_get_sensor_data_invalid_fields_raises():
    with pytest.raises(ValueError, match="not in the.*valid types"):
        get_sensor_data("abc", fields=["bad_field"])


@patch(RM_GET, return_value={"device_id": "abc", "items": [], "cursor": None})
def test_get_sensor_data_uses_path_and_iso_interval(mock_get):
    result = get_sensor_data("abc", start_time="2025-07-17T20:00:00Z",
                             end_time="2025-07-17T21:00:00Z",
                             fields=["humidity"], interval=timedelta(minutes=5))
    assert isinstance(result, dict)
    mock_get.assert_called_once_with(f"{V2_SENSORS_ENDPOINT}/abc/data", params={
        "start_time": "2025-07-17T20:00:00Z",
        "end_time": "2025-07-17T21:00:00Z",
        "fields": "humidity",
        "interval": "PT5M",
    })


@patch(RM_GET, return_value={"device_id": "abc", "items": [], "cursor": None})
def test_get_sensor_data_accepts_duration_string(mock_get):
    get_sensor_data("abc", interval="PT1H")
    assert mock_get.call_args.kwargs["params"]["interval"] == "PT1H"


def test_get_sensor_data_rejects_v1_interval_format():
    with pytest.raises(ValueError, match="ISO 8601 duration"):
        get_sensor_data("abc", interval="5m")


@pytest.mark.parametrize("device_id", ["", "  "])
def test_get_sensor_data_empty_device_id_raises(device_id):
    with pytest.raises(ValueError, match="device_id"):
        get_sensor_data(device_id)


@patch(RM_GET)
def test_get_all_sensor_data_walks_pages(mock_get):
    mock_get.side_effect = [
        {"device_id": "dev1", "items": [{"timestamp": "t1"}], "cursor": "c1"},
        {"device_id": "dev1", "items": [{"timestamp": "t2"}], "cursor": None},
    ]
    result = get_all_sensor_data("dev1", interval="PT5M")
    assert isinstance(result, types.GeneratorType)
    assert [r["timestamp"] for r in result] == ["t1", "t2"]
    assert all(c.args[0] == f"{V2_SENSORS_ENDPOINT}/dev1/data"
               for c in mock_get.call_args_list)


def test_get_all_sensor_data_invalid_fields_raises():
    with pytest.raises(ValueError, match="not in the.*valid types"):
        get_all_sensor_data("dev1", fields=["bad_field"])


# ----------------------------
# check_sensor_fields
# ----------------------------

def test_check_sensor_fields_none_returns_none():
    assert check_sensor_fields(None) is None


def test_check_sensor_fields_empty_list_returns_none():
    assert check_sensor_fields([]) is None


def test_check_sensor_fields_valid_fields_no_error():
    check_sensor_fields(["temperature", "humidity"])


def test_check_sensor_fields_invalid_field_raises():
    with pytest.raises(ValueError, match="not in the.*valid types"):
        check_sensor_fields(["not_a_real_field"])


def test_check_sensor_fields_mixed_valid_invalid_raises():
    with pytest.raises(ValueError, match="not in the.*valid types"):
        check_sensor_fields(["temperature", "bad_field"])
