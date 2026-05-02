"""
Workplace (Guest & Mailroom) API client and functional wrappers for pykada.

The :class:`WorkplaceClient` provides access to guest visit history, site
management, and deny-list uploads through Verkada's Workplace API.
"""
import base64
from typeguard import typechecked
from typing import Dict, Any, Optional, Generator, List

from pykada.api_tokens import VerkadaTokenManager
from pykada.endpoints import GUEST_DENY_LIST_ENDPOINT, GUEST_SITES_ENDPOINT, \
    GUEST_VISITS_ENDPOINT, GUEST_V2_EVENTS_ENDPOINT, GUEST_V2_HOSTS_ENDPOINT, \
    GUEST_V2_APPROVED_LISTS_ENDPOINT, GUEST_V2_APPROVED_LISTS_ADD_ENDPOINT, \
    GUEST_V2_APPROVED_LISTS_REMOVE_ENDPOINT, GUEST_V2_GUEST_TYPES_ENDPOINT
from pykada.verkada_client import BaseClient
from pykada.helpers import require_non_empty_str, remove_null_fields
from pykada.verkada_requests import VerkadaRequestManager

class WorkplaceClient(BaseClient):
    """
    Client for interacting with Verkada's Workplace (Guest & Mailroom) API.
    This client provides methods to manage guest visits, deny lists, and sites.
    """

    def __init__(self,
                 api_key: Optional[str] = None,
                 token_manager: Optional[VerkadaTokenManager] = None):
        super().__init__(api_key, token_manager)

    @typechecked
    def get_guest_sites(self) -> Dict[str, Any]:
        """
        Returns a list of Guest sites in an organization.

        :return: A dictionary containing guest site objects within the organization.
        """
        return self.request_manager.get(GUEST_SITES_ENDPOINT)


    @typechecked
    def delete_guest_deny_list(self, site_id: str) -> Dict[str, Any]:
        """
        Delete the deny list for a specific Guest site.

        :param site_id: The unique identifier for the Guest site.
        :return: JSON response confirming deletion.
        :raises ValueError: If site_id is an empty string.
        """
        require_non_empty_str(site_id, "site_id")
        params = {"site_id": site_id}
        return self.request_manager.delete(GUEST_DENY_LIST_ENDPOINT, params=params)


    @typechecked
    def create_guest_deny_list(self, filename: str, site_id: str) -> Dict[str, Any]:
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

        return self.request_manager.post(GUEST_DENY_LIST_ENDPOINT, params=params, payload=payload)

    def get_all_guest_visits(
        self,
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

        return VerkadaRequestManager.iterate_paginated_results(
            lambda **kwargs: self.get_guest_visits(**kwargs),
            initial_params=params,
            next_token_key="next_page_token",
            items_key="visits"
        )

    @typechecked
    def get_guest_visits(
        self,
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

        return self.request_manager.get(GUEST_VISITS_ENDPOINT, params=params)


    @typechecked
    def get_guest_events(self, site_id: str, start_time: str, end_time: str,
                         limit: Optional[int] = None,
                         cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve guest events for a site.

        :param site_id: The unique identifier of the Guest site.
        :param start_time: Start time in ISO 8601 format (e.g. ``'2025-01-17T21:06:20Z'``).
        :param end_time: End time in ISO 8601 format.
        :param limit: Maximum number of items to return (default 100, max 200).
        :param cursor: Pagination cursor for the next page.
        :return: JSON response containing guest events.
        :raises ValueError: If site_id, start_time, or end_time is empty.
        """
        require_non_empty_str(site_id, "site_id")
        require_non_empty_str(start_time, "start_time")
        require_non_empty_str(end_time, "end_time")
        params = remove_null_fields({
            "site_id": site_id,
            "start_time": start_time,
            "end_time": end_time,
            "limit": limit,
            "cursor": cursor,
        })
        return self.request_manager.get(GUEST_V2_EVENTS_ENDPOINT, params=params)


    @typechecked
    def create_guest_event(self, site_id: str, guest_type_id: str, host_id: str,
                           event_times: List[Dict[str, Any]],
                           event_name: Optional[str] = None,
                           event_address: Optional[str] = None,
                           event_description: Optional[str] = None,
                           invitees: Optional[List[Dict[str, Any]]] = None,
                           rsvp_enabled: Optional[bool] = None,
                           walk_in_enabled: Optional[bool] = None) -> Dict[str, Any]:
        """
        Create a guest event.

        :param site_id: The unique identifier of the Guest site.
        :param guest_type_id: The unique identifier of the guest type.
        :param host_id: The unique identifier of the host.
        :param event_times: List of start/end time objects for the event.
        :param event_name: Optional name for the event.
        :param event_address: Optional location of the event.
        :param event_description: Optional description of the event.
        :param invitees: Optional list of invitee objects.
        :param rsvp_enabled: Whether to generate an RSVP link.
        :param walk_in_enabled: Whether walk-ins are allowed.
        :return: JSON response containing the created event.
        :raises ValueError: If site_id, guest_type_id, or host_id is empty.
        """
        require_non_empty_str(site_id, "site_id")
        require_non_empty_str(guest_type_id, "guest_type_id")
        require_non_empty_str(host_id, "host_id")
        payload = remove_null_fields({
            "site_id": site_id,
            "guest_type_id": guest_type_id,
            "host_id": host_id,
            "event_times": event_times,
            "event_name": event_name,
            "event_address": event_address,
            "event_description": event_description,
            "invitees": invitees,
            "rsvp_enabled": rsvp_enabled,
            "walk_in_enabled": walk_in_enabled,
        })
        return self.request_manager.post(GUEST_V2_EVENTS_ENDPOINT, payload=payload)


    @typechecked
    def delete_guest_event(self, guest_event_id: str) -> Dict[str, Any]:
        """
        Delete a guest event.

        :param guest_event_id: The unique identifier of the guest event.
        :return: JSON response confirming deletion.
        :raises ValueError: If guest_event_id is empty.
        """
        require_non_empty_str(guest_event_id, "guest_event_id")
        url = f"{GUEST_V2_EVENTS_ENDPOINT}/{guest_event_id}"
        return self.request_manager.delete(url)


    @typechecked
    def get_guest_event(self, guest_event_id: str) -> Dict[str, Any]:
        """
        Retrieve a single guest event by ID.

        :param guest_event_id: The unique identifier of the guest event.
        :return: JSON response containing the guest event.
        :raises ValueError: If guest_event_id is empty.
        """
        require_non_empty_str(guest_event_id, "guest_event_id")
        url = f"{GUEST_V2_EVENTS_ENDPOINT}/{guest_event_id}"
        return self.request_manager.get(url)


    @typechecked
    def get_guest_hosts(self, site_id: str,
                        email: Optional[str] = None,
                        cursor: Optional[str] = None,
                        limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Retrieve hosts for a Guest site.

        :param site_id: The unique identifier of the Guest site.
        :param email: Optional email to filter to a single host.
        :param cursor: Pagination cursor for the next page.
        :param limit: Maximum number of hosts to return (default 100, max 200).
        :return: JSON response containing hosts.
        :raises ValueError: If site_id is empty.
        """
        require_non_empty_str(site_id, "site_id")
        params = remove_null_fields({
            "site_id": site_id,
            "email": email,
            "cursor": cursor,
            "limit": limit,
        })
        return self.request_manager.get(GUEST_V2_HOSTS_ENDPOINT, params=params)


    @typechecked
    def get_approved_lists(self, site_id: Optional[str] = None,
                           cursor: Optional[str] = None,
                           limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Retrieve approved lists for the organization or a specific site.

        :param site_id: Optional site ID to filter results.
        :param cursor: Pagination cursor for the next page.
        :param limit: Maximum number of lists to return (default 100, max 1000).
        :return: JSON response containing approved lists.
        """
        params = remove_null_fields({"site_id": site_id, "cursor": cursor, "limit": limit})
        return self.request_manager.get(GUEST_V2_APPROVED_LISTS_ENDPOINT, params=params)


    @typechecked
    def add_people_to_approved_lists(self, people: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add people to approved lists.

        :param people: List of people objects to add to approved lists.
        :return: JSON response after adding people.
        """
        return self.request_manager.patch(GUEST_V2_APPROVED_LISTS_ADD_ENDPOINT,
                                          payload={"people": people})


    @typechecked
    def remove_people_from_approved_lists(self, people: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Remove people from approved lists.

        :param people: List of people objects to remove from approved lists.
        :return: JSON response after removing people.
        """
        return self.request_manager.patch(GUEST_V2_APPROVED_LISTS_REMOVE_ENDPOINT,
                                          payload={"people": people})


    @typechecked
    def get_approved_list_members(self, approved_list_id: str,
                                  cursor: Optional[str] = None,
                                  limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Retrieve members of a specific approved list.

        :param approved_list_id: The unique identifier of the approved list.
        :param cursor: Pagination cursor for the next page.
        :param limit: Maximum number of members to return (default 100, max 1000).
        :return: JSON response containing list members.
        :raises ValueError: If approved_list_id is empty.
        """
        require_non_empty_str(approved_list_id, "approved_list_id")
        url = f"{GUEST_V2_APPROVED_LISTS_ENDPOINT}/{approved_list_id}"
        params = remove_null_fields({"cursor": cursor, "limit": limit})
        return self.request_manager.get(url, params=params)


    @typechecked
    def reset_approved_list(self, approved_list_id: str) -> Dict[str, Any]:
        """
        Reset an approved list, removing all members.

        :param approved_list_id: The unique identifier of the approved list.
        :return: JSON response after resetting the list.
        :raises ValueError: If approved_list_id is empty.
        """
        require_non_empty_str(approved_list_id, "approved_list_id")
        url = f"{GUEST_V2_APPROVED_LISTS_ENDPOINT}/{approved_list_id}/reset"
        return self.request_manager.patch(url)


    @typechecked
    def get_guest_types(self, site_id: str,
                        cursor: Optional[str] = None,
                        limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Retrieve guest types for a site.

        :param site_id: The unique identifier of the Guest site.
        :param cursor: Pagination cursor for the next page.
        :param limit: Maximum number of guest types to return (default 100, max 200).
        :return: JSON response containing guest types.
        :raises ValueError: If site_id is empty.
        """
        require_non_empty_str(site_id, "site_id")
        params = remove_null_fields({"site_id": site_id, "cursor": cursor, "limit": limit})
        return self.request_manager.get(GUEST_V2_GUEST_TYPES_ENDPOINT, params=params)


# ---------------------------------------------------------------------------
# Module-level default client — shared across all functional wrappers.
# ---------------------------------------------------------------------------
_default_workplace_client: Optional[WorkplaceClient] = None


def _get_default_client() -> WorkplaceClient:
    global _default_workplace_client
    if _default_workplace_client is None:
        _default_workplace_client = WorkplaceClient()
    return _default_workplace_client


def get_guest_sites(*args, **kwargs) -> dict:
    """
    Returns all Workplace guest sites for the organization.

    :return: A dictionary containing the list of guest sites.
    :rtype: dict
    """
    return _get_default_client().get_guest_sites(*args, **kwargs)


@typechecked
def create_guest_deny_list(filename: str, site_id: str):
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

    ---

    **Note:** This is a functional wrapper for its equivalent method in the WorkplaceClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a WorkplaceClient object directly for better performance.
    """
    return _get_default_client().create_guest_deny_list(filename, site_id)

@typechecked
def delete_guest_deny_list(site_id: str):
    """
    Delete the deny list for a specific Guest site.

    :param site_id: The unique identifier for the Guest site.
    :return: JSON response confirming deletion.
    :raises ValueError: If site_id is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the WorkplaceClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a WorkplaceClient object directly for better performance.
    """
    return _get_default_client().delete_guest_deny_list(site_id)

@typechecked
def get_all_guest_visits(site_id: str, start_time: int, end_time: int):
    """
    Retrieve all visits in a Guest site.

    This function retrieves all visits within a specified time range for a given Guest site.
    It handles pagination automatically.

    :param site_id: Unique identifier for the Guest site.
    :param start_time: Start time as a UNIX timestamp.
    :param end_time: End time as a UNIX timestamp.
    :return: JSON response containing all guest visits.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the WorkplaceClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a WorkplaceClient object directly for better performance.
    """
    return _get_default_client().get_all_guest_visits(site_id, start_time, end_time)

@typechecked
def get_guest_sites():
    """
    Returns a list of Guest sites in an organization.

    :return: A dictionary containing guest site objects within the organization.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the WorkplaceClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a WorkplaceClient object directly for better performance.
    """
    return _get_default_client().get_guest_sites()

@typechecked
def get_guest_visits(site_id: str, start_time: int, end_time: int, page_token: Optional[str] = None, page_size: Optional[int] = 100):
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

    ---

    **Note:** This is a functional wrapper for its equivalent method in the WorkplaceClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a WorkplaceClient object directly for better performance.
    """
    return _get_default_client().get_guest_visits(site_id, start_time, end_time, page_token, page_size)

@typechecked
def get_guest_events(site_id: str, start_time: str, end_time: str,
                     limit: Optional[int] = None, cursor: Optional[str] = None):
    """
    Retrieve guest events for a site.

    :param site_id: The unique identifier of the Guest site.
    :param start_time: Start time in ISO 8601 format (e.g. ``'2025-01-17T21:06:20Z'``).
    :param end_time: End time in ISO 8601 format.
    :param limit: Maximum number of items to return (default 100, max 200).
    :param cursor: Pagination cursor for the next page.
    :return: JSON response containing guest events.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the WorkplaceClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a WorkplaceClient object directly for better performance.
    """
    return _get_default_client().get_guest_events(site_id, start_time, end_time, limit, cursor)

@typechecked
def create_guest_event(site_id: str, guest_type_id: str, host_id: str,
                       event_times: List[Dict[str, Any]],
                       event_name: Optional[str] = None,
                       event_address: Optional[str] = None,
                       event_description: Optional[str] = None,
                       invitees: Optional[List[Dict[str, Any]]] = None,
                       rsvp_enabled: Optional[bool] = None,
                       walk_in_enabled: Optional[bool] = None):
    """
    Create a guest event.

    :param site_id: The unique identifier of the Guest site.
    :param guest_type_id: The unique identifier of the guest type.
    :param host_id: The unique identifier of the host.
    :param event_times: List of start/end time objects for the event.
    :param event_name: Optional name for the event.
    :param event_address: Optional location of the event.
    :param event_description: Optional description of the event.
    :param invitees: Optional list of invitee objects.
    :param rsvp_enabled: Whether to generate an RSVP link.
    :param walk_in_enabled: Whether walk-ins are allowed.
    :return: JSON response containing the created event.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the WorkplaceClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a WorkplaceClient object directly for better performance.
    """
    return _get_default_client().create_guest_event(
        site_id, guest_type_id, host_id, event_times,
        event_name, event_address, event_description,
        invitees, rsvp_enabled, walk_in_enabled)

@typechecked
def delete_guest_event(guest_event_id: str):
    """
    Delete a guest event.

    :param guest_event_id: The unique identifier of the guest event.
    :return: JSON response confirming deletion.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the WorkplaceClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a WorkplaceClient object directly for better performance.
    """
    return _get_default_client().delete_guest_event(guest_event_id)

@typechecked
def get_guest_event(guest_event_id: str):
    """
    Retrieve a single guest event by ID.

    :param guest_event_id: The unique identifier of the guest event.
    :return: JSON response containing the guest event.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the WorkplaceClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a WorkplaceClient object directly for better performance.
    """
    return _get_default_client().get_guest_event(guest_event_id)

@typechecked
def get_guest_hosts(site_id: str, email: Optional[str] = None,
                    cursor: Optional[str] = None, limit: Optional[int] = None):
    """
    Retrieve hosts for a Guest site.

    :param site_id: The unique identifier of the Guest site.
    :param email: Optional email to filter to a single host.
    :param cursor: Pagination cursor for the next page.
    :param limit: Maximum number of hosts to return (default 100, max 200).
    :return: JSON response containing hosts.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the WorkplaceClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a WorkplaceClient object directly for better performance.
    """
    return _get_default_client().get_guest_hosts(site_id, email, cursor, limit)

@typechecked
def get_approved_lists(site_id: Optional[str] = None,
                       cursor: Optional[str] = None, limit: Optional[int] = None):
    """
    Retrieve approved lists for the organization or a specific site.

    :param site_id: Optional site ID to filter results.
    :param cursor: Pagination cursor for the next page.
    :param limit: Maximum number of lists to return (default 100, max 1000).
    :return: JSON response containing approved lists.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the WorkplaceClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a WorkplaceClient object directly for better performance.
    """
    return _get_default_client().get_approved_lists(site_id, cursor, limit)

@typechecked
def add_people_to_approved_lists(people: List[Dict[str, Any]]):
    """
    Add people to approved lists.

    :param people: List of people objects to add to approved lists.
    :return: JSON response after adding people.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the WorkplaceClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a WorkplaceClient object directly for better performance.
    """
    return _get_default_client().add_people_to_approved_lists(people)

@typechecked
def remove_people_from_approved_lists(people: List[Dict[str, Any]]):
    """
    Remove people from approved lists.

    :param people: List of people objects to remove from approved lists.
    :return: JSON response after removing people.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the WorkplaceClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a WorkplaceClient object directly for better performance.
    """
    return _get_default_client().remove_people_from_approved_lists(people)

@typechecked
def get_approved_list_members(approved_list_id: str,
                              cursor: Optional[str] = None, limit: Optional[int] = None):
    """
    Retrieve members of a specific approved list.

    :param approved_list_id: The unique identifier of the approved list.
    :param cursor: Pagination cursor for the next page.
    :param limit: Maximum number of members to return (default 100, max 1000).
    :return: JSON response containing list members.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the WorkplaceClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a WorkplaceClient object directly for better performance.
    """
    return _get_default_client().get_approved_list_members(approved_list_id, cursor, limit)

@typechecked
def reset_approved_list(approved_list_id: str):
    """
    Reset an approved list, removing all members.

    :param approved_list_id: The unique identifier of the approved list.
    :return: JSON response after resetting the list.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the WorkplaceClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a WorkplaceClient object directly for better performance.
    """
    return _get_default_client().reset_approved_list(approved_list_id)

@typechecked
def get_guest_types(site_id: str, cursor: Optional[str] = None, limit: Optional[int] = None):
    """
    Retrieve guest types for a site.

    :param site_id: The unique identifier of the Guest site.
    :param cursor: Pagination cursor for the next page.
    :param limit: Maximum number of guest types to return (default 100, max 200).
    :return: JSON response containing guest types.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the WorkplaceClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a WorkplaceClient object directly for better performance.
    """
    return _get_default_client().get_guest_types(site_id, cursor, limit)
