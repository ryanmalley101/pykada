from typeguard import typechecked
from typing import Optional, List, Dict, Any

from pykada.helpers import check_user_external_id
from pykada.endpoints import ACCESS_USER_UNLOCK_ENDPOINT, \
    ACCESS_DOORS_ENDPOINT, ACCESS_ADMIN_UNLOCK_ENDPOINT
from pykada.verkada_requests import *


@typechecked
def unlock_door_as_admin(door_id: str) -> Dict[str, Any]:
    """
    Unlock a door as an administrator.

    This function sends a request to unlock the specified door without requiring user identification.

    :param door_id: The unique identifier for the door.
    :return: JSON response containing the result of the unlock operation.
    :raises ValueError: If door_id is an empty string.
    """
    if not door_id:
        raise ValueError("door_id must be a non-empty string")

    payload = {"door_id": door_id}
    return post_request(ACCESS_ADMIN_UNLOCK_ENDPOINT, payload=payload)


@typechecked
def unlock_door_as_user(door_id: str, user_id: Optional[str] = None,
                        external_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Unlock a door as a user.

    This function sends a request to unlock the specified door, using either the internal user_id or the external_id.

    :param door_id: The unique identifier for the door.
    :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
    :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
    :return: JSON response containing the result of the unlock operation.
    :raises ValueError: If door_id is an empty string.
    """
    if not door_id:
        raise ValueError("door_id must be a non-empty string")

    payload = check_user_external_id(user_id, external_id)
    payload["door_id"] = door_id

    return post_request(ACCESS_USER_UNLOCK_ENDPOINT, payload=payload)


@typechecked
def get_doors(door_id_list: Optional[List[Any]] = None,
              site_id_list: Optional[List[Any]] = None) -> Dict[str, Any]:
    """
    Retrieve door information.

    This function sends a GET request to retrieve details for doors based on provided door IDs and/or site IDs.

    :param door_id_list: A list of door IDs. If provided, these will be joined into a comma-separated string.
    :param site_id_list: A list of site IDs. If provided, these will be joined into a comma-separated string.
    :return: JSON response containing door information.
    """
    door_ids = ",".join(map(str, door_id_list)) if door_id_list else None
    site_ids = ",".join(map(str, site_id_list)) if site_id_list else None

    params = {"door_ids": door_ids, "site_ids": site_ids}
    return get_request(ACCESS_DOORS_ENDPOINT, params=params)
