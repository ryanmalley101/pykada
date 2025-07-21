import pytest
from unittest.mock import patch

from typeguard import TypeCheckError

import access_door_exceptions as de
from access_door_exceptions import *
from pykada.helpers import DOOR_STATUS_ENUM, FREQUENCY_ENUM, WEEKDAY_ENUM


# A minimal valid exception for reuse
def minimal_exc(**overrides):
    exc = {
        "date": "2025-05-01",
        "door_status": DOOR_STATUS_ENUM["ACCESS_CONTROLLED"],
        "start_time": "09:00",
        "end_time": "17:00",
    }
    exc.update(overrides)
    return exc


# ———— create_door_exception_calendar ———— #

def test_create_calendar_empty_doors_raises():
    with pytest.raises(ValueError):
        create_door_exception_calendar([], [], "My Cal")

def test_create_calendar_door_empty_string_raises():
    with pytest.raises(ValueError):
        create_door_exception_calendar(["", "door2"], [], "My Cal")

def test_create_calendar_empty_name_raises():
    with pytest.raises(ValueError):
        create_door_exception_calendar(["door1"], [], "")

def test_create_calendar_invalid_exception_missing_fields():
    # missing date
    bad_exc = {"door_status": DOOR_STATUS_ENUM["ACCESS_CONTROLLED"]}
    with pytest.raises(ValueError):
        create_door_exception_calendar(["door1"], [bad_exc], "Cal")

def test_create_calendar_all_day_default_constraints():
    # all_day_default true but wrong door_status
    exc = minimal_exc(all_day_default=True, door_status="UNLOCKED")
    with pytest.raises(ValueError):
        create_door_exception_calendar(["door1"], [exc], "Cal")

    # all_day_default true but provided start_time/end_time
    exc = minimal_exc(all_day_default=True)
    exc["start_time"] = "10:00"
    with pytest.raises(ValueError):
        create_door_exception_calendar(["door1"], [exc], "Cal")

def test_create_calendar_double_badge_requires_group_ids():
    exc = minimal_exc(double_badge=True)
    # no group ids
    with pytest.raises(ValueError):
        create_door_exception_calendar(["door1"], [exc], "Cal")

    # group ids present but double_badge false
    exc2 = minimal_exc(double_badge_group_ids=["g1"])
    with pytest.raises(ValueError):
        create_door_exception_calendar(["door1"], [exc2], "Cal")

def test_create_calendar_first_person_in_requires_group_ids():
    exc = minimal_exc(first_person_in=True)
    with pytest.raises(ValueError):
        create_door_exception_calendar(["door1"], [exc], "Cal")

    # valid first_person_in scenario
    valid = minimal_exc(
        door_status="CARD_AND_CODE",
        first_person_in=True,
        first_person_in_group_ids=["sup1"]
    )
    with patch("access_door_exceptions.post_request", return_value={"ok": True}) as mock_post:
        res = create_door_exception_calendar(["door1"], [valid], "Cal")
        mock_post.assert_called_once_with(
            de.ACCESS_DOOR_EXCEPTIONS_ENDPOINT,
            payload={"doors": ["door1"], "exceptions": [valid], "name": "Cal"}
        )
        assert res == {"ok": True}

def test_create_calendar_with_recurrence_rule():
    rr = {"frequency": "DAILY", "interval": 1, "start_time": "08:00"}
    valid = minimal_exc(recurrence_rule=rr)
    with patch("access_door_exceptions.post_request", return_value={"ok": True}) as mock_post:
        res = create_door_exception_calendar(["door1"], [valid], "Cal")
        mock_post.assert_called_once()
        assert res == {"ok": True}


# ———— update_door_exception_calendar ———— #

def test_update_calendar_empty_doors_raises():
    with pytest.raises(ValueError):
        update_door_exception_calendar([], [], "Cal", calendar_id="cid")

def test_update_calendar_empty_name_raises():
    with pytest.raises(ValueError):
        update_door_exception_calendar(["door1"], [], "", calendar_id="cid")

