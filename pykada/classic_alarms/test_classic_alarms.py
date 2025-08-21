import pytest
from typeguard import TypeCheckError
from unittest.mock import patch

# Adjust this import to point at the module where you defined these two functions.
from pykada.classic_alarms import get_alarm_devices, get_alarm_site_information
from pykada.endpoints import ALARMS_DEVICES_ENDPOINT, ALARMS_SITES_ENDPOINT


# ————— get_alarm_devices ————— #

@pytest.mark.parametrize("bad_id", ["", "   "])
def test_get_alarm_devices_empty_site_id_raises_value_error(bad_id):
    with pytest.raises(ValueError) as exc:
        get_alarm_devices(bad_id)
    assert "site_id must be a non-empty string" in str(exc.value)


def test_get_alarm_devices_none_site_id_raises_type_error():
    with pytest.raises(TypeCheckError):
        get_alarm_devices(None)  # site_id: str, None is invalid


@patch("classic_alarms.get_request", return_value={"devices": []})
def test_get_alarm_devices_returns_dict(mock_get):
    result = get_alarm_devices("site123")
    mock_get.assert_called_once_with(
        ALARMS_DEVICES_ENDPOINT,
        params={"site_id": "site123"}
    )
    assert isinstance(result, dict)


@patch("classic_alarms.get_request", return_value={"devices": ["a","b"]})
def test_get_alarm_devices_with_device_ids(mock_get):
    ids = ["dev1", "dev2", "dev3"]
    result = get_alarm_devices("site123", device_ids=ids)
    mock_get.assert_called_once_with(
        ALARMS_DEVICES_ENDPOINT,
        params={"site_id": "site123", "device_ids": "dev1,dev2,dev3"}
    )
    assert result == {"devices": ["a","b"]}


# ————— get_alarm_site_information ————— #

@patch("classic_alarms.get_request", return_value={"sites": []})
def test_get_site_information_default(mock_get):
    result = get_alarm_site_information()
    mock_get.assert_called_once_with(
        ALARMS_SITES_ENDPOINT,
        params={}
    )
    assert isinstance(result, dict)


@patch("classic_alarms.get_request", return_value={"sites": ["s1","s2"]})
def test_get_site_information_with_site_ids(mock_get):
    site_ids = ["s1", "s2", "s3"]
    result = get_alarm_site_information(site_ids=site_ids)
    mock_get.assert_called_once_with(
        ALARMS_SITES_ENDPOINT,
        params={"site_ids": "s1,s2,s3"}
    )
    assert result == {"sites": ["s1","s2"]}
