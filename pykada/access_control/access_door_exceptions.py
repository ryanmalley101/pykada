import re
from typeguard import typechecked
from typing import Dict, Any, Optional, List

from pykada.endpoints import *
from pykada.verkada_requests import *
from pykada.helpers import \
    require_non_empty_str, FREQUENCY_ENUM, DOOR_STATUS_ENUM, WEEKDAY_ENUM


# Helper functions

def is_valid_date(date_str: str) -> bool:
    """
    Validates that a date string is in YYYY-MM-DD format.
    """
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    return bool(re.match(pattern, date_str))

def is_valid_time(time_str: str) -> bool:
    """
    Validates that a time string is in HH:MM format (00:00 to 23:59) with required leading zeros.
    """
    pattern = r"^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
    return bool(re.match(pattern, time_str))


# Recurrence Rule Validation
@typechecked
def validate_recurrence_rule(rr: Dict[str, Any], idx: Optional[int] = None) -> None:
    """
    Validates a recurrence rule object based on the expected schema.

    :param rr: The recurrence rule object.
    :param idx: Optional index for context.
    :raises ValueError: If any required field is missing or invalid.
    """
    require_non_empty_str(rr.get("frequency", ""), "frequency", idx)
    frequency = rr["frequency"]

    if "interval" not in rr or not isinstance(rr["interval"], int):
        raise ValueError(f"Exception at index {idx}: 'interval' must be an integer in recurrence_rule")

    require_non_empty_str(rr.get("start_time", ""), "recurrence_rule start_time", idx)
    if not is_valid_time(rr["start_time"]):
        raise ValueError(f"Exception at index {idx}: 'recurrence_rule start_time' must be in HH:MM format")

    if "by_day" in rr:
        # Validate that by_day is a list of non-empty strings.
        if not isinstance(rr["by_day"], list) or not all(isinstance(day, str) and day.strip() for day in rr["by_day"]):
            raise ValueError(f"Exception at index {idx}: 'by_day' must be a list of non-empty strings")
        # Validate allowed usage based on frequency.
        if frequency == FREQUENCY_ENUM["DAILY"]:
            raise ValueError(f"Exception at index {idx}: 'by_day' is not supported for DAILY frequency")
        elif frequency == FREQUENCY_ENUM["WEEKLY"]:
            if len(rr["by_day"]) < 1:
                raise ValueError(f"Exception at index {idx}: 'by_day' must contain at least one value for WEEKLY frequency")
        elif frequency in (FREQUENCY_ENUM["MONTHLY"], FREQUENCY_ENUM["YEARLY"]):
            if "by_set_pos" not in rr or rr["by_set_pos"] is None:
                raise ValueError(f"Exception at index {idx}: For MONTHLY or YEARLY frequency, 'by_set_pos' is required when 'by_day' is provided")
            if len(rr["by_day"]) != 1:
                raise ValueError(f"Exception at index {idx}: For MONTHLY or YEARLY frequency, 'by_day' must contain exactly one value")
        # Validate that each day is one of the allowed weekdays.
        if not set(rr["by_day"]).issubset(set(WEEKDAY_ENUM.values())):
            raise ValueError(f"Exception at index {idx}: 'by_day' values must be one of {list(WEEKDAY_ENUM.values())}")

    if "by_month" in rr:
        if not isinstance(rr["by_month"], int) or not (1 <= rr["by_month"] <= 12) or frequency != FREQUENCY_ENUM["YEARLY"]:
            raise ValueError(f"Exception at index {idx}: 'by_month' must be an integer between 1 and 12 and is only supported for YEARLY frequency.")

    if "by_month_day" in rr:
        if frequency not in (FREQUENCY_ENUM["MONTHLY"], FREQUENCY_ENUM["YEARLY"]):
            raise ValueError(f"Exception at index {idx}: 'by_month_day' is only supported for MONTHLY or YEARLY frequency.")
        if "by_set_pos" in rr:
            raise ValueError(f"Exception at index {idx}: Only one of 'by_month_day' or 'by_set_pos' is allowed.")
        if not isinstance(rr["by_month_day"], int) or not (1 <= rr["by_month_day"] <= 31):
            raise ValueError(f"Exception at index {idx}: 'by_month_day' must be an integer between 1 and 31.")

    if "by_set_pos" in rr:
        if not isinstance(rr["by_set_pos"], int) or not (1 <= rr["by_set_pos"] <= 5):
            raise ValueError(f"Exception at index {idx}: 'by_set_pos' must be an integer between 1 and 5.")
        if frequency not in (FREQUENCY_ENUM["MONTHLY"], FREQUENCY_ENUM["YEARLY"]):
            raise ValueError(f"Exception at index {idx}: 'by_set_pos' is only supported for MONTHLY or YEARLY frequency.")

    if "excluded_dates" in rr:
        if not isinstance(rr["excluded_dates"], list) or not all(isinstance(d, str) and is_valid_date(d) for d in rr["excluded_dates"]):
            raise ValueError(f"Exception at index {idx}: 'excluded_dates' must be a list of valid dates in YYYY-MM-DD format")

    if "until" in rr:
        if not isinstance(rr["until"], str) or not is_valid_date(rr["until"]):
            raise ValueError(f"Exception at index {idx}: 'until' must be a valid date in YYYY-MM-DD format")

    if "count" in rr:
        if not isinstance(rr["count"], int):
            raise ValueError(f"Exception at index {idx}: 'count' must be an integer")
    if "count" in rr and "until" in rr:
        raise ValueError(f"Exception at index {idx}: Only one of 'count' or 'until' may be provided in recurrence_rule")

