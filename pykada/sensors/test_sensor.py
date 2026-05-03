import pytest
import types
from unittest.mock import patch
from pykada.sensors import (
    check_sensor_fields, get_sensor_alerts, get_sensor_data,
    get_all_sensor_alerts, get_all_sensor_data,
)


# Patch SENSOR_FIELD_ENUM to simulate valid fields
@pytest.fixture(autouse=True)
def patch_sensor_enum(monkeypatch):
    monkeypatch.setattr("pykada.sensors.SENSOR_FIELD_ENUM", {
        "temp": "temperature",
        "hum": "humidity",
        "co2": "co2"
    })

# ----------------------------
# Tests for get_sensor_alerts
# ----------------------------

def test_get_sensor_alerts_empty_device_ids_raises():
    with pytest.raises(ValueError, match="device_ids"):
        get_sensor_alerts([])

def test_get_sensor_alerts_invalid_fields_raises():
    with pytest.raises(ValueError, match="not in the.*valid types"):
        get_sensor_alerts(["123"], fields=["invalid_field"])

@patch("pykada.verkada_requests.VerkadaRequestManager.get")
@patch("pykada.sensors.remove_null_fields", side_effect=lambda x: x)
def test_get_sensor_alerts_valid(mock_clean, mock_get):
    mock_get.return_value = {"alerts": []}
    result = get_sensor_alerts(["123"], start_time=1, end_time=2, fields=["temperature"])
    assert isinstance(result, dict)
    assert mock_get.called

# ----------------------------
# Tests for get_sensor_data
# ----------------------------

def test_get_sensor_data_invalid_fields_raises():
    with pytest.raises(ValueError, match="not in the.*valid types"):
        get_sensor_data("abc", fields=["bad_field"])

@patch("pykada.verkada_requests.VerkadaRequestManager.get")
@patch("pykada.sensors.remove_null_fields", side_effect=lambda x: x)
def test_get_sensor_data_valid(mock_clean, mock_get):
    mock_get.return_value = {"data": []}
    result = get_sensor_data("abc", start_time=1, end_time=2, fields=["humidity"], interval="5m")
    assert isinstance(result, dict)
    assert mock_get.called


# ----------------------------
# Tests for check_sensor_fields
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


# ----------------------------
# Tests for get_all_sensor_alerts
# ----------------------------

def test_get_all_sensor_alerts_empty_device_ids_raises():
    with pytest.raises(ValueError, match="device_ids"):
        get_all_sensor_alerts([])


@patch("pykada.verkada_requests.VerkadaRequestManager.get",
       return_value={"alert_events": [], "page_cursor": None})
def test_get_all_sensor_alerts_returns_generator(mock_get):
    result = get_all_sensor_alerts(["dev1"])
    assert isinstance(result, types.GeneratorType)


@patch("pykada.verkada_requests.VerkadaRequestManager.get",
       return_value={"alert_events": [], "page_cursor": None})
def test_get_all_sensor_alerts_invalid_fields_raises(mock_get):
    with pytest.raises(ValueError, match="not in the.*valid types"):
        get_all_sensor_alerts(["dev1"], fields=["bad_field"])


# ----------------------------
# Tests for get_all_sensor_data
# ----------------------------

@patch("pykada.verkada_requests.VerkadaRequestManager.get",
       return_value={"data": [], "page_cursor": None})
def test_get_all_sensor_data_returns_generator(mock_get):
    result = get_all_sensor_data("dev1")
    assert isinstance(result, types.GeneratorType)


@patch("pykada.verkada_requests.VerkadaRequestManager.get",
       return_value={"data": [], "page_cursor": None})
def test_get_all_sensor_data_invalid_fields_raises(mock_get):
    with pytest.raises(ValueError, match="not in the.*valid types"):
        get_all_sensor_data("dev1", fields=["bad_field"])
