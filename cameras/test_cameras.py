import pytest
from typeguard import TypeCheckError
from unittest.mock import patch

# Import your actual module here. Adjust `alerts` if needed.
from cameras import *

# ---------- Type Error Tests ----------

@pytest.mark.parametrize("func, kwargs", [
    (get_camera_alerts, {"start_time": "not-a-number"}),  # invalid int
    (delete_lpoi, {"license_plate": 123}),         # invalid str
    (update_lpoi, {"license_plate": "ABC123", "description": 456}),  # invalid str
    (create_lpoi, {"license_plate": None, "description": "Valid"}),  # invalid str
    (get_lpr_timestamps, {"camera_id": "cam1", "license_plate": "XYZ", "start_time": "now"}),  # invalid int
    (get_object_counts, {"camera_id": 101}),  # should be str
    (set_object_position_mqtt, {
        "broker_cert": None, "broker_host_port": "host:1883", "camera_id": "cam1"
    }),  # None not allowed
    (update_cloud_backup_settings, {
        "camera_id": "abc",
        "days_to_preserve": "1,1,1,1,1,1,1",
        "enabled": "yes",  # invalid bool
        "time_to_preserve": "0,86400",
        "upload_timeslot": "anytime",
        "video_quality": "STANDARD_QUALITY",
        "video_to_upload": "ALL"
    }),
])
def test_type_errors(func, kwargs):
    with pytest.raises(TypeCheckError):
        func(**kwargs)

# ---------- Dict Return Type Tests (Mocked) ----------

@patch("cameras.get_request", return_value={"status": "ok"})
@pytest.mark.parametrize("func, kwargs", [
    (get_camera_alerts, {}),
    (get_lpois, {}),
    (get_lpr_timestamps, {"camera_id": "cam1", "license_plate": "XYZ"}),
    (get_object_counts, {"camera_id": "cam1"}),
    (get_occupancy_trends, {"camera_id": "cam1"}),
    (get_cloud_backup_settings, {"camera_id": "cam1"}),
    (get_camera_data, {}),
])
def test_get_request_dict_returns(mock_get, func, kwargs):
    result = func(**kwargs)
    assert isinstance(result, dict)

@patch("cameras.delete_request", return_value={"deleted": True})
def test_delete_lpoi_returns_dict(mock_delete):
    result = delete_lpoi("ABC123")
    assert isinstance(result, dict)

@patch("cameras.patch_request", return_value={"updated": True})
def test_update_lpoi_returns_dict(mock_patch):
    result = update_lpoi("ABC123", "Updated description")
    assert isinstance(result, dict)

@patch("cameras.post_request", return_value={"created": True})
def test_create_lpoi_returns_dict(mock_post):
    result = create_lpoi("XYZ999", "Stolen Vehicle")
    assert isinstance(result, dict)

@patch("cameras.post_request", return_value={"configured": True})
def test_set_object_position_mqtt_returns_dict(mock_post):
    result = set_object_position_mqtt(
        broker_cert="cert",
        broker_host_port="broker:1883",
        camera_id="cam1",
        client_username="user",
        client_password="pass"
    )
    assert isinstance(result, dict)

@patch("cameras.post_request", return_value={"backup": True})
def test_set_cloud_backup_settings_returns_dict(mock_post):
    result = update_cloud_backup_settings(
        camera_id="cam1",
        days_to_preserve="1,1,1,1,1,1,1",
        enabled=True,
        time_to_preserve="0,86400",
        upload_timeslot="night",
        video_quality="STANDARD_QUALITY",
        video_to_upload="ALL"
    )
    assert isinstance(result, dict)
