import pytest
from typeguard import TypeCheckError
from unittest.mock import patch

# Import the cameras module
from pykada.cameras import *

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

@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"status": "ok"})
@pytest.mark.parametrize("func, kwargs", [
    (get_camera_alerts, {}),
    (get_lpois, {}),
    (get_lpr_timestamps, {"camera_id": "cam1", "license_plate": "XYZ"}),
    (get_object_counts, {"camera_id": "cam1"}),
    (get_occupancy_trends, {"camera_id": "cam1", "trend_type": "person", "interval": "1_hour"}),
    (get_cloud_backup_settings, {"camera_id": "cam1"}),
    (get_camera_data, {}),
])
def test_get_request_dict_returns(mock_get, func, kwargs):
    result = func(**kwargs)
    assert isinstance(result, dict)

@patch("pykada.verkada_requests.VerkadaRequestManager.delete", return_value={"deleted": True})
def test_delete_lpoi_returns_dict(mock_delete):
    result = delete_lpoi("ABC123")
    assert isinstance(result, dict)

@patch("pykada.verkada_requests.VerkadaRequestManager.patch", return_value={"updated": True})
def test_update_lpoi_returns_dict(mock_patch):
    result = update_lpoi("ABC123", "Updated description")
    assert isinstance(result, dict)

@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"created": True})
def test_create_lpoi_returns_dict(mock_post):
    result = create_lpoi("XYZ999", "Stolen Vehicle")
    assert isinstance(result, dict)

@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"configured": True})
def test_set_object_position_mqtt_returns_dict(mock_post):
    result = set_object_position_mqtt(
        broker_cert="cert",
        broker_host_port="broker:1883",
        camera_id="cam1",
        client_username="user",
        client_password="pass"
    )
    assert isinstance(result, dict)

@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"backup": True})
def test_set_cloud_backup_settings_returns_dict(mock_post):
    result = update_cloud_backup_settings(
        camera_id="cam1",
        days_to_preserve="1,1,1,1,1,1,1",
        enabled=True,
        time_to_preserve="0,86400",
        upload_timeslot="0,86400",
        video_quality="STANDARD_QUALITY",
        video_to_upload="ALL"
    )
    assert isinstance(result, dict)


@patch("pykada.verkada_requests.VerkadaRequestManager.get")
def test_get_viewing_stations_returns_dict(mock_get):
    mock_get.return_value = {"viewing_stations": []}
    result = get_viewing_stations()
    assert isinstance(result, dict)
    mock_get.assert_called_once()


# ---------- footage & thumbnails ----------

@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"link": "url"})
def test_get_footage_link_returns_dict(mock_get):
    result = get_footage_link("cam1")
    assert isinstance(result, dict)


@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"link": "url"})
def test_get_footage_link_with_timestamp(mock_get):
    result = get_footage_link("cam1", timestamp=1700000000)
    assert isinstance(result, dict)
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["timestamp"] == 1700000000


@patch("pykada.verkada_requests.VerkadaRequestManager.get_image", return_value=b"\xff\xd8\xff")
def test_get_historical_thumbnail_returns_bytes(mock_get_image):
    result = get_historical_thumbnail("cam1")
    assert result == b"\xff\xd8\xff"


@patch("pykada.verkada_requests.VerkadaRequestManager.get_image", return_value=b"\xff\xd8\xff")
def test_get_latest_thumbnail_returns_bytes(mock_get_image):
    result = get_latest_thumbnail("cam1")
    assert result == b"\xff\xd8\xff"


@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"link": "url"})
def test_get_thumbnail_link_returns_dict(mock_get):
    result = get_thumbnail_link("cam1")
    assert isinstance(result, dict)


@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"jwt": "tok"})
def test_get_streaming_token_returns_dict(mock_get):
    result = get_streaming_token()
    assert isinstance(result, dict)


# ---------- dashboard ----------

@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"trends": []})
def test_get_dashboard_widget_trends_returns_dict(mock_post):
    result = get_dashboard_widget_trends("dash1")
    assert isinstance(result, dict)


def test_get_dashboard_widget_trends_empty_id_raises():
    with pytest.raises(ValueError, match="dashboard_id"):
        get_dashboard_widget_trends("")


@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"trends": []})
def test_get_dashboard_occupancy_trend_data_returns_dict(mock_get):
    result = get_dashboard_occupancy_trend_data("dash1")
    assert isinstance(result, dict)


def test_get_dashboard_occupancy_trend_data_empty_id_raises():
    with pytest.raises(ValueError, match="dashboard_id"):
        get_dashboard_occupancy_trend_data("")


# ---------- POI ----------

@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"persons_of_interest": []})
def test_get_pois_returns_dict(mock_get):
    result = get_pois()
    assert isinstance(result, dict)


@patch("pykada.verkada_requests.VerkadaRequestManager.patch", return_value={"updated": True})
def test_update_poi_returns_dict(mock_patch):
    result = update_poi("pid1", "new label")
    assert isinstance(result, dict)


@patch("pykada.verkada_requests.VerkadaRequestManager.delete", return_value={"deleted": True})
def test_delete_poi_returns_dict(mock_delete):
    result = delete_poi("pid1")
    assert isinstance(result, dict)


