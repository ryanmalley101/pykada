import pytest
from typeguard import TypeCheckError

from pykada.access_control import validate_door_exception
from pykada.enums import DOOR_STATUS_ENUM


VALID_STATUS = DOOR_STATUS_ENUM["ACCESS_CONTROLLED"]  # "access_controlled"


def _base_exc(**overrides):
    exc = {
        "date": "2025-01-15",
        "door_status": VALID_STATUS,
        "start_time": "08:00",
        "end_time": "17:00",
    }
    exc.update(overrides)
    return exc


# ---------- structural / type checks ----------

def test_non_dict_raises_type_error():
    with pytest.raises(TypeCheckError):
        validate_door_exception("not-a-dict")


# ---------- date ----------

def test_missing_date_raises():
    exc = _base_exc()
    del exc["date"]
    with pytest.raises(ValueError, match="'date' is required"):
        validate_door_exception(exc)


def test_empty_date_raises():
    with pytest.raises(ValueError, match="date"):
        validate_door_exception(_base_exc(date=""))


def test_bad_date_format_raises():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        validate_door_exception(_base_exc(date="01/15/2025"))


# ---------- door_status ----------

def test_missing_door_status_raises():
    exc = _base_exc()
    del exc["door_status"]
    with pytest.raises(ValueError, match="'door_status' is required"):
        validate_door_exception(exc)


def test_invalid_door_status_raises():
    with pytest.raises(ValueError, match="door_status"):
        validate_door_exception(_base_exc(door_status="always_open"))


# ---------- start_time / end_time (non-all-day) ----------

def test_missing_start_time_raises():
    exc = _base_exc()
    del exc["start_time"]
    with pytest.raises(ValueError, match="'start_time' is required"):
        validate_door_exception(exc)


def test_bad_start_time_format_raises():
    with pytest.raises(ValueError, match="HH:MM"):
        validate_door_exception(_base_exc(start_time="8:00"))


def test_missing_end_time_raises():
    exc = _base_exc()
    del exc["end_time"]
    with pytest.raises(ValueError, match="'end_time' is required"):
        validate_door_exception(exc)


def test_bad_end_time_format_raises():
    with pytest.raises(ValueError, match="HH:MM"):
        validate_door_exception(_base_exc(end_time="5pm"))


# ---------- all_day_default ----------

def test_all_day_wrong_door_status_raises():
    with pytest.raises(ValueError, match="access_controlled"):
        validate_door_exception({
            "date": "2025-01-15",
            "door_status": DOOR_STATUS_ENUM["UNLOCKED"],
            "all_day_default": True,
        })


def test_all_day_bad_start_time_raises():
    with pytest.raises(ValueError, match="start_time must be '00:00'"):
        validate_door_exception({
            "date": "2025-01-15",
            "door_status": VALID_STATUS,
            "all_day_default": True,
            "start_time": "09:00",
        })


def test_all_day_bad_end_time_raises():
    with pytest.raises(ValueError, match="end_time must be '23:59'"):
        validate_door_exception({
            "date": "2025-01-15",
            "door_status": VALID_STATUS,
            "all_day_default": True,
            "end_time": "18:00",
        })


def test_all_day_with_double_badge_raises():
    with pytest.raises(ValueError, match="double_badge"):
        validate_door_exception({
            "date": "2025-01-15",
            "door_status": VALID_STATUS,
            "all_day_default": True,
            "double_badge": True,
        })


def test_all_day_with_first_person_in_raises():
    with pytest.raises(ValueError, match="first_person_in"):
        validate_door_exception({
            "date": "2025-01-15",
            "door_status": VALID_STATUS,
            "all_day_default": True,
            "first_person_in": True,
        })


def test_all_day_valid():
    validate_door_exception({
        "date": "2025-01-15",
        "door_status": VALID_STATUS,
        "all_day_default": True,
    })


# ---------- double_badge ----------

def test_double_badge_wrong_door_status_raises():
    with pytest.raises(ValueError, match="access_controlled"):
        validate_door_exception(_base_exc(
            double_badge=True,
            door_status=DOOR_STATUS_ENUM["UNLOCKED"],
        ))


def test_double_badge_group_ids_without_double_badge_raises():
    with pytest.raises(ValueError, match="double_badge must also be set"):
        validate_door_exception(_base_exc(double_badge_group_ids=["grp1"]))


def test_double_badge_valid():
    validate_door_exception(_base_exc(double_badge=True))


def test_double_badge_with_group_ids_valid():
    validate_door_exception(_base_exc(
        double_badge=True,
        double_badge_group_ids=["grp1"],
    ))


# ---------- first_person_in ----------

def test_first_person_in_wrong_door_status_raises():
    with pytest.raises(ValueError, match="door_status"):
        validate_door_exception(_base_exc(
            first_person_in=True,
            door_status=DOOR_STATUS_ENUM["LOCKED"],
        ))


def test_first_person_in_group_ids_without_first_person_in_raises():
    with pytest.raises(ValueError, match="first_person_in must also be set"):
        validate_door_exception(_base_exc(first_person_in_group_ids=["grp1"]))


def test_first_person_in_valid():
    validate_door_exception(_base_exc(first_person_in=True))


def test_first_person_in_card_and_code_valid():
    validate_door_exception(_base_exc(
        first_person_in=True,
        door_status=DOOR_STATUS_ENUM["CARD_AND_CODE"],
    ))


def test_first_person_in_unlocked_valid():
    validate_door_exception(_base_exc(
        first_person_in=True,
        door_status=DOOR_STATUS_ENUM["UNLOCKED"],
    ))


# ---------- happy paths ----------

def test_minimal_valid_exception():
    validate_door_exception(_base_exc())


def test_valid_with_idx():
    validate_door_exception(_base_exc(), idx=0)


def test_all_door_statuses_valid():
    for status in DOOR_STATUS_ENUM.values():
        exc = _base_exc(door_status=status)
        if status != VALID_STATUS:
            exc.update({"start_time": "08:00", "end_time": "17:00"})
        validate_door_exception(exc)
