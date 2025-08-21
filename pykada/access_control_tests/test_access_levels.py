import pytest
from typeguard import TypeCheckError
from unittest.mock import patch

# Replace 'access_levels' with the actual module name.
import access_levels as al
from access_levels import (
    is_valid_time,
)
from pykada.access_control import get_all_access_levels, \
    get_access_level, create_access_level, update_access_level, \
    delete_access_level, add_access_schedule_event_to_access_level, \
    update_access_schedule_event_on_access_level, \
    delete_access_schedule_event_on_access_level
from pykada.enums import WEEKDAY_ENUM


# --- is_valid_time --- #

@pytest.mark.parametrize("time_str, expected", [
    ("00:00", True),
    ("23:59", True),
    ("12:34", True),
    ("24:00", False),
    ("12:60", False),
    ("9:00", False),
    ("09:0", False),
    ("ab:cd", False),
])
def test_is_valid_time(time_str, expected):
    assert is_valid_time(time_str) is expected


# --- get_all_access_levels --- #

@patch("access_levels.get_request", return_value={"levels": []})
def test_get_all_access_levels(mock_get):
    result = get_all_access_levels()
    mock_get.assert_called_once_with(al.ACCESS_LEVEL_ENDPOINT)
    assert result == {"levels": []}


# --- get_access_level --- #

def test_get_access_level_empty_id_raises_value():
    with pytest.raises(ValueError):
        get_access_level("")

def test_get_access_level_none_id_raises_type_error():
    with pytest.raises(TypeCheckError):
        get_access_level(None)

@patch("access_levels.get_request", return_value={"level": {"id": "lvl1"}})
def test_get_access_level_success(mock_get):
    result = get_access_level("lvl1")
    expected_url = f"{al.ACCESS_LEVEL_ENDPOINT}/lvl1"
    mock_get.assert_called_once_with(expected_url)
    assert result == {"level": {"id": "lvl1"}}


# --- create_access_level --- #

def test_create_access_level_empty_name_raises_value():
    with pytest.raises(ValueError):
        create_access_level(["g1"], [], ["d1"], "", ["s1"])

def test_create_access_level_none_name_raises_type_error():
    with pytest.raises(TypeCheckError):
        create_access_level(["g1"], [], ["d1"], None, ["s1"])

@patch("access_levels.post_request", return_value={"created": True})
def test_create_access_level_success(mock_post):
    groups = ["g1"]
    events = [{"access_schedule_event_id": "e1", "door_status": "access_granted", "start_time": "09:00", "end_time": "17:00", "weekday": WEEKDAY_ENUM["MONDAY"]}]
    doors = ["d1"]
    name = "LevelName"
    sites = ["s1"]
    result = create_access_level(groups, events, doors, name, sites)
    mock_post.assert_called_once_with(
        al.ACCESS_LEVEL_ENDPOINT,
        payload={"access_groups": groups, "access_schedule_events": events, "doors": doors, "name": name, "sites": sites}
    )
    assert result == {"created": True}


# --- update_access_level --- #

def test_update_access_level_empty_id_raises_value():
    with pytest.raises(ValueError):
        update_access_level("", ["g"], [], ["d"], "name", ["s"])

def test_update_access_level_none_id_raises_type_error():
    with pytest.raises(TypeCheckError):
        update_access_level(None, ["g"], [], ["d"], "name", ["s"])

def test_update_access_level_empty_name_raises_value():
    with pytest.raises(ValueError):
        update_access_level("lvl1", ["g"], [], ["d"], "", ["s"])

@patch("access_levels.put_request", return_value={"updated": True})
def test_update_access_level_success(mock_put):
    lvl_id = "lvl1"
    groups = ["g1"]
    events = []
    doors = ["d1"]
    name = "NewName"
    sites = ["s1"]
    result = update_access_level(lvl_id, groups, events, doors, name, sites)
    expected_url = f"{al.ACCESS_LEVEL_ENDPOINT}/{lvl_id}"
    mock_put.assert_called_once_with(
        expected_url,
        payload={"access_groups": groups, "access_schedule_events": events, "doors": doors, "name": name, "sites": sites}
    )
    assert result == {"updated": True}


# --- delete_access_level --- #

def test_delete_access_level_empty_id_raises_value():
    with pytest.raises(ValueError):
        delete_access_level("")