# Door Exception Object Validation

@typechecked
def validate_door_exception(exc: Dict[str, Any], idx: Optional[int] = None) -> None:
    """
    Validates a door exception object based on the expected schema.

    :param exc: The door exception object.
    :param idx: Optional index for context.
    :raises ValueError: If any required field is missing or invalid.
    """
    if not isinstance(exc, dict):
        raise ValueError(f"Exception at index {idx}: must be a dictionary")

    if "date" not in exc:
        raise ValueError(f"Exception at index {idx}: 'date' is required")
    require_non_empty_str(exc["date"], "date", idx)
    if not is_valid_date(exc["date"]):
        raise ValueError(f"Exception at index {idx}: 'date' must be in YYYY-MM-DD format")

    if "door_status" not in exc:
        raise ValueError(f"Exception at index {idx}: 'door_status' is required")
    require_non_empty_str(exc["door_status"], "door_status", idx)
    if exc["door_status"] not in list(DOOR_STATUS_ENUM.values()):
        raise ValueError(f"Exception at index {idx}: 'door_status' must be one of {list(DOOR_STATUS_ENUM.values())}")

    if exc.get("double_badge", False):
        if not isinstance(exc["double_badge"], bool):
            raise ValueError(f"Exception at index {idx}: 'double_badge' must be a boolean")
        if "double_badge_group_ids" not in exc or not isinstance(exc["double_badge_group_ids"], list):
            raise ValueError(f"Exception at index {idx}: 'double_badge_group_ids' must be provided as a list when double_badge is True")

    if "double_badge_group_ids" in exc:
        if "double_badge" not in exc or exc.get("double_badge", False):
            raise ValueError(
                f"Exception at index {idx}: 'double_badge must also be set to TRUE if value is provided.")


    all_day = exc.get("all_day_default", False)
    if all_day:
        if exc["door_status"] != "access_controlled":
            raise ValueError(f"Exception at index {idx}: when all_day_default is True, door_status must be 'access_controlled'")
        if "start_time" in exc and exc["start_time"] not in (None, "", "00:00"):
            raise ValueError(f"Exception at index {idx}: when all_day_default is True, start_time must be '00:00' or not provided")
        if "end_time" in exc and exc["end_time"] not in (None, "", "23:59"):
            raise ValueError(f"Exception at index {idx}: when all_day_default is True, end_time must be '23:59' or not provided")
    else:
        if "start_time" not in exc:
            raise ValueError(f"Exception at index {idx}: 'start_time' is required for non all-day exceptions")
        require_non_empty_str(exc["start_time"], "start_time", idx)
        if not is_valid_time(exc["start_time"]):
            raise ValueError(f"Exception at index {idx}: 'start_time' must be in HH:MM format")
        if "end_time" not in exc:
            raise ValueError(f"Exception at index {idx}: 'end_time' is required for non all-day exceptions")
        require_non_empty_str(exc["end_time"], "end_time", idx)
        if not is_valid_time(exc["end_time"]):
            raise ValueError(f"Exception at index {idx}: 'end_time' must be in HH:MM format")

    if exc.get("first_person_in", False):
        if "first_person_in_group_ids" not in exc or not isinstance(exc["first_person_in_group_ids"], list):
            raise ValueError(f"Exception at index {idx}: 'first_person_in_group_ids' must be provided as a list when first_person_in is True")

    if "recurrence_rule" in exc:
        validate_recurrence_rule(exc["recurrence_rule"], idx)

