import types
from datetime import datetime, time, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from typeguard import TypeCheckError

from pykada.cameras import *
from pykada.cameras import CamerasClient
from pykada.endpoints import (
    LPOI_BATCH_ENDPOINT,
    V2_ANALYTICS_CAMERAS_ENDPOINT,
    V2_CAMERA_SITES_ENDPOINT,
    V2_CAMERAS_ENDPOINT,
    V2_FOOTAGE_LINK_ENDPOINT,
    V2_LPOI_ENDPOINT,
    V2_LPR_ZONES_ENDPOINT,
    V2_NCIC_PLATE_SEARCH_ENDPOINT,
    V2_OCCUPANCY_TRENDS_CAMERAS_ENDPOINT,
    V2_OPERATIONAL_DASHBOARD_ENDPOINT,
    V2_PEOPLE_LIST_ENDPOINT,
    V2_PEOPLE_LISTS_ENDPOINT,
    V2_POI_ENDPOINT,
    V2_SMART_LIST_ENDPOINT,
    V2_SMART_LISTS_ENDPOINT,
    V2_STREAMING_TOKEN_ENDPOINT,
    V2_THUMBNAIL_ENDPOINT,
    V2_THUMBNAIL_LINK_ENDPOINT,
    V2_VIEWING_STATIONS_ENDPOINT,
)

RM = "pykada.verkada_requests.VerkadaRequestManager"
CAM = f"{V2_CAMERAS_ENDPOINT}/cam1"
T0 = "2025-07-17T20:00:00Z"
T1 = "2025-07-17T21:00:00Z"
DT0 = datetime(2025, 7, 17, 20, 0, tzinfo=timezone.utc)


# ---------- Request shape: (function, kwargs, http method, url, request kwargs) ----------

