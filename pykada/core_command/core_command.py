from typeguard import typechecked
from typing import Optional, Dict, Any
import time

from pykada.endpoints import AUDIT_LOG_ENDPOINT, COMMAND_USER_ENDPOINT
from pykada.helpers import check_user_external_id, iterate_paginated_results, \
    remove_null_fields
from pykada.verkada_requests import *

def get_all_audit_logs(start_time: Optional[int] = None,
                       end_time: Optional[int] = None):
    params = {
        "start_time": start_time,
        "end_time": end_time,
    }
    return iterate_paginated_results(get_audit_logs,
                                     initial_params=params,
                                     items_key="audit_logs",
                                     next_token_key="next_page_token")


@typechecked
def get_audit_logs(
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    page_token: Optional[str] = None,
    page_size: Optional[int] = 100
) -> Dict[str, Any]:
    """
    Retrieve audit log events based on various filters.

    :param start_time: The start of the time range for requested events, as a Unix timestamp in seconds.
                       Defaults to one hour ago from the current time if not provided.
    :param end_time: The end of the time range for requested events, as a Unix timestamp in seconds.
                     Defaults to the current time if not provided.
    :param page_token: The pagination token used to fetch the next page of results.
    :param page_size: The number of items returned in a single response (0 to 200). Defaults to 100.
    :return: JSON response containing audit log events matching the provided filters.
    :raises ValueError: If page_size is not between 0 and 200.
    """
    current_time = int(time.time())
    if start_time is None:
        start_time = current_time - 3600  # default to one hour ago
    if end_time is None:
        end_time = current_time

    if page_size is not None and (page_size < 0 or page_size > 200):
        raise ValueError("page_size must be between 0 and 200")

    params = {
        "start_time": start_time,
        "end_time": end_time,
        "page_token": page_token,
        "page_size": page_size
    }
    # Remove keys with None values.
    params = {k: v for k, v in params.items() if v is not None}

    return get_request(AUDIT_LOG_ENDPOINT, params=params)


@typechecked
def get_user(user_id: Optional[str] = None,
             external_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve a user for an organization based on either the provided user ID or external ID.
    Exactly one of user_id or external_id must be provided.

    :param user_id: The internal user identifier.
    :param external_id: The external user identifier.
    :return: JSON response containing user details.
    :raises ValueError: If not exactly one of user_id or external_id is provided.
    """
    params = check_user_external_id(user_id, external_id)
    return get_request(COMMAND_USER_ENDPOINT, params=params)


@typechecked
def create_user(
    external_id: Optional[str] = None,
    company_name: Optional[str] = None,
    department: Optional[str] = None,
    department_id: Optional[str] = None,
    email: Optional[str] = None,
    employee_id: Optional[str] = None,
    employee_title: Optional[str] = None,
    employee_type: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    middle_name: Optional[str] = None,
    phone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new user in an organization.

    Creates a user using the Core API endpoint. An external_id is required; if not provided,
    the newly created user will contain a generated user ID for identification.

    Body Parameters:
      - company_name (string): The name of the company the user is part of.
      - department (string): The name of the department the user is part of.
      - department_id (string): The department ID of the department the user is in.
      - email (string): The email address of the user.
      - employee_id (string): The user's employee ID (does not have to be unique).
      - employee_title (string): The title of the employee.
      - employee_type (string): The type of employee.
      - external_id (string, required): A unique identifier managed externally provided by the consumer.
      - first_name (string): The first name of the user.
      - last_name (string): The last name of the user.
      - middle_name (string): The middle name of the user.
      - phone (string): The main phone number of the user (E.164 format preferred).

    :param external_id: External unique identifier (required).
    :param company_name: Optional company name.
    :param department: Optional department name.
    :param department_id: Optional department ID.
    :param email: Optional email address.
    :param employee_id: Optional employee ID.
    :param employee_title: Optional employee title.
    :param employee_type: Optional employee type.
    :param first_name: Optional first name.
    :param last_name: Optional last name.
    :param middle_name: Optional middle name.
    :param phone: Optional phone number.
    :return: JSON response containing the created user information.
    :raises ValueError: If external_id is an empty string.
    """

    payload = {
        "company_name": company_name,
        "department": department,
        "department_id": department_id,
        "email": email,
        "employee_id": employee_id,
        "employee_title": employee_title,
        "employee_type": employee_type,
        "external_id": external_id,
        "first_name": first_name,
        "last_name": last_name,
        "middle_name": middle_name,
        "phone": phone,
    }
    # Remove keys with None values.
    payload = remove_null_fields(payload)

    return post_request(COMMAND_USER_ENDPOINT, payload=payload)


@typechecked
def update_user(
    external_id: Optional[str] = None,
    user_id: Optional[str] = None,
    company_name: Optional[str] = None,
    department: Optional[str] = None,
    department_id: Optional[str] = None,
    email: Optional[str] = None,
    employee_id: Optional[str] = None,
    employee_title: Optional[str] = None,
    employee_type: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    middle_name: Optional[str] = None,
    phone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing user in an organization.

    Updates a user using the Core API endpoint. Exactly one of user_id or external_id must be provided.
    The fields provided in the payload will be updated for the user.

    :param external_id: External unique identifier.
    :param user_id: Internal user identifier.
    :param company_name: Optional company name.
    :param department: Optional department name.
    :param department_id: Optional department ID.
    :param email: Optional email address.
    :param employee_id: Optional employee ID.
    :param employee_title: Optional employee title.
    :param employee_type: Optional employee type.
    :param first_name: Optional first name.
    :param last_name: Optional last name.
    :param middle_name: Optional middle name.
    :param phone: Optional phone number.
    :return: JSON response containing the updated user information.
    :raises ValueError: If not exactly one of user_id or external_id is provided.
    """
    params = check_user_external_id(user_id, external_id)

    payload = {
        "company_name": company_name,
        "department": department,
        "department_id": department_id,
        "email": email,
        "employee_id": employee_id,
        "employee_title": employee_title,
        "employee_type": employee_type,
        "external_id": external_id,
        "first_name": first_name,
        "last_name": last_name,
        "middle_name": middle_name,
        "phone": phone,
    }

    # Remove keys with None values.
    payload = {k: v for k, v in payload.items() if v is not None}

    return put_request(url=COMMAND_USER_ENDPOINT, params=params, payload=payload)


@typechecked
def delete_user(user_id: Optional[str] = None,
                external_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Delete a user from an organization based on either provided user ID or external ID.
    Exactly one of user_id or external_id must be provided.

    :param user_id: The internal user identifier.
    :param external_id: The external user identifier.
    :return: JSON response confirming deletion.
    :raises ValueError: If not exactly one of user_id or external_id is provided.
    """
    params = check_user_external_id(user_id, external_id)
    return delete_request(COMMAND_USER_ENDPOINT, params=params)
