import types
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from typeguard import TypeCheckError

from pykada.access_control import (
    add_exception_to_door_exception_calendar,
    create_door_exception_calendar,
    delete_door_exception_calendar,
    delete_exception_on_door_exception_calendar,
    get_all_door_exception_calendars,
    get_door_exception_calendar,
    get_door_exception_calendars,
    get_exception_on_door_exception_calendar,
    update_door_exception_calendar,
    update_exception_on_door_exception_calendar,
    validate_recurrence_rule,
)
from pykada.endpoints import V2_ACCESS_EXCEPTION_CALENDARS_ENDPOINT as CALS
from pykada.enums import DOOR_STATUS_ENUM, FREQUENCY_ENUM, WEEKDAY_FULL_ENUM

RM = "pykada.verkada_requests.VerkadaRequestManager"


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


# ———— listing ———— #

@patch(f"{RM}.get", return_value={"items": [], "cursor": None})
def test_get_door_exception_calendars_params(mock_get):
    get_door_exception_calendars(
        last_updated_after=datetime(2025, 8, 4, 21, 51, 53, tzinfo=timezone.utc),
        limit=500, cursor="c")
    mock_get.assert_called_once_with(CALS, params={
        "last_updated_after": "2025-08-04T21:51:53Z", "limit": 500, "cursor": "c"})


@patch(f"{RM}.get", return_value={"items": [], "cursor": None})
def test_get_door_exception_calendars_no_params(mock_get):
    get_door_exception_calendars()
    mock_get.assert_called_once_with(CALS, params={})


def test_get_door_exception_calendars_rejects_epoch():
    with pytest.raises(TypeCheckError):
        get_door_exception_calendars(last_updated_after=1700000000)


def test_get_door_exception_calendars_limit():
    with pytest.raises(ValueError, match="between 1 and 1000"):
        get_door_exception_calendars(limit=1001)


@patch(f"{RM}.get")
def test_get_all_door_exception_calendars_walks_pages(mock_get):
    mock_get.side_effect = [{"items": [{"calendar_id": "a"}], "cursor": "c1"},
                            {"items": [{"calendar_id": "b"}], "cursor": None}]
    result = get_all_door_exception_calendars(last_updated_after="2025-08-04T00:00:00Z")
    assert isinstance(result, types.GeneratorType)
    assert [c["calendar_id"] for c in result] == ["a", "b"]
    assert mock_get.call_args_list[1].kwargs["params"]["cursor"] == "c1"
    assert mock_get.call_args_list[1].kwargs["params"]["last_updated_after"] == \
        "2025-08-04T00:00:00Z"


# ———— single calendar ———— #

@patch(f"{RM}.get", return_value={"calendar_id": "cal1"})
def test_get_door_exception_calendar_uses_path(mock_get):
    # v1 sent calendar_id as a query param to the list endpoint
    get_door_exception_calendar("cal1")
    mock_get.assert_called_once_with(f"{CALS}/cal1")


@patch(f"{RM}.post", return_value={"calendar_id": "cal1"})
def test_create_door_exception_calendar(mock_post):
    exc = minimal_exc()
    create_door_exception_calendar("Holidays", ["door1"], [exc])
    mock_post.assert_called_once_with(CALS, payload={
        "name": "Holidays", "doors": ["door1"], "exceptions": [exc]})


@patch(f"{RM}.post", return_value={})
def test_create_door_exception_calendar_allows_empty_lists(mock_post):
    create_door_exception_calendar("Empty", [], [])
    mock_post.assert_called_once()


@patch(f"{RM}.put", return_value={"calendar_id": "cal1"})
def test_update_door_exception_calendar(mock_put):
    exc = minimal_exc(exception_id="e1")
    update_door_exception_calendar("cal1", "Holidays", ["door1", "door2"], [exc])
    mock_put.assert_called_once_with(f"{CALS}/cal1", payload={
        "name": "Holidays", "doors": ["door1", "door2"], "exceptions": [exc]})


@patch(f"{RM}.delete", return_value={})
def test_delete_door_exception_calendar(mock_delete):
    assert delete_door_exception_calendar("cal1") == {}
    mock_delete.assert_called_once_with(f"{CALS}/cal1")


@pytest.mark.parametrize("call", [
    lambda: create_door_exception_calendar("", ["door1"], []),
    lambda: create_door_exception_calendar("Cal", ["", "door2"], []),
    lambda: create_door_exception_calendar("Cal", ["door1"], [{"door_status": "unlocked"}]),
    lambda: update_door_exception_calendar("", "Cal", [], []),
    lambda: update_door_exception_calendar("cal1", "", [], []),
    lambda: get_door_exception_calendar(" "),
    lambda: delete_door_exception_calendar(""),
])
def test_calendar_validation_errors(call):
    with pytest.raises(ValueError):
        call()


