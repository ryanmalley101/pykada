import base64
from typeguard import typechecked
from typing import Dict, Any, Optional, Generator

from pykada.endpoints import GUEST_DENY_LIST_ENDPOINT, GUEST_SITES_ENDPOINT, \
    GUEST_VISITS_ENDPOINT
from pykada.verkada_requests import get_request, post_request, delete_request
from pykada.helpers import require_non_empty_str, iterate_paginated_results


@typechecked
def get_guest_sites() -> Dict[str, Any]:
    """
    Returns a list of Guest sites in an organization.

    :return: A dictionary containing guest site objects within the organization.
    """
    return get_request(GUEST_SITES_ENDPOINT)


@typechecked
def delete_guest_deny_list(site_id: str) -> Dict[str, Any]:
    """
    Delete the deny list for a specific Guest site.

    :param site_id: The unique identifier for the Guest site.
    :return: JSON response confirming deletion.
    :raises ValueError: If site_id is an empty string.
    """
    require_non_empty_str(site_id, "site_id")
    params = {"site_id": site_id}
    return delete_request(GUEST_DENY_LIST_ENDPOINT, params=params)


@typechecked
def create_guest_deny_list(filename: str, site_id: str) -> Dict[str, Any]:
    """
    Create a Deny List for a Verkada Guest site.

    This function reads a CSV file from the given filename, encodes its contents into
    a Base64 ASCII string, and posts the data to the Guest Deny List endpoint.
    This operation will overwrite any Deny List in use for the site.

    Query Parameters:
      - site_id (str): The unique identifier of the Guest site.

    Body Parameters:
      - base64_ascii_deny_list_csv (str): Base64 encoded (ASCII) deny list CSV data.

    :param filename: Path to the CSV file containing the deny list.
    :param site_id: The unique identifier for the Guest site.
    :return: JSON response from the POST request.
    :raises ValueError: If either filename or site_id is an empty string.
    """
    require_non_empty_str(filename, "filename")
    require_non_empty_str(site_id, "site_id")

    with open(filename, "rb") as file:
        csv_content = file.read()

    encoded_csv = base64.b64encode(csv_content).decode("ascii")
    payload = {"base64_ascii_deny_list_csv": encoded_csv}
    params = {"site_id": site_id}

    return post_request(GUEST_DENY_LIST_ENDPOINT, params=params, payload=payload)

def get_all_guest_visits(
    site_id: str,
    start_time: int,
    end_time: int,
) -> Generator[Any, None, None]:
    """
    Retrieve all visits in a Guest site.

    This function retrieves all visits within a specified time range for a given Guest site.
    It handles pagination automatically.

    :param site_id: Unique identifier for the Guest site.
    :param start_time: Start time as a UNIX timestamp.
    :param end_time: End time as a UNIX timestamp.
    :return: JSON response containing all guest visits.
    """

    params = {
        "site_id": site_id,
        "start_time": start_time,
        "end_time": end_time,
    }

    return iterate_paginated_results(get_guest_visits,
                                     items_key="visits",
                                     next_token_key="next_page_token",
                                     initial_params=params)

@typechecked
def get_guest_visits(
    site_id: str,
    start_time: int,
    end_time: int,
    page_token: Optional[str] = None,
    page_size: Optional[int] = 100
) -> Dict[str, Any]:
    """
    Retrieve a list of visits in a Guest site.

    Query Parameters:
      - site_id (str, required): The unique identifier of the Guest site.
      - start_time (int, required): The start of the time range for requested visits (UNIX timestamp).
      - end_time (int, required): The end of the time range for requested visits (UNIX timestamp).
                                  Must be at most one day (86400 seconds) away from start_time.
      - page_token (str, optional): The pagination token used to fetch the next page of results.
      - page_size (int, optional): The number of items returned in a single response (0 to 200). Defaults to 100.

    :param site_id: Unique identifier for the Guest site.
    :param start_time: Start time as a UNIX timestamp.
    :param end_time: End time as a UNIX timestamp.
    :param page_token: Optional pagination token.
    :param page_size: Optional number of items per response.
    :return: JSON response containing guest visits.
    :raises ValueError: If site_id is empty, if the time range exceeds one day, or if page_size is out of range.
    """
    if not site_id or not site_id.strip():
        raise ValueError("site_id must be a non-empty string")

    # Ensure the time range does not exceed one day (86400 seconds)
    if abs(end_time - start_time) > 86400:
        raise ValueError("The time range between start_time and end_time must be at most one day (86400 seconds)")

    if page_size is not None and (page_size < 0 or page_size > 200):
        raise ValueError("page_size must be between 0 and 200")

    params = {
        "site_id": site_id,
        "start_time": start_time,
        "end_time": end_time,
        "page_token": page_token,
        "page_size": page_size,
    }
    # Remove keys with None values.
    params = {k: v for k, v in params.items() if v is not None}

    return get_request(GUEST_VISITS_ENDPOINT, params=params)