REQUEST_CASES = [
    # devices and sites
    (get_camera_data, {}, "get", V2_CAMERAS_ENDPOINT, {"params": {}}),
    (get_camera_data, {"site_ids": ["s1", "s2"], "limit": 50, "cursor": "c"}, "get",
     V2_CAMERAS_ENDPOINT, {"params": {"site_id": "s1,s2", "limit": 50, "cursor": "c"}}),
    (get_camera_sites, {"limit": 10}, "get", V2_CAMERA_SITES_ENDPOINT,
     {"params": {"limit": 10}}),
    # footage
    (get_footage_link, {"camera_id": "cam1", "timestamp": DT0}, "get",
     V2_FOOTAGE_LINK_ENDPOINT, {"params": {"camera_id": "cam1", "timestamp": T0}}),
    (get_footage_link, {"camera_id": "cam1"}, "get", V2_FOOTAGE_LINK_ENDPOINT,
     {"params": {"camera_id": "cam1"}}),
    (get_thumbnail_link, {"camera_id": "cam1", "timestamp": T0,
                          "expiry": timedelta(hours=2), "start_time": T0, "end_time": T1},
     "get", V2_THUMBNAIL_LINK_ENDPOINT,
     {"params": {"camera_id": "cam1", "timestamp": T0, "expiry": "PT2H",
                 "start_time": T0, "end_time": T1}}),
    # LPOI
    (create_lpoi, {"license_plate": "XYZ999", "description": "Stolen"}, "post",
     V2_LPOI_ENDPOINT, {"payload": {"license_plate": "XYZ999", "description": "Stolen"}}),
    (get_lpois, {"limit": 5000, "cursor": "c"}, "get", V2_LPOI_ENDPOINT,
     {"params": {"limit": 5000, "cursor": "c"}}),
    (update_lpoi, {"license_plate": "ABC 123", "description": "New"}, "patch",
     f"{V2_LPOI_ENDPOINT}/ABC%20123", {"payload": {"description": "New"}}),
    (delete_lpoi, {"license_plate": "ABC123"}, "delete", f"{V2_LPOI_ENDPOINT}/ABC123", {}),
    # LPR
    (get_seen_license_plates, {"camera_id": "cam1", "license_plate": "ABC", "start_time": T0,
                               "end_time": T1, "limit": 10, "cursor": "c"},
     "get", f"{CAM}/lpr/images",
     {"params": {"license_plate": "ABC", "start_time": T0, "end_time": T1,
                 "limit": 10, "cursor": "c"}}),
    (get_lpr_timestamps, {"camera_id": "cam1", "license_plate": "ABC123", "start_time": T0},
     "get", f"{CAM}/lpr/ABC123/timestamps", {"params": {"start_time": T0}}),
    (get_lpr_zones, {"limit": 200}, "get", V2_LPR_ZONES_ENDPOINT, {"params": {"limit": 200}}),
    (get_lpr_zone_metrics, {"zone_id": "z1", "start_time": T0, "end_time": DT0}, "get",
     f"{V2_LPR_ZONES_ENDPOINT}/z1/metrics", {"params": {"start_time": T0, "end_time": T0}}),
    (get_lpr_zone_records, {"zone_id": "z1", "vehicle_status": "still_in", "limit": 100},
     "get", f"{V2_LPR_ZONES_ENDPOINT}/z1/records",
     {"params": {"vehicle_status": "still_in", "limit": 100}}),
    (search_ncic_license_plates, {"start_time": T0, "end_time": T1, "license_plate": "*ABC*",
                                  "geo_fence": [(37.7, -122.4), (37.8, -122.4), (37.7, -122.3)],
                                  "limit": 1000},
     "post", V2_NCIC_PLATE_SEARCH_ENDPOINT,
     {"payload": {"start_time": T0, "end_time": T1, "license_plate": "*ABC*",
                  "geo_fence": [{"latitude": 37.7, "longitude": -122.4},
                                {"latitude": 37.8, "longitude": -122.4},
                                {"latitude": 37.7, "longitude": -122.3}],
                  "limit": 1000}}),
    # people
    (get_pois, {"limit": 20}, "get", V2_POI_ENDPOINT, {"params": {"limit": 20}}),
    (update_poi, {"person_id": "p1", "label": "New"}, "patch", f"{V2_POI_ENDPOINT}/p1",
     {"payload": {"label": "New"}}),
    (delete_poi, {"person_id": "p1"}, "delete", f"{V2_POI_ENDPOINT}/p1", {}),
    (get_people_lists, {"limit": 1000}, "get", V2_PEOPLE_LISTS_ENDPOINT,
     {"params": {"limit": 1000}}),
    (delete_people_list, {"list_id": "l1"}, "delete", f"{V2_PEOPLE_LIST_ENDPOINT}/l1", {}),
    (get_smart_lists, {}, "get", V2_SMART_LISTS_ENDPOINT, {"params": {}}),
    (delete_smart_list, {"list_id": "l1"}, "delete", f"{V2_SMART_LIST_ENDPOINT}/l1", {}),
    # analytics
    (get_object_counts, {"camera_id": "cam1", "start_time": T0, "end_time": T1, "limit": 5},
     "get", f"{CAM}/analytics/object_counts",
     {"params": {"start_time": T0, "end_time": T1, "limit": 5}}),
    (get_max_people_vehicle_counts, {"camera_id": "cam1", "start_time": T0,
                                     "search_zones": [[3, 3], [3, 4]]},
     "get", f"{CAM}/analytics/max_object_counts",
     {"params": {"start_time": T0, "search_zones": "[[3,3],[3,4]]"}}),
    (get_max_people_vehicle_counts, {"camera_id": "cam1"}, "get",
     f"{CAM}/analytics/max_object_counts", {"params": {}}),
    (get_occupancy_trends, {"camera_id": "cam1", "interval": "15_minutes",
                            "trend_type": "vehicle", "preset_id": "pr1"},
     "get", f"{CAM}/occupancy_trends",
     {"params": {"interval": "15_minutes", "type": "vehicle", "preset_id": "pr1"}}),
    (get_occupancy_trends, {"camera_id": "cam1"}, "get", f"{CAM}/occupancy_trends",
     {"params": {}}),
    (get_occupancy_trend_enabled_cameras, {"cursor": "c"}, "get",
     V2_OCCUPANCY_TRENDS_CAMERAS_ENDPOINT, {"params": {"cursor": "c"}}),
    (get_object_position_mqtt, {"camera_id": "cam1"}, "get",
     f"{V2_ANALYTICS_CAMERAS_ENDPOINT}/cam1/mqtt_configs", {}),
    (set_object_position_mqtt, {"camera_id": "cam1", "broker_host_port": "broker:443",
                                "broker_cert": "cert", "client_username": "u"},
     "put", f"{V2_ANALYTICS_CAMERAS_ENDPOINT}/cam1/mqtt_configs",
     {"payload": {"broker_host_port": "broker:443", "broker_cert": "cert",
                  "client_username": "u"}}),
    # dashboards
    (get_dashboards, {"limit": 5}, "get", V2_OPERATIONAL_DASHBOARD_ENDPOINT,
     {"params": {"limit": 5}}),
    (get_dashboard_occupancy_trend_data, {"dashboard_id": "d1", "start_time": T0,
                                          "interval": "PT15M"},
     "get", f"{V2_OPERATIONAL_DASHBOARD_ENDPOINT}/d1/occupancy_trends",
     {"params": {"start_time": T0, "interval": "PT15M"}}),
    (get_dashboard_widget_trends, {"dashboard_id": "d1", "start_time": DT0, "interval": "PT1D",
                                   "site_ids": ["s1"], "widget_types": ["occupancy", "queue"]},
     "post", f"{V2_OPERATIONAL_DASHBOARD_ENDPOINT}/d1/widget_trends/query",
     {"payload": {"start_time": T0, "interval": "PT1D", "site_ids": ["s1"],
                  "widget_types": ["occupancy", "queue"]}}),
    # cloud backup
    (get_cloud_backup_settings, {"camera_id": "cam1"}, "get",
     f"{CAM}/cloud_backup/settings", {}),
    # PTZ, audio, viewing stations
    (get_ptz_presets, {"camera_id": "cam1"}, "get", f"{CAM}/ptz/presets", {}),
    (move_camera_to_ptz_preset, {"camera_id": "cam1", "preset_id": "pr1"}, "post",
     f"{CAM}/ptz/position", {"payload": {"preset_id": "pr1"}}),
    (get_camera_audio_status, {"camera_id": "cam1"}, "get", f"{CAM}/audio", {}),
    (set_camera_audio_status, {"camera_id": "cam1", "enabled": False}, "post",
     f"{CAM}/audio", {"payload": {"enabled": False}}),
    (get_viewing_stations, {"limit": 50}, "get", V2_VIEWING_STATIONS_ENDPOINT,
     {"params": {"limit": 50}}),
]