# Door Exception Calendar Functions

@typechecked
def get_all_door_exception_calendars(last_updated_at: Optional[int] = None) -> Dict[str, Any]:
    """
    Retrieve all available door exception calendars.

    :param last_updated_at: Optional timestamp (Unix seconds) to filter calendars updated after this time.
    :return: JSON response containing all available door exception calendars.
    """
    params = {"last_updated_at": last_updated_at} if last_updated_at is not None else {}
    return get_request(ACCESS_DOOR_EXCEPTIONS_ENDPOINT, params=params)

@typechecked
def get_door_exception_calendar(calendar_id: str) -> Dict[str, Any]:
    """
    Retrieve a specific door exception calendar.

    :param calendar_id: The unique identifier for the door exception calendar.
    :return: JSON response containing the door exception calendar details.
    :raises ValueError: If calendar_id is an empty string.
    """
    require_non_empty_str(calendar_id, "calendar_id")
    params = {'calendar_id': calendar_id}
    return get_request(ACCESS_DOOR_EXCEPTIONS_ENDPOINT, params=params)

@typechecked
def create_door_exception_calendar(doors: List[str],
                                   exceptions: List[Dict[str, Any]],
                                   name: str) -> Dict[str, Any]:
    """
    Create a new door exception calendar.

    :param doors: A non-empty list of door IDs.
    :param exceptions: A non-empty list of door exception objects.
    :param name: Name of the door exception calendar.
    :return: JSON response containing the created door exception calendar information.
    :raises ValueError: If any required field is missing or invalid.
    """
    require_non_empty_str(name, "name")
    if not doors or not all(isinstance(door, str) and door.strip() for door in doors):
        raise ValueError("doors must be a non-empty list of non-empty strings")
    for idx, door in enumerate(doors):
        require_non_empty_str(door, "door", idx)

    for exc in exceptions:
        validate_door_exception(exc)

    payload = {
        "doors": doors,
        "exceptions": exceptions,
        "name": name
    }
    return post_request(ACCESS_DOOR_EXCEPTIONS_ENDPOINT, payload=payload)

@typechecked
def update_door_exception_calendar(doors: List[str],
                                   exceptions: List[Dict[str, Any]],
                                   name: str,
                                   calendar_id: str) -> Dict[str, Any]:
    """
    Update an existing door exception calendar.

    :param doors: A non-empty list of door IDs.
    :param exceptions: A non-empty list of door exception objects.
    :param name: Updated name of the door exception calendar.
    :param calendar_id: The unique identifier of the calendar to update.
    :return: JSON response containing the updated door exception calendar information.
    :raises ValueError: If any required field is missing or invalid.
    """
    require_non_empty_str(name, "name")
    if not doors or not all(isinstance(door, str) and door.strip() for door in doors):
        raise ValueError("doors must be a non-empty list of non-empty strings")
    for idx, door in enumerate(doors):
        require_non_empty_str(door, "door", idx)

    for exc in exceptions:
        validate_door_exception(exc)

    payload = {
        "doors": doors,
        "exceptions": exceptions,
        "name": name
    }
    params = {"calendar_id": calendar_id}
    # Using put_request for update
    return put_request(ACCESS_DOOR_EXCEPTIONS_ENDPOINT, payload=payload, params=params)

