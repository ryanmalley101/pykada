import pytest
from unittest.mock import patch
from sensors import get_sensor_alerts, get_sensor_data
import numpy as np

# Patch SENSOR_FIELD_ENUM to simulate valid fields
@pytest.fixture(autouse=True)
def patch_sensor_enum(monkeypatch):
    monkeypatch.setattr("sensors.SENSOR_FIELD_ENUM", {
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

@patch("sensors.get_request")
@patch("sensors.remove_null_fields", side_effect=lambda x: x)
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

@patch("sensors.get_request")
@patch("sensors.remove_null_fields", side_effect=lambda x: x)
def test_get_sensor_data_valid(mock_clean, mock_get):
    mock_get.return_value = {"data": []}
    result = get_sensor_data("abc", start_time=1, end_time=2, fields=["humidity"], interval="5m")
    assert isinstance(result, dict)
    assert mock_get.called