@pytest.mark.parametrize("func, kwargs, method, url, request_kwargs", REQUEST_CASES,
                         ids=[f"{c[0].__name__}-{i}" for i, c in enumerate(REQUEST_CASES)])
def test_request_shape(func, kwargs, method, url, request_kwargs):
    with patch(f"{RM}.{method}", return_value={"ok": True}) as mock:
        result = func(**kwargs)
    assert result == {"ok": True}
    mock.assert_called_once_with(url, **request_kwargs)


# ---------- thumbnails (binary) ----------

@patch(f"{RM}.get_image", return_value=b"\xff\xd8\xff")
def test_get_historical_thumbnail(mock_get_image):
    assert get_historical_thumbnail("cam1", timestamp=T0, resolution="low-res",
                                    start_time=T0, end_time=T1) == b"\xff\xd8\xff"
    mock_get_image.assert_called_once_with(V2_THUMBNAIL_ENDPOINT, params={
        "camera_id": "cam1", "timestamp": T0, "resolution": "low-res",
        "start_time": T0, "end_time": T1,
    })


@patch(f"{RM}.get_image", return_value=b"\xff\xd8\xff")
def test_get_latest_thumbnail(mock_get_image):
    assert get_latest_thumbnail("cam1", resolution="hi-res") == b"\xff\xd8\xff"
    mock_get_image.assert_called_once_with(f"{CAM}/footage/thumbnails/latest",
                                           params={"resolution": "hi-res"})


