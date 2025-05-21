from typeguard import typechecked
from typing import Dict, Any, List, Optional
import re

from pykada.endpoints import *
from pykada.helpers import WEEKDAY_ENUM, require_non_empty_str
from pykada.verkada_requests import *


def is_valid_time(time_str: str) -> bool:
    """
    Checks if the input string matches the HH:MM time format (00:00 to 23:59) with required leading zeros.

    :param time_str: The time string to validate.
    :return: True if the string matches the format, False otherwise.
    """
    pattern = r"^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
    return bool(re.match(pattern, time_str))


@typechecked
def get_all_access_levels() -> Dict[str, Any]:
    """
    Retrieve all available access levels.

    :return: JSON response containing all available access levels.
    """
    return get_request(ACCESS_LEVEL_ENDPOINT)


@typechecked
def get_access_level(access_level_id: str) -> Dict[str, Any]:
    """
    Retrieve details for a specific access level.

    :param access_level_id: The unique identifier for the access level.
    :return: JSON response containing the access level details.
    :raises ValueError: If access_level_id is an empty string.
    """
    if not access_level_id:
        raise ValueError("access_level_id must be a non-empty string")

    url = f"{ACCESS_LEVEL_ENDPOINT}/{access_level_id}"
    return get_request(url)


@typechecked
def create_access_level(
        name: str,
        access_groups: Optional[List[str]] = None,
        access_schedule_events: Optional[List[Dict[str, Any]]] = None,
        doors: Optional[List[str]] = None,
        sites: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a new Access Level.

    To use this API, you need an API Key having permission "Door Access Management"
    for all sites listed in 'sites' for the Access Level, and "Manage via API" must
    also be enabled for all doors listed in 'doors'.

    Body Parameters:
      - access_groups (List[str], required): IDs of Access Groups granted door access via this Access Level.
      - access_schedule_events (List[Dict[str, Any]], required): List of Access Schedule Events associated with this Access Level.
            Each event object should include:
              - access_schedule_event_id (str): Unique identifier for the Access Schedule Event.
              - door_status (str): Door status for Access Schedule Events (defaults to "access_granted").
              - start_time (str): Start time of the event in HH:MM format (00:00 to 23:59, with leading zeros).
              - end_time (str): End time of the event in HH:MM format (00:00 to 23:59, with leading zeros).
              - weekday (str): Enum for days of the week (e.g., "SU").
      - doors (List[str], required): IDs of Doors accessible under this Access Level.
      - name (str, required): Name of the Access Level.
      - sites (List[str], required): IDs of Sites containing the Doors this Access Level applies to.

    :param access_groups: List of Access Group IDs.
    :param access_schedule_events: List of Access Schedule Event objects.
    :param doors: List of Door IDs.
    :param name: Name for the Access Level.
    :param sites: List of Site IDs.
    :return: JSON response containing the created Access Level information.
    :raises ValueError: If name is an empty string.
    """
    require_non_empty_str(name, "name")

    payload = {
        "access_groups": access_groups if access_groups else [],
        "access_schedule_events": access_schedule_events if access_schedule_events else [],
        "doors": doors if doors else [],
        "name": name,
        "sites": sites if sites else [],
    }
    return post_request(ACCESS_LEVEL_ENDPOINT, payload=payload)


@typechecked
def update_access_level(
        access_level_id: str,
        access_groups: List[str],
        access_schedule_events: List[Dict[str, Any]],
        doors: List[str],
        name: str,
        sites: List[str]
) -> Dict[str, Any]:
    """
    Update an existing Access Level.

    To use this API, you need an API Key having permission "Door Access Management"
    for all sites listed in 'sites' for the Access Level, and "Manage via API" must
    also be enabled for all doors listed in 'doors'.

    :param access_level_id: The ID of the Access Level to be updated.
    :param access_groups: List of Access Group IDs.
    :param access_schedule_events: List of Access Schedule Event objects.
    :param doors: List of Door IDs.
    :param name: Name for the Access Level.
    :param sites: List of Site IDs.
    :return: JSON response containing the updated Access Level information.
    :raises ValueError: If access_level_id or name is an empty string.
    """
    if not access_level_id:
        raise ValueError("access_level_id must be a non-empty string")
    if not name:
        raise ValueError("name must be a non-empty string")

    payload = {
        "access_groups": access_groups,
        "access_schedule_events": access_schedule_events,
        "doors": doors,
        "name": name,
        "sites": sites,
    }
    url = f"{ACCESS_LEVEL_ENDPOINT}/{access_level_id}"
    return put_request(url, payload=payload)


@typechecked
def delete_access_level(access_level_id: str) -> Dict[str, Any]:
    """
    Delete an access level.

    :param access_level_id: The unique identifier for the access level to delete.
    :return: JSON response confirming deletion.
    :raises ValueError: If access_level_id is an empty string.
    """
    if not access_level_id:
        raise ValueError("access_level_id must be a non-empty string")

    params = {"access_level_id": access_level_id}
    url = f"{ACCESS_LEVEL_ENDPOINT}/{access_level_id}"
    return delete_request(url, params=params)


@typechecked
def add_access_schedule_event_to_access_level(
        access_level_id: str,
        start_time: str,
        end_time: str,
        weekday: str,
) -> Dict[str, Any]:
    """
    Add an access schedule event to a specific access level.

    The event details are provided in the payload. The door_status is fixed to "access_granted".

    :param access_level_id: The unique identifier for the access level.
    :param start_time: Start time of the event in HH:MM format (00:00 to 23:59, with leading zeros).
    :param end_time: End time of the event in HH:MM format (00:00 to 23:59, with leading zeros).
    :param weekday: Enum for days of the week (e.g., "SU").
    :return: JSON response containing the created event information.
    :raises ValueError: If access_level_id is empty, if start_time or end_time are not valid, or if weekday is invalid.
    """
    if not access_level_id:
        raise ValueError("access_level_id must be a non-empty string")
    if not is_valid_time(start_time) or not is_valid_time(end_time):
        raise ValueError(
            "start_time and end_time must be in HH:MM format (00:00 to 23:59) with required leading zeros")
    if weekday not in WEEKDAY_ENUM.values():
        raise ValueError(
            f"weekday must be one of the values in WEEKDAY_ENUM: {list(WEEKDAY_ENUM.values())}")

    payload = {
        "door_status": "access_granted",
        "start_time": start_time,
        "end_time": end_time,
        "weekday": weekday,
    }
    url = f"{ACCESS_LEVEL_ENDPOINT}/{access_level_id}/access_schedule_event"
    return post_request(url, payload=payload)


@typechecked
def update_access_schedule_event_on_access_level(
        access_level_id: str,
        event_id: str,
        start_time: str,
        end_time: str,
        weekday: str,
) -> Dict[str, Any]:
    """
    Update an access schedule event on a specific access level.

    :param access_level_id: The unique identifier for the access level.
    :param event_id: The unique identifier for the schedule event.
    :param start_time: Updated start time in HH:MM format.
    :param end_time: Updated end time in HH:MM format.
    :param weekday: Updated weekday enum (e.g., "SU").
    :return: JSON response containing the updated event information.
    :raises ValueError: If any of the required identifiers or times are invalid.
    """
    if not access_level_id:
        raise ValueError("access_level_id must be a non-empty string")
    if not event_id:
        raise ValueError("event_id must be a non-empty string")
    if not is_valid_time(start_time) or not is_valid_time(end_time):
        raise ValueError(
            "start_time and end_time must be in HH:MM format (00:00 to 23:59) with required leading zeros")
    if weekday not in WEEKDAY_ENUM.values():
        raise ValueError(
            f"weekday must be one of the values in WEEKDAY_ENUM: {list(WEEKDAY_ENUM.values())}")

    payload = {
        "door_status": "access_granted",
        "start_time": start_time,
        "end_time": end_time,
        "weekday": weekday,
    }
    url = f"{ACCESS_LEVEL_ENDPOINT}/{access_level_id}/access_schedule_event/{event_id}"
    return put_request(url, payload=payload)


@typechecked
def delete_access_schedule_event_on_access_level(
        access_level_id: str,
        event_id: str
) -> Dict[str, Any]:
    """
    Delete an access schedule event from a specific access level.

    :param access_level_id: The unique identifier for the access level.
    :param event_id: The unique identifier for the schedule event.
    :return: JSON response confirming deletion.
    :raises ValueError: If access_level_id or event_id is an empty string.
    """
    if not access_level_id:
        raise ValueError("access_level_id must be a non-empty string")
    if not event_id:
        raise ValueError("event_id must be a non-empty string")

    url = f"{ACCESS_LEVEL_ENDPOINT}/{access_level_id}/access_schedule_event/{event_id}"
    return delete_request(url)