def test_update_calendar_invalid_exception_propagates():
    # re-use missing-field exception
    bad = [{"door_status": DOOR_STATUS_ENUM["ACCESS_CONTROLLED"]}]
    with pytest.raises(ValueError):
        update_door_exception_calendar(["door1"], bad, "Cal", calendar_id="cid")

@patch("access_door_exceptions.put_request", return_value={"updated": True})
def test_update_calendar_success(mock_put):
    doors = ["door1", "door2"]
    excs = [ minimal_exc() ]
    name = "Updated Cal"
    cal_id = "calendar123"
    res = update_door_exception_calendar(doors, excs, name, calendar_id=cal_id)
    mock_put.assert_called_once_with(
        de.ACCESS_DOOR_EXCEPTIONS_ENDPOINT,
        payload={"doors": doors, "exceptions": excs, "name": name},
        params={"calendar_id": cal_id}
    )
    assert res == {"updated": True}

def base_rr(**overrides):
    """
    Return a minimal valid daily recurrence rule.
    """
    rr = {
        "frequency": FREQUENCY_ENUM["DAILY"],
        "interval": 1,
        "start_time": "08:00"
    }
    rr.update(overrides)
    return rr


# --- VALID CASES --- #

def test_daily_minimal_valid():
    validate_recurrence_rule(base_rr())


def test_weekly_with_by_day_valid():
    rr = base_rr(
        frequency=FREQUENCY_ENUM["WEEKLY"],
        by_day=[WEEKDAY_ENUM["MONDAY"], WEEKDAY_ENUM["WEDNESDAY"]]
    )
    validate_recurrence_rule(rr)


def test_monthly_with_by_month_day_valid():
    rr = base_rr(
        frequency=FREQUENCY_ENUM["MONTHLY"],
        by_month_day=15
    )
    validate_recurrence_rule(rr)


def test_monthly_with_by_day_and_set_pos_valid():
    rr = base_rr(
        frequency=FREQUENCY_ENUM["MONTHLY"],
        by_day=[WEEKDAY_ENUM["TUESDAY"]],
        by_set_pos=3
    )
    validate_recurrence_rule(rr)


def test_yearly_with_by_month_and_by_month_day_valid():
    rr = base_rr(
        frequency=FREQUENCY_ENUM["YEARLY"],
        by_month=12,
        by_month_day=25
    )
    validate_recurrence_rule(rr)


def test_yearly_with_by_month_and_set_pos_valid():
    rr = base_rr(
        frequency=FREQUENCY_ENUM["YEARLY"],
        by_month=11,
        by_day=[WEEKDAY_ENUM["FRIDAY"]],
        by_set_pos=4
    )
    validate_recurrence_rule(rr)


def test_excluded_dates_valid():
    rr = base_rr(
        excluded_dates=["2023-01-01", "2023-12-31"]
    )
    validate_recurrence_rule(rr)


def test_until_valid():
    rr = base_rr(until="2024-06-30")
    validate_recurrence_rule(rr)


def test_count_valid():
    rr = base_rr(count=5)
    validate_recurrence_rule(rr)


# --- INVALID CASES --- #

