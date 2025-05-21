from typeguard import typechecked
from typing import Optional
from pykada.endpoints import ACCESS_GROUPS_ENDPOINT, ACCESS_GROUP_ENDPOINT, \
    ACCESS_GROUP_USER_ENDPOINT
from pykada.helpers import remove_null_fields, require_non_empty_str
from pykada.verkada_requests import *



@typechecked
def get_access_groups() -> dict:
    """
    Retrieve all access groups.

    :return: JSON response containing a list of access groups.
    :rtype: dict
    """
    return get_request(ACCESS_GROUPS_ENDPOINT)


@typechecked
def delete_access_group(group_id: str) -> dict:
    """
    Delete an access group.

    :param group_id: The unique identifier for the access group.
    :type group_id: str
    :return: JSON response after deleting the access group.
    :rtype: dict
    :raises ValueError: If group_id is an empty string.
    """
    if not group_id:
        raise ValueError("group_id must be a non-empty string")
    params = {"group_id": group_id}
    return delete_request(ACCESS_GROUP_ENDPOINT, params=params)


@typechecked
def get_access_group(group_id: str) -> dict:
    """
    Retrieve a specific access group by its ID.

    :param group_id: The unique identifier for the access group.
    :type group_id: str
    :return: JSON response containing the access group details.
    :rtype: dict
    :raises ValueError: If group_id is an empty string.
    """
    if not group_id:
        raise ValueError("group_id must be a non-empty string")
    params = {"group_id": group_id}
    return get_request(ACCESS_GROUP_ENDPOINT, params=params)


@typechecked
def create_access_group(name: str) -> dict:
    """
    Create a new access group with the specified name.

    :param name: The name for the new access group.
    :type name: str
    :return: JSON response containing details of the created access group.
    :rtype: dict
    :raises ValueError: If name is an empty string.
    """

    require_non_empty_str(name, 'name')

    payload = {"name": name}

    return post_request(ACCESS_GROUP_ENDPOINT, payload=payload)


@typechecked
def add_user_to_access_group(group_id: str, external_id: Optional[str] = None,
                             user_id: Optional[str] = None) -> dict:
    """
    Add a user to an access group. Exactly one of user_id or external_id must be provided.

    :param group_id: The unique identifier for the access group.
    :type group_id: str
    :param external_id: The external identifier for the user.
    :type external_id: str, optional
    :param user_id: The internal user identifier.
    :type user_id: str, optional
    :return: JSON response after adding the user to the access group.
    :rtype: dict
    :raises ValueError: If group_id is empty, or if not exactly one of user_id or external_id is provided.
    """
    if not group_id:
        raise ValueError("group_id must be a non-empty string")
    if (user_id is None and external_id is None) or (
            user_id is not None and external_id is not None):
        raise ValueError(
            "Exactly one of user_id or external_id must be provided, not both or neither.")

    params = {"group_id": group_id}
    payload = {"external_id": external_id, "user_id": user_id}
    # Remove keys with None values from payload.
    payload = remove_null_fields(payload)
    return put_request(ACCESS_GROUP_USER_ENDPOINT, params=params,
                       payload=payload)


@typechecked
def remove_user_from_access_group(group_id: str,
                                  external_id: Optional[str] = None,
                                  user_id: Optional[str] = None) -> dict:
    """
    Remove a user from an access group. Exactly one of user_id or external_id must be provided.

    :param group_id: The unique identifier for the access group.
    :type group_id: str
    :param external_id: The external identifier for the user.
    :type external_id: str, optional
    :param user_id: The internal user identifier.
    :type user_id: str, optional
    :return: JSON response after removing the user from the access group.
    :rtype: dict
    :raises ValueError: If group_id is empty, or if not exactly one of user_id or external_id is provided.
    """
    if not group_id:
        raise ValueError("group_id must be a non-empty string")
    if (user_id is None and external_id is None) or (
            user_id is not None and external_id is not None):
        raise ValueError(
            "Exactly one of user_id or external_id must be provided, not both or neither.")

    params = {"group_id": group_id, "external_id": external_id,
              "user_id": user_id}
    # Remove keys with None values.
    params = remove_null_fields(params)
    return put_request(ACCESS_GROUP_USER_ENDPOINT, params=params)