def test_get_historical_thumbnail_window_needs_both_ends():
    with pytest.raises(ValueError, match="together"):
        get_historical_thumbnail("cam1", start_time=T0)


def test_get_historical_thumbnail_window_not_with_hi_res():
    with pytest.raises(ValueError, match="hi-res"):
        get_historical_thumbnail("cam1", resolution="hi-res", start_time=T0, end_time=T1)


def test_get_thumbnail_link_window_needs_both_ends():
    with pytest.raises(ValueError, match="together"):
        get_thumbnail_link("cam1", end_time=T1)


@pytest.mark.parametrize("resolution", ["high", "low", "HI-RES"])
def test_thumbnail_invalid_resolution(resolution):
    with pytest.raises(ValueError, match="resolution"):
        get_latest_thumbnail("cam1", resolution=resolution)


def test_get_thumbnail_link_invalid_expiry():
    with pytest.raises(ValueError, match="expiry"):
        get_thumbnail_link("cam1", expiry="1 day")


# ---------- streaming token ----------

def test_get_streaming_token_sends_api_key_header():
    tm = MagicMock()
    tm.api_key = "the-api-key"
    tm.get_token.return_value = "session"
    client = CamerasClient(token_manager=None, request_manager=None, api_key="k")
    client.request_manager.token_manager = tm
    with patch(f"{RM}.get", return_value={"jwt": "tok"}) as mock_get:
        assert client.get_streaming_token(exclude_accessible_resources=True) == {"jwt": "tok"}
    mock_get.assert_called_once_with(V2_STREAMING_TOKEN_ENDPOINT,
                                     headers={"x-api-key": "the-api-key"},
                                     params={"exclude_accessible_resources": True})


# ---------- validation ----------

@pytest.mark.parametrize("func, kwargs", [
    (get_footage_link, {"camera_id": ""}),
    (get_latest_thumbnail, {"camera_id": " "}),
    (get_seen_license_plates, {"camera_id": ""}),
    (get_lpr_timestamps, {"camera_id": "cam1", "license_plate": ""}),
    (get_object_counts, {"camera_id": ""}),
    (get_max_people_vehicle_counts, {"camera_id": ""}),
    (get_occupancy_trends, {"camera_id": ""}),
    (get_cloud_backup_settings, {"camera_id": ""}),
    (get_camera_audio_status, {"camera_id": ""}),
    (get_ptz_presets, {"camera_id": ""}),
    (move_camera_to_ptz_preset, {"camera_id": "cam1", "preset_id": ""}),
    (update_lpoi, {"license_plate": "", "description": "x"}),
    (delete_poi, {"person_id": ""}),
    (get_lpr_zone_metrics, {"zone_id": "", "start_time": T0, "end_time": T1}),
    (get_dashboard_widget_trends, {"dashboard_id": ""}),
    (get_dashboard_occupancy_trend_data, {"dashboard_id": ""}),
    (delete_people_list, {"list_id": ""}),
])
def test_empty_ids_raise(func, kwargs):
    with pytest.raises(ValueError):
        func(**kwargs)