def test_delete_access_level_none_id_raises_type_error():
    with pytest.raises(TypeCheckError):
        delete_access_level(None)

@patch("access_levels.delete_request", return_value={"deleted": True})
def test_delete_access_level_success(mock_delete):
    lvl_id = "lvl1"
    result = delete_access_level(lvl_id)
    expected_url = f"{al.ACCESS_LEVEL_ENDPOINT}/{lvl_id}"
    mock_delete.assert_called_once_with(expected_url, params={"access_level_id": lvl_id})
    assert result == {"deleted": True}


# --- add_access_schedule_event_to_access_level --- #

def test_add_event_empty_level_id_raises_value():
    with pytest.raises(ValueError):
        add_access_schedule_event_to_access_level("", "09:00", "17:00", WEEKDAY_ENUM["TUESDAY"])

@patch("access_levels.is_valid_time", return_value=False)
def test_add_event_bad_time_raises_value(mock_time):
    with pytest.raises(ValueError):
        add_access_schedule_event_to_access_level("lvl1", "9:00", "17:00", WEEKDAY_ENUM["TUESDAY"])

def test_add_event_invalid_weekday_raises_value():
    with pytest.raises(ValueError):
        add_access_schedule_event_to_access_level("lvl1", "09:00", "17:00", "XU")

@patch("access_levels.post_request", return_value={"event_created": True})
def test_add_event_success(mock_post):
    lvl_id = "lvl1"
    st, et, wd = "08:00", "18:00", WEEKDAY_ENUM["WEDNESDAY"]
    result = add_access_schedule_event_to_access_level(lvl_id, st, et, wd)
    expected_url = f"{al.ACCESS_LEVEL_ENDPOINT}/{lvl_id}/access_schedule_event"
    mock_post.assert_called_once_with(expected_url, payload={"door_status": "access_granted", "start_time": st, "end_time": et, "weekday": wd})
    assert result == {"event_created": True}


# --- update_access_schedule_event_on_access_level --- #

def test_update_event_empty_ids_raises_value():
    with pytest.raises(ValueError):
        update_access_schedule_event_on_access_level("", "eid", "09:00", "17:00", WEEKDAY_ENUM["FRIDAY"])
    with pytest.raises(ValueError):
        update_access_schedule_event_on_access_level("lvl1", "", "09:00", "17:00", WEEKDAY_ENUM["FRIDAY"])

@patch("access_levels.is_valid_time", return_value=False)
def test_update_event_bad_time_raises_value(mock_time):
    with pytest.raises(ValueError):
        update_access_schedule_event_on_access_level("lvl1", "eid", "9:00", "17:00", WEEKDAY_ENUM["FRIDAY"])

def test_update_event_invalid_weekday_raises_value():
    with pytest.raises(ValueError):
        update_access_schedule_event_on_access_level("lvl1", "eid", "09:00", "17:00", "XX")

@patch("access_levels.put_request", return_value={"event_updated": True})
def test_update_event_success(mock_put):
    lvl_id, eid = "lvl1", "eid"
    st, et, wd = "07:00", "19:00", WEEKDAY_ENUM["THURSDAY"]
    result = update_access_schedule_event_on_access_level(lvl_id, eid, st, et, wd)
    expected_url = f"{al.ACCESS_LEVEL_ENDPOINT}/{lvl_id}/access_schedule_event/{eid}"
    mock_put.assert_called_once_with(expected_url, payload={"door_status": "access_granted", "start_time": st, "end_time": et, "weekday": wd})
    assert result == {"event_updated": True}


# --- delete_access_schedule_event_on_access_level --- #

def test_delete_event_empty_ids_raises_value():
    with pytest.raises(ValueError):
        delete_access_schedule_event_on_access_level("", "eid")
    with pytest.raises(ValueError):
        delete_access_schedule_event_on_access_level("lvl1", "")

@patch("access_levels.delete_request", return_value={"event_deleted": True})
def test_delete_event_success(mock_del):
    lvl_id, eid = "lvl1", "eid"
    result = delete_access_schedule_event_on_access_level(lvl_id, eid)
    expected_url = f"{al.ACCESS_LEVEL_ENDPOINT}/{lvl_id}/access_schedule_event/{eid}"
    mock_del.assert_called_once_with(expected_url)
    assert result == {"event_deleted": True}

