import types
from unittest.mock import patch

import pytest

from pykada.access_control import (
    add_access_schedule_event_to_access_level,
    build_access_schedule_event,
    create_access_level,
    delete_access_level,
    delete_access_schedule_event_on_access_level,
    get_access_level,
    get_access_levels,
    get_access_schedule_event,
    get_all_access_levels,
    update_access_level,
    update_access_schedule_event_on_access_level,
)
from pykada.endpoints import V2_ACCESS_LEVELS_ENDPOINT as LEVELS

RM = "pykada.verkada_requests.VerkadaRequestManager"
EVENTS = f"{LEVELS}/al1/access_schedule_events"


def weekly(day, start, end):
    return {"recurrence_rule": {"frequency": "WEEKLY", "interval": 1, "by_day": [day]},
            "start_time": start, "end_time": end}


@pytest.mark.parametrize("func, kwargs, method, url, request_kwargs", [
    (get_access_levels, {"limit": 1000}, "get", LEVELS, {"params": {"limit": 1000}}),
    (get_access_level, {"access_level_id": "al1"}, "get", f"{LEVELS}/al1", {}),
    (create_access_level, {
        "name": "Staff", "sites": ["s1"], "access_groups": ["g1"], "doors": ["d1"],
        "access_schedule_events": [
            {"weekday": "Monday", "start_time": "09:00", "end_time": "17:00"},
            {"weekday": "Saturday", "start_time": "10:00", "end_time": "12:00"},
        ]},
     "post", LEVELS,
     {"payload": {"name": "Staff", "sites": ["s1"], "access_groups": ["g1"], "doors": ["d1"],
                  "access_schedule_events": [weekly("Monday", "09:00", "17:00"),
                                             weekly("Saturday", "10:00", "12:00")]}}),
    (update_access_level, {"access_level_id": "al1", "doors": ["d1", "d2"]}, "patch",
     f"{LEVELS}/al1", {"payload": {"doors": ["d1", "d2"]}}),
    (update_access_level, {"access_level_id": "al1", "name": "New", "access_groups": []},
     "patch", f"{LEVELS}/al1", {"payload": {"name": "New", "access_groups": []}}),
    (delete_access_level, {"access_level_id": "al1"}, "delete", f"{LEVELS}/al1", {}),
    (add_access_schedule_event_to_access_level, {"access_level_id": "al1",
                                                 "weekday": "Friday", "start_time": "08:00",
                                                 "end_time": "18:00"},
     "post", EVENTS, {"payload": weekly("Friday", "08:00", "18:00")}),
    (get_access_schedule_event, {"access_level_id": "al1", "event_id": "ev1"}, "get",
     f"{EVENTS}/ev1", {}),
    (update_access_schedule_event_on_access_level, {"access_level_id": "al1",
                                                    "event_id": "ev1", "end_time": "19:00"},
     "patch", f"{EVENTS}/ev1", {"payload": {"end_time": "19:00"}}),
    (update_access_schedule_event_on_access_level, {"access_level_id": "al1",
                                                    "event_id": "ev1", "weekday": "Sunday"},
     "patch", f"{EVENTS}/ev1",
     {"payload": {"recurrence_rule": {"frequency": "WEEKLY", "interval": 1,
                                      "by_day": ["Sunday"]}}}),
    (delete_access_schedule_event_on_access_level, {"access_level_id": "al1",
                                                    "event_id": "ev1"},
     "delete", f"{EVENTS}/ev1", {}),
])
def test_request_shape(func, kwargs, method, url, request_kwargs):
    with patch(f"{RM}.{method}", return_value={"ok": True}) as mock:
        assert func(**kwargs) == {"ok": True}
    mock.assert_called_once_with(url, **request_kwargs)


@patch(f"{RM}.get")
def test_get_all_access_levels_walks_pages(mock_get):
    mock_get.side_effect = [{"items": [{"access_level_id": "a"}], "cursor": "c1"},
                            {"items": [{"access_level_id": "b"}], "cursor": None}]
    result = get_all_access_levels()
    assert isinstance(result, types.GeneratorType)
    assert [lvl["access_level_id"] for lvl in result] == ["a", "b"]


def test_build_access_schedule_event():
    assert build_access_schedule_event("Tuesday", "07:30", "07:31") == \
        weekly("Tuesday", "07:30", "07:31")


@pytest.mark.parametrize("args, match", [
    (("TU", "07:00", "08:00"), "weekday"),
    (("tuesday", "07:00", "08:00"), "weekday"),
    (("Tuesday", "7:00", "08:00"), "start_time"),
    (("Tuesday", "07:00", "24:00"), "end_time"),
    (("Tuesday", "08:00", "08:00"), "after"),
    (("Tuesday", "09:00", "08:00"), "after"),
])
def test_build_access_schedule_event_validation(args, match):
    with pytest.raises(ValueError, match=match):
        build_access_schedule_event(*args)


@pytest.mark.parametrize("call, match", [
    (lambda: create_access_level("", ["s1"], [], [], []), "name"),
    (lambda: create_access_level("L", [], [], [], []), "sites"),
    (lambda: create_access_level("L", ["s1"], [], [],
                                 [{"weekday": "Monday", "start_time": "09:00"}]),
     r"access_schedule_events\[0\] is missing \['end_time'\]"),
    (lambda: update_access_level("al1"), "At least one"),
    (lambda: update_access_level("al1", sites=[]), "sites"),
    (lambda: update_access_level("", name="x"), "access_level_id"),
    (lambda: add_access_schedule_event_to_access_level("al1", "MO", "09:00", "10:00"),
     "weekday"),
    (lambda: update_access_schedule_event_on_access_level("al1", "ev1"), "At least one"),
    (lambda: update_access_schedule_event_on_access_level("al1", "ev1", start_time="10:00",
                                                          end_time="09:00"), "after"),
    (lambda: update_access_schedule_event_on_access_level("al1", "", start_time="10:00"),
     "event_id"),
    (lambda: get_access_levels(limit=1001), "between 1 and 1000"),
])
def test_validation(call, match):
    with pytest.raises(ValueError, match=match):
        call()


def test_update_access_level_cannot_change_schedule_events():
    with pytest.raises(TypeError):
        update_access_level("al1", access_schedule_events=[])