@pytest.mark.parametrize("func, kwargs", [
    (get_footage_link, {"camera_id": "cam1", "timestamp": 1700000000}),
    (get_object_counts, {"camera_id": "cam1", "start_time": 1700000000}),
    (get_lpr_timestamps, {"camera_id": "cam1", "license_plate": "X", "start_time": "now"}),
    (delete_lpoi, {"license_plate": 123}),
    (create_lpoi, {"license_plate": None, "description": "Valid"}),
    (get_camera_data, {"site_ids": "s1,s2"}),
    (set_object_position_mqtt, {"camera_id": "cam1", "broker_host_port": "h:443",
                                "broker_cert": None}),
])
def test_type_and_format_errors(func, kwargs):
    with pytest.raises((TypeCheckError, ValueError)):
        func(**kwargs)


@pytest.mark.parametrize("func, kwargs, match", [
    (get_camera_data, {"limit": 201}, "between 1 and 200"),
    (get_lpois, {"limit": 10001}, "between 1 and 10000"),
    (get_lpr_zone_records, {"zone_id": "z1", "limit": 101}, "between 1 and 100"),
    (search_ncic_license_plates, {"start_time": T0, "end_time": T1, "limit": 1001},
     "between 1 and 1000"),
    (get_people_lists, {"limit": 0}, "between 1 and 1000"),
])
def test_limits(func, kwargs, match):
    with pytest.raises(ValueError, match=match):
        func(**kwargs)


def test_create_lpoi_too_long():
    with pytest.raises(ValueError, match="11 characters"):
        create_lpoi("ABCDEFGHIJKL", "x")


@pytest.mark.parametrize("interval", ["1_hour", "15_minutes", "1_day"])
@patch(f"{RM}.get", return_value={})
def test_occupancy_trends_valid_intervals(mock_get, interval):
    get_occupancy_trends("cam1", interval=interval)


@pytest.mark.parametrize("kwargs, match", [
    ({"interval": "6_hours"}, "interval"),
    ({"interval": "PT1H"}, "interval"),
    ({"trend_type": "bicycle"}, "trend_type"),
])
def test_occupancy_trends_invalid_choices(kwargs, match):
    with pytest.raises(ValueError, match=match):
        get_occupancy_trends("cam1", **kwargs)


@pytest.mark.parametrize("func, kwargs", [
    (get_dashboard_occupancy_trend_data, {"dashboard_id": "d1", "interval": "1_hour"}),
    (get_dashboard_widget_trends, {"dashboard_id": "d1", "interval": "1_hour"}),
    (get_dashboard_widget_trends, {"dashboard_id": "d1", "widget_types": ["pie"]}),
])
def test_dashboard_invalid_choices(func, kwargs):
    with pytest.raises(ValueError):
        func(**kwargs)


def test_max_counts_end_time_requires_start_time():
    with pytest.raises(ValueError, match="start_time"):
        get_max_people_vehicle_counts("cam1", end_time=T1)


def test_lpr_zone_records_invalid_status():
    with pytest.raises(ValueError, match="vehicle_status"):
        get_lpr_zone_records("z1", vehicle_status="parked")


def test_lpr_zone_records_generator_validates_status_eagerly():
    with pytest.raises(ValueError, match="vehicle_status"):
        get_all_lpr_zone_records("z1", vehicle_status="parked")


@pytest.mark.parametrize("points", [2, 701])
def test_ncic_geo_fence_size(points):
    with pytest.raises(ValueError, match="geo_fence"):
        search_ncic_license_plates(T0, T1, geo_fence=[(0.0, 0.0)] * points)


# ---------- persons of interest ----------

@patch(f"{RM}.post", return_value={"person_id": "p1"})
def test_create_poi_encodes_image(mock_post, tmp_path):
    image = tmp_path / "face.jpg"
    image.write_bytes(b"fake-image-bytes")
    assert create_poi(str(image), "Suspect") == {"person_id": "p1"}
    mock_post.assert_called_once_with(V2_POI_ENDPOINT, payload={
        "base64_image": "ZmFrZS1pbWFnZS1ieXRlcw==", "label": "Suspect",
    })


def test_create_poi_missing_file():
    with pytest.raises(FileNotFoundError):
        create_poi("/no/such/face.jpg", "Suspect")