def test_missing_interval():
    rr = {"frequency": FREQUENCY_ENUM["DAILY"], "start_time": "08:00"}
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_interval_not_int():
    rr = base_rr(interval="one")
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_missing_start_time():
    rr = {"frequency": FREQUENCY_ENUM["DAILY"], "interval": 1}
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_bad_start_time_format():
    rr = base_rr(start_time="8:00")
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_by_day_not_supported_for_daily():
    rr = base_rr(by_day=[WEEKDAY_ENUM["SUNDAY"]])
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_by_day_wrong_type():
    rr = base_rr(
        frequency=FREQUENCY_ENUM["WEEKLY"],
        by_day="MO"
    )
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_by_day_empty_for_weekly():
    rr = base_rr(
        frequency=FREQUENCY_ENUM["WEEKLY"],
        by_day=[]
    )
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_by_day_invalid_values():
    rr = base_rr(
        frequency=FREQUENCY_ENUM["WEEKLY"],
        by_day=["XX"]
    )
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_by_month_non_yearly():
    rr = base_rr(
        frequency=FREQUENCY_ENUM["MONTHLY"],
        by_month=7
    )
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_by_month_out_of_range():
    rr = base_rr(
        frequency=FREQUENCY_ENUM["YEARLY"],
        by_month=13
    )
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_by_month_day_non_monthly_yearly():
    rr = base_rr(
        frequency=FREQUENCY_ENUM["DAILY"],
        by_month_day=10
    )
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_by_month_day_with_set_pos_error():
    rr = base_rr(
        frequency=FREQUENCY_ENUM["MONTHLY"],
        by_month_day=10,
        by_set_pos=1
    )
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_by_month_day_out_of_range():
    rr = base_rr(
        frequency=FREQUENCY_ENUM["MONTHLY"],
        by_month_day=0
    )
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_by_set_pos_non_monthly_yearly():
    rr = base_rr(
        frequency=FREQUENCY_ENUM["DAILY"],
        by_set_pos=2
    )
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_by_set_pos_out_of_range():
    rr = base_rr(
        frequency=FREQUENCY_ENUM["MONTHLY"],
        by_day=[WEEKDAY_ENUM["MONDAY"]],
        by_set_pos=6
    )
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_excluded_dates_invalid_format():
    rr = base_rr(
        excluded_dates=["2023-01-01", "01-01-2023"]
    )
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_until_invalid_format():
    rr = base_rr(until="2023/12/31")
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_both_count_and_until():
    rr = base_rr(count=3, until="2025-01-01")
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)

#
#
# # Minimal valid exception for payloads
# minimal_exc = {
#     "date": "2025-01-01",
#     "door_status": DOOR_STATUS_ENUM["ACCESS_CONTROLLED"],
#     "start_time": "09:00",
#     "end_time": "17:00"
# }


# 1. TypeCheckError for wrong-typed parameters

def test_get_all_door_exception_calendars_type_error():
    with pytest.raises(TypeCheckError):
        get_all_door_exception_calendars(last_updated_at="not-an-int")


def test_get_door_exception_calendar_type_error():
    with pytest.raises(TypeCheckError):
        get_door_exception_calendar(None)  # calendar_id must be str


def test_create_door_exception_calendar_type_error():
    with pytest.raises(TypeCheckError):
        create_door_exception_calendar("not-a-list", [], "Name")


def test_update_door_exception_calendar_type_error():
    with pytest.raises(TypeCheckError):
        update_door_exception_calendar([], [], "Name", calendar_id=None)


def test_delete_door_exception_calendar_type_error():
    with pytest.raises(TypeCheckError):
        delete_door_exception_calendar(123)  # calendar_id must be str


def test_get_exception_on_door_exception_calendar_type_error():
    with pytest.raises(TypeCheckError):
        get_exception_on_door_exception_calendar("cid", None)


def test_add_exception_to_door_exception_calendar_type_error():
    with pytest.raises(TypeCheckError):
        add_exception_to_door_exception_calendar(None, minimal_exc())


def test_update_exception_on_door_exception_calendar_type_error():
    with pytest.raises(TypeCheckError):
        update_exception_on_door_exception_calendar("cid", "eid", "not-a-dict")


def test_delete_exception_on_door_exception_calendar_type_error():
    with pytest.raises(TypeCheckError):
        delete_exception_on_door_exception_calendar(None, "eid")


# 2. Return-type smoke tests for each wrapper

@patch("access_door_exceptions.get_request", return_value={"data": []})
def test_get_all_door_exception_calendars_returns_dict(mock_req):
    assert isinstance(get_all_door_exception_calendars(), dict)


@patch("access_door_exceptions.get_request", return_value={"cal": {}})
def test_get_door_exception_calendar_returns_dict(mock_req):
    assert isinstance(get_door_exception_calendar("cal1"), dict)


@patch("access_door_exceptions.post_request", return_value={"id": "new"})
def test_create_door_exception_calendar_returns_dict(mock_req):
    assert isinstance(create_door_exception_calendar(["d1"],
                                                     [minimal_exc()],
                                                     "MyCal"), dict)


@patch("access_door_exceptions.put_request", return_value={"id": "upd"})
def test_update_door_exception_calendar_returns_dict(mock_req):
    assert isinstance(update_door_exception_calendar(["d1"], [minimal_exc()], "MyCal", calendar_id="cal1"), dict)