@patch("builtins.open", return_value=__import__("io").BytesIO(b"fake-image-bytes"))
@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"created": True})
def test_create_poi_returns_dict(mock_post, mock_open):
    import io
    mock_open.return_value.__enter__ = lambda s: io.BytesIO(b"fake-image-bytes")
    mock_open.return_value.__exit__ = lambda s, *a: False
    result = create_poi("image.jpg", "Suspect")
    assert isinstance(result, dict)


# ---------- LPR / seen plates ----------

@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"detections": []})
def test_get_seen_license_plates_returns_dict(mock_get):
    result = get_seen_license_plates("cam1")
    assert isinstance(result, dict)


def test_get_seen_license_plates_empty_camera_id_raises():
    with pytest.raises(ValueError):
        get_seen_license_plates("")


# ---------- audio ----------

@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"enabled": True})
def test_get_camera_audio_status_returns_dict(mock_get):
    result = get_camera_audio_status("cam1")
    assert isinstance(result, dict)


def test_get_camera_audio_status_empty_camera_id_raises():
    with pytest.raises(ValueError):
        get_camera_audio_status("")


@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"enabled": False})
def test_set_camera_audio_status_returns_dict(mock_post):
    result = set_camera_audio_status("cam1", enabled=False)
    assert isinstance(result, dict)


# ---------- max counts & occupancy ----------

@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"counts": []})
def test_get_max_people_vehicle_counts_returns_dict(mock_get):
    result = get_max_people_vehicle_counts("cam1")
    assert isinstance(result, dict)


def test_get_max_people_vehicle_counts_empty_camera_id_raises():
    with pytest.raises(ValueError):
        get_max_people_vehicle_counts("")


@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"cameras": []})
def test_get_occupancy_trend_enabled_cameras_returns_dict(mock_get):
    result = get_occupancy_trend_enabled_cameras()
    assert isinstance(result, dict)


# ---------- cloud backup validation ----------

def test_update_cloud_backup_days_to_preserve_wrong_count_raises():
    with pytest.raises(ValueError, match="days_to_preserve"):
        update_cloud_backup_settings(
            camera_id="cam1", days_to_preserve="1,1,1,1,1,1",
            enabled=1, time_to_preserve="0,86400",
            upload_timeslot="0,86400", video_quality="STANDARD_QUALITY",
            video_to_upload="ALL",
        )


def test_update_cloud_backup_days_to_preserve_invalid_value_raises():
    with pytest.raises(ValueError, match="days_to_preserve"):
        update_cloud_backup_settings(
            camera_id="cam1", days_to_preserve="1,1,1,1,1,1,X",
            enabled=1, time_to_preserve="0,86400",
            upload_timeslot="0,86400", video_quality="STANDARD_QUALITY",
            video_to_upload="ALL",
        )


def test_update_cloud_backup_enabled_invalid_raises():
    with pytest.raises(ValueError, match="enabled"):
        update_cloud_backup_settings(
            camera_id="cam1", days_to_preserve="1,1,1,1,1,1,1",
            enabled=2, time_to_preserve="0,86400",
            upload_timeslot="0,86400", video_quality="STANDARD_QUALITY",
            video_to_upload="ALL",
        )


def test_update_cloud_backup_time_to_preserve_invalid_raises():
    with pytest.raises(ValueError, match="time_to_preserve"):
        update_cloud_backup_settings(
            camera_id="cam1", days_to_preserve="1,1,1,1,1,1,1",
            enabled=1, time_to_preserve="0",
            upload_timeslot="0,86400", video_quality="STANDARD_QUALITY",
            video_to_upload="ALL",
        )


def test_update_cloud_backup_video_quality_invalid_raises():
    with pytest.raises(ValueError, match="video_quality"):
        update_cloud_backup_settings(
            camera_id="cam1", days_to_preserve="1,1,1,1,1,1,1",
            enabled=1, time_to_preserve="0,86400",
            upload_timeslot="0,86400", video_quality="ULTRA_QUALITY",
            video_to_upload="ALL",
        )


def test_update_cloud_backup_video_to_upload_invalid_raises():
    with pytest.raises(ValueError, match="video_to_upload"):
        update_cloud_backup_settings(
            camera_id="cam1", days_to_preserve="1,1,1,1,1,1,1",
            enabled=1, time_to_preserve="0,86400",
            upload_timeslot="0,86400", video_quality="STANDARD_QUALITY",
            video_to_upload="PARTIAL",
        )


# ---------- pagination generators ----------

@patch("pykada.verkada_requests.VerkadaRequestManager.get",
       return_value={"alerts": [], "next_page_token": None})
def test_get_all_camera_alerts_returns_generator(mock_get):
    import types
    result = get_all_camera_alerts()
    assert isinstance(result, types.GeneratorType)


@patch("pykada.verkada_requests.VerkadaRequestManager.get",
       return_value={"cameras": [], "next_page_token": None})
def test_get_all_camera_data_returns_generator(mock_get):
    import types
    result = get_all_camera_data()
    assert isinstance(result, types.GeneratorType)