def test_update_poi_empty_label():
    with pytest.raises(ValueError, match="label"):
        update_poi("p1", "")


# ---------- bulk LPOIs (v1) ----------

@patch(f"{RM}.post", return_value={"addedMs": 1})
def test_create_bulk_lpois(mock_post, tmp_path):
    csv_file = tmp_path / "plates.csv"
    csv_file.write_text("License Plate,Name\nABC123,Car\n")
    assert create_bulk_lpois(str(csv_file)) == {"addedMs": 1}
    url = mock_post.call_args.args[0]
    files = mock_post.call_args.kwargs["files"]
    assert url == LPOI_BATCH_ENDPOINT
    assert files["file"][0] == str(csv_file) and files["file"][2] == "text/csv"


@patch(f"{RM}.delete", return_value={"addedMs": 1})
def test_delete_bulk_lpois(mock_delete, tmp_path):
    csv_file = tmp_path / "plates.csv"
    csv_file.write_text("License Plate\nABC123\n")
    assert delete_bulk_lpois(str(csv_file)) == {"addedMs": 1}
    assert mock_delete.call_args.args[0] == LPOI_BATCH_ENDPOINT


def test_create_bulk_lpois_wrong_columns(tmp_path):
    csv_file = tmp_path / "plates.csv"
    csv_file.write_text("Plate,Name\nABC123,Car\n")
    with pytest.raises(ValueError, match="column"):
        create_bulk_lpois(str(csv_file))


# ---------- cloud backup ----------

FULL_BACKUP = dict(
    enabled=True, video_to_upload="MOTION", video_quality="HIGH_QUALITY",
    backup_days=["Monday", "Friday"], backup_window=("00:00:00", "24:00:00"),
    upload_window=(time(1, 0), time(5, 30)),
)
FULL_BACKUP_BODY = {
    "enabled": True, "video_to_upload": "MOTION", "video_quality": "HIGH_QUALITY",
    "backup_days": ["Monday", "Friday"],
    "backup_window": {"start_time": "00:00:00", "end_time": "24:00:00"},
    "upload_window": {"start_time": "01:00:00", "end_time": "05:30:00"},
}


@patch(f"{RM}.put", return_value={"camera_id": "cam1"})
def test_replace_cloud_backup_settings(mock_put):
    replace_cloud_backup_settings("cam1", **FULL_BACKUP)
    mock_put.assert_called_once_with(f"{CAM}/cloud_backup/settings", payload=FULL_BACKUP_BODY)


@patch(f"{RM}.put", return_value={})
def test_replace_cloud_backup_settings_empty_days_allowed(mock_put):
    replace_cloud_backup_settings("cam1", **{**FULL_BACKUP, "backup_days": []})
    assert mock_put.call_args.kwargs["payload"]["backup_days"] == []


def test_replace_cloud_backup_settings_requires_all_fields():
    with pytest.raises(TypeError):
        replace_cloud_backup_settings("cam1", enabled=True)


@patch(f"{RM}.patch", return_value={"camera_id": "cam1"})
def test_update_cloud_backup_settings_partial(mock_patch):
    update_cloud_backup_settings("cam1", enabled=False)
    mock_patch.assert_called_once_with(f"{CAM}/cloud_backup/settings",
                                       payload={"enabled": False})


@patch(f"{RM}.patch", return_value={})
def test_update_cloud_backup_settings_window_only(mock_patch):
    update_cloud_backup_settings("cam1", upload_window=("22:00:00", "23:59:59"))
    assert mock_patch.call_args.kwargs["payload"] == {
        "upload_window": {"start_time": "22:00:00", "end_time": "23:59:59"}}


def test_update_cloud_backup_settings_requires_a_field():
    with pytest.raises(ValueError, match="At least one"):
        update_cloud_backup_settings("cam1")