@patch("access_door_exceptions.delete_request", return_value={"deleted": True})
def test_delete_door_exception_calendar_returns_dict(mock_req):
    assert isinstance(delete_door_exception_calendar("cal1"), dict)


@patch("access_door_exceptions.get_request", return_value={"exc": {}})
def test_get_exception_on_door_exception_calendar_returns_dict(mock_req):
    assert isinstance(get_exception_on_door_exception_calendar("cal1", "e1"), dict)


@patch("access_door_exceptions.post_request", return_value={"added": True})
def test_add_exception_to_door_exception_calendar_returns_dict(mock_req):
    assert isinstance(add_exception_to_door_exception_calendar("cal1", minimal_exc()), dict)


@patch("access_door_exceptions.put_request", return_value={"updated": True})
def test_update_exception_on_door_exception_calendar_returns_dict(mock_req):
    assert isinstance(update_exception_on_door_exception_calendar("cal1", "e1", minimal_exc()), dict)


@patch("access_door_exceptions.delete_request", return_value={"deleted": True})
def test_delete_exception_on_door_exception_calendar_returns_dict(mock_req):
    assert isinstance(delete_exception_on_door_exception_calendar("cal1", "e1"), dict)


# 3. Parameter integration tests for get_all_door_exception_calendars

@patch("access_door_exceptions.get_request", return_value={})
def test_get_all_door_exception_calendars_params_none(mock_req):
    get_all_door_exception_calendars()
    mock_req.assert_called_once_with(de.ACCESS_DOOR_EXCEPTIONS_ENDPOINT, params={})


@patch("access_door_exceptions.get_request", return_value={})
def test_get_all_door_exception_calendars_with_param(mock_req):
    get_all_door_exception_calendars(last_updated_at=123)
    mock_req.assert_called_once_with(de.ACCESS_DOOR_EXCEPTIONS_ENDPOINT, params={"last_updated_at": 123})


# 4. Parameter tests for get_door_exception_calendar

@patch("access_door_exceptions.get_request", return_value={})
def test_get_door_exception_calendar_params(mock_req):
    get_door_exception_calendar("calX")
    mock_req.assert_called_once_with(de.ACCESS_DOOR_EXCEPTIONS_ENDPOINT, params={"calendar_id": "calX"})


# 5. Parameter tests for exception endpoints (URL construction)

@patch("access_door_exceptions.get_request", return_value={})
def test_get_exception_on_door_exception_calendar_url(mock_req):
    get_exception_on_door_exception_calendar("cid", "eid")
    expected = f"{de.ACCESS_DOOR_EXCEPTIONS_ENDPOINT}/cid/exception/eid"
    mock_req.assert_called_once_with(expected)


@patch("access_door_exceptions.post_request", return_value={})
def test_add_exception_to_door_exception_calendar_url(mock_req):
    get_id = "cid"
    add_exception_to_door_exception_calendar(get_id, minimal_exc())
    expected = f"{de.ACCESS_DOOR_EXCEPTIONS_ENDPOINT}/{get_id}/exception"
    mock_req.assert_called_once_with(expected, payload=minimal_exc())


@patch("access_door_exceptions.put_request", return_value={})
def test_update_exception_on_door_exception_calendar_url(mock_req):
    get_id, exc_id = "cid", "eid"
    update_exception_on_door_exception_calendar(get_id, exc_id, minimal_exc())
    expected = f"{de.ACCESS_DOOR_EXCEPTIONS_ENDPOINT}/{get_id}/exception/{exc_id}"
    mock_req.assert_called_once_with(expected, payload=minimal_exc())


@patch("access_door_exceptions.delete_request", return_value={})
def test_delete_exception_on_door_exception_calendar_url(mock_req):
    get_id, exc_id = "cid", "eid"
    delete_exception_on_door_exception_calendar(get_id, exc_id)
    expected = f"{de.ACCESS_DOOR_EXCEPTIONS_ENDPOINT}/{get_id}/exception/{exc_id}"
    mock_req.assert_called_once_with(expected)