@typechecked
def delete_door_exception_calendar(calendar_id: str) -> Dict[str, Any]:
    """
    Delete a door exception calendar.

    :param calendar_id: The unique identifier for the door exception calendar to delete.
    :return: JSON response confirming deletion.
    :raises ValueError: If calendar_id is an empty string.
    """
    require_non_empty_str(calendar_id, "calendar_id")
    params = {"calendar_id": calendar_id}
    return delete_request(ACCESS_DOOR_EXCEPTIONS_ENDPOINT, params=params)

@typechecked
def get_exception_on_door_exception_calendar(calendar_id: str,
                                             exception_id: str) -> Dict[str, Any]:
    """
    Retrieve a specific exception from a door exception calendar.

    :param calendar_id: The unique identifier for the door exception calendar.
    :param exception_id: The unique identifier for the exception.
    :return: JSON response containing the exception details.
    :raises ValueError: If calendar_id or exception_id is an empty string.
    """
    require_non_empty_str(calendar_id, "calendar_id")
    require_non_empty_str(exception_id, "exception_id")
    url = f"{ACCESS_DOOR_EXCEPTIONS_ENDPOINT}/{calendar_id}/exception/{exception_id}"
    return get_request(url)

@typechecked
def add_exception_to_door_exception_calendar(
    calendar_id: str,
    exception: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Add an Exception to a Door Exception Calendar.

    Adds a new Exception to the Door Exception Calendar identified by `calendar_id` using the details provided in the exception object.
    The exception object must follow the expected schema and will be validated using the `validate_door_exception` function.

    :param calendar_id: The unique identifier for the door exception calendar.
    :param exception: A dictionary representing the new exception details.
    :return: JSON response containing the created exception information.
    :raises ValueError: If calendar_id is an empty string or if the exception object fails validation.
    """
    require_non_empty_str(calendar_id, "calendar_id")
    validate_door_exception(exception)

    url = f"{ACCESS_DOOR_EXCEPTIONS_ENDPOINT}/{calendar_id}/exception"
    return post_request(url, payload=exception)

@typechecked
def update_exception_on_door_exception_calendar(
        calendar_id: str,
        exception_id: str,
        exception: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update an Exception on a Door Exception Calendar.

    Updates the Exception identified by `exception_id` on the Door Exception Calendar
    identified by `calendar_id` using the new exception details provided as a single object.

    The provided exception object must follow the expected schema, which is validated using
    the `validate_door_exception` function. For example, the object must include:
      - date (in YYYY-MM-DD format)
      - door_status (one of the allowed values)
      - For non all-day exceptions, valid start_time and end_time (in HH:MM format)
      - If all_day_default is True, door_status must be "access_controlled", and start_time/end_time
        should be omitted or defaulted to "00:00" and "23:59", respectively.
      - Optional fields such as first_person_in, double_badge, and their corresponding group IDs,
        as well as an optional recurrence_rule object.

    :param calendar_id: The unique identifier for the door exception calendar.
    :param exception_id: The unique identifier for the exception to update.
    :param exception: A dictionary representing the new exception details.
    :return: JSON response containing the updated exception information.
    :raises ValueError: If any required parameter is missing or if the exception object fails validation.
    """
    require_non_empty_str(calendar_id, "calendar_id")
    require_non_empty_str(exception_id, "exception_id")
    validate_door_exception(exception)

    url = f"{ACCESS_DOOR_EXCEPTIONS_ENDPOINT}/{calendar_id}/exception/{exception_id}"
    return put_request(url, payload=exception)


@typechecked
def delete_exception_on_door_exception_calendar(calendar_id: str, exception_id: str) -> Dict[str, Any]:
    """
    Delete an exception from a door exception calendar.

    :param calendar_id: The unique identifier for the door exception calendar.
    :param exception_id: The unique identifier for the exception to delete.
    :return: JSON response confirming deletion of the exception.
    :raises ValueError: If calendar_id or exception_id is an empty string.
    """
    require_non_empty_str(calendar_id, "calendar_id")
    require_non_empty_str(exception_id, "exception_id")
    url = f"{ACCESS_DOOR_EXCEPTIONS_ENDPOINT}/{calendar_id}/exception/{exception_id}"
    return delete_request(url)