@pytest.mark.parametrize("kwargs, match", [
    ({"video_quality": "ULTRA_QUALITY"}, "video_quality"),
    ({"video_to_upload": "PARTIAL"}, "video_to_upload"),
    ({"backup_days": ["MO"]}, "backup_days"),
    ({"backup_days": ["monday"]}, "backup_days"),
    ({"backup_window": ("1:00:00", "05:00:00")}, "backup_window start"),
    ({"backup_window": ("01:00", "05:00")}, "HH:MM:SS"),
    ({"upload_window": ("05:00:00", "01:00:00")}, "end after it starts"),
    ({"upload_window": ("05:00:00", "05:00:00")}, "end after it starts"),
    ({"backup_window": ("00:00:00", "25:00:00")}, "backup_window end"),
])
def test_cloud_backup_validation(kwargs, match):
    with pytest.raises(ValueError, match=match):
        update_cloud_backup_settings("cam1", **kwargs)


def test_cloud_backup_window_must_be_pair():
    with pytest.raises(TypeCheckError):
        update_cloud_backup_settings("cam1", backup_window="01:00:00-05:00:00")


# ---------- pagination generators ----------

@pytest.mark.parametrize("gen_func, kwargs, page_func_url", [
    (get_all_camera_data, {"site_ids": ["s1"]}, V2_CAMERAS_ENDPOINT),
    (get_all_camera_sites, {}, V2_CAMERA_SITES_ENDPOINT),
    (get_all_lpois, {}, V2_LPOI_ENDPOINT),
    (get_all_seen_license_plates, {"camera_id": "cam1"}, f"{CAM}/lpr/images"),
    (get_all_lpr_timestamps, {"camera_id": "cam1", "license_plate": "ABC"},
     f"{CAM}/lpr/ABC/timestamps"),
    (get_all_lpr_zones, {}, V2_LPR_ZONES_ENDPOINT),
    (get_all_lpr_zone_records, {"zone_id": "z1"}, f"{V2_LPR_ZONES_ENDPOINT}/z1/records"),
    (get_all_pois, {}, V2_POI_ENDPOINT),
    (get_all_people_lists, {}, V2_PEOPLE_LISTS_ENDPOINT),
    (get_all_smart_lists, {}, V2_SMART_LISTS_ENDPOINT),
    (get_all_object_counts, {"camera_id": "cam1"}, f"{CAM}/analytics/object_counts"),
    (get_all_occupancy_trend_enabled_cameras, {}, V2_OCCUPANCY_TRENDS_CAMERAS_ENDPOINT),
    (get_all_dashboards, {}, V2_OPERATIONAL_DASHBOARD_ENDPOINT),
    (get_all_viewing_stations, {}, V2_VIEWING_STATIONS_ENDPOINT),
])
def test_get_all_walks_cursor_pages(gen_func, kwargs, page_func_url):
    with patch(f"{RM}.get") as mock_get:
        mock_get.side_effect = [{"items": [1, 2], "cursor": "c1"},
                                {"items": [3], "cursor": None}]
        result = gen_func(**kwargs)
        assert isinstance(result, types.GeneratorType)
        assert list(result) == [1, 2, 3]
    assert [c.args[0] for c in mock_get.call_args_list] == [page_func_url] * 2
    assert mock_get.call_args_list[1].kwargs["params"]["cursor"] == "c1"


@patch(f"{RM}.post")
def test_search_all_ncic_walks_body_cursor(mock_post):
    mock_post.side_effect = [{"items": ["r1"], "cursor": "c1"},
                             {"items": ["r2"], "cursor": None}]
    assert list(search_all_ncic_license_plates(T0, T1, license_plate="ABC*")) == ["r1", "r2"]
    second = mock_post.call_args_list[1].kwargs["payload"]
    assert second["cursor"] == "c1" and second["license_plate"] == "ABC*"


@patch(f"{RM}.get", return_value={"items": [], "cursor": None})
def test_get_all_lpois_uses_large_default_page(mock_get):
    list(get_all_lpois())
    assert mock_get.call_args.kwargs["params"]["limit"] == 1000