def test_calendar_exception_index_in_error():
    bad = minimal_exc(door_status="open")
    with pytest.raises(ValueError, match="index 1"):
        create_door_exception_calendar("Cal", ["d1"], [minimal_exc(), bad])


# ———— individual exceptions ———— #

@patch(f"{RM}.get", return_value={"exception_id": "e1"})
def test_get_exception(mock_get):
    get_exception_on_door_exception_calendar("cal1", "e1")
    mock_get.assert_called_once_with(f"{CALS}/cal1/exceptions/e1")


@patch(f"{RM}.post", return_value={"exception_id": "e1"})
def test_add_exception(mock_post):
    exc = minimal_exc(recurrence_rule={"frequency": "WEEKLY", "interval": 1,
                                       "by_day": ["Monday", "Friday"]})
    add_exception_to_door_exception_calendar("cal1", exc)
    mock_post.assert_called_once_with(f"{CALS}/cal1/exceptions", payload=exc)


@patch(f"{RM}.put", return_value={"exception_id": "e1"})
def test_update_exception(mock_put):
    exc = minimal_exc(start_time="09:00:00", end_time="17:30:00")
    update_exception_on_door_exception_calendar("cal1", "e1", exc)
    mock_put.assert_called_once_with(f"{CALS}/cal1/exceptions/e1", payload=exc)


@patch(f"{RM}.delete", return_value={})
def test_delete_exception(mock_delete):
    assert delete_exception_on_door_exception_calendar("cal1", "e1") == {}
    mock_delete.assert_called_once_with(f"{CALS}/cal1/exceptions/e1")


def test_add_exception_rejects_v1_weekday_codes():
    exc = minimal_exc(recurrence_rule={"frequency": "WEEKLY", "interval": 1, "by_day": ["MO"]})
    with pytest.raises(ValueError, match="full weekday names"):
        add_exception_to_door_exception_calendar("cal1", exc)


@pytest.mark.parametrize("func, args", [
    (get_exception_on_door_exception_calendar, ("cid", None)),
    (add_exception_to_door_exception_calendar, (None, minimal_exc())),
    (update_exception_on_door_exception_calendar, ("cid", "eid", "not-a-dict")),
    (delete_exception_on_door_exception_calendar, (None, "eid")),
    (create_door_exception_calendar, ("Name", "not-a-list", [])),
])
def test_type_errors(func, args):
    with pytest.raises(TypeCheckError):
        func(*args)


# ———— validate_recurrence_rule ———— #

def base_rr(**overrides):
    """
    Return a minimal valid daily recurrence rule.
    """
    rr = {
        "frequency": FREQUENCY_ENUM["DAILY"],
        "interval": 1,
    }
    rr.update(overrides)
    return rr


# --- VALID CASES --- #

def test_daily_minimal_valid():
    validate_recurrence_rule(base_rr())


def test_weekly_with_by_day_valid():
    rr = base_rr(
        frequency=FREQUENCY_ENUM["WEEKLY"],
        by_day=[WEEKDAY_FULL_ENUM["MONDAY"], WEEKDAY_FULL_ENUM["WEDNESDAY"]]
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
        by_day=[WEEKDAY_FULL_ENUM["TUESDAY"]],
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
        by_day=[WEEKDAY_FULL_ENUM["FRIDAY"]],
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
    rr = {"frequency": FREQUENCY_ENUM["DAILY"]}
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_interval_not_int():
    rr = base_rr(interval="one")
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_weekly_missing_by_day():
    rr = base_rr(frequency=FREQUENCY_ENUM["WEEKLY"])
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_monthly_missing_by_month_day_and_by_set_pos():
    rr = base_rr(frequency=FREQUENCY_ENUM["MONTHLY"])
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_yearly_missing_by_month():
    rr = base_rr(
        frequency=FREQUENCY_ENUM["YEARLY"],
        by_month_day=25,
    )
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_invalid_frequency():
    rr = base_rr(frequency="HOURLY")
    with pytest.raises(ValueError):
        validate_recurrence_rule(rr)


def test_by_day_not_supported_for_daily():
    rr = base_rr(by_day=[WEEKDAY_FULL_ENUM["SUNDAY"]])
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
        by_day=[WEEKDAY_FULL_ENUM["MONDAY"]],
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



@pytest.mark.parametrize("field, value", [("interval", 0), ("count", 0), ("count", -2)])
def test_interval_and_count_must_be_positive(field, value):
    with pytest.raises(ValueError, match="positive integer"):
        validate_recurrence_rule(base_rr(**{field: value}))
