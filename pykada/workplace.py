"""
Workplace (Guest & Mailroom) API client and functional wrappers for pykada.

The :class:`WorkplaceClient` covers Guest events, hosts, guest types and
approved lists through Verkada's v2 Guest API, plus Guest sites, visits and
deny lists, which have no v2 endpoint yet and still use v1.
"""
import base64
from datetime import datetime, timedelta
from typing import Any, Dict, Generator, List, Optional, Union

from typeguard import typechecked

from pykada.api_tokens import VerkadaTokenManager
from pykada.endpoints import (
    GUEST_DENY_LIST_ENDPOINT,
    GUEST_SITES_ENDPOINT,
    GUEST_VISITS_ENDPOINT,
    V2_GUEST_APPROVED_LISTS_ENDPOINT,
    V2_GUEST_EVENTS_ENDPOINT,
    V2_GUEST_HOSTS_ENDPOINT,
    V2_GUEST_TYPES_ENDPOINT,
)
from pykada.helpers import (
    check_limit,
    copy_docstring_from,
    path_segment,
    remove_null_fields,
    require_non_empty_str,
    to_iso8601,
    to_unix_seconds,
)
from pykada.verkada_client import BaseClient
from pykada.verkada_requests import VerkadaRequestManager

Timestamp = Union[datetime, str]

_ONE_DAY_SECONDS = 86400


def _check_people_count(people: List[Dict[str, Any]]) -> None:
    if not 1 <= len(people) <= 100:
        raise ValueError("people must contain between 1 and 100 entries.")


class WorkplaceClient(BaseClient):
    """
    Client for interacting with Verkada's Workplace (Guest & Mailroom) API.
    This client provides methods to manage guest events, hosts, guest types,
    approved lists, visits, deny lists, and sites.
    """

    def __init__(self,
                 api_key: Optional[str] = None,
                 token_manager: Optional[VerkadaTokenManager] = None,
                 request_manager: Optional[VerkadaRequestManager] = None,
                 api_version: Optional[str] = None):
        super().__init__(api_key, token_manager, request_manager, api_version)

    # ------------------------------------------------------------------
    # Sites, visits and deny lists (v1)
    # ------------------------------------------------------------------

    @typechecked
    def get_guest_sites(self) -> Dict[str, Any]:
        """
        Returns the Guest sites in the organization. Uses v1 (no v2 endpoint yet).

        :return: ``{"guest_sites": [{"org_id", "site_id", "site_name"}, ...]}``.
        """
        return self.request_manager.get(GUEST_SITES_ENDPOINT)

    @typechecked
    def get_all_guest_visits(self, site_id: str,
                             start_time: Timestamp,
                             end_time: Timestamp) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every visit at a Guest site in a time range, walking all pages automatically.

        The visits endpoint accepts at most one day per request, so longer
        ranges are fetched as consecutive 24-hour windows.

        :param site_id: The Guest site ID.
        :param start_time: Start of the range, as a timezone-aware ``datetime``
            or ISO 8601 string.
        :param end_time: End of the range.
        :return: A generator that yields individual visit dictionaries.
        :rtype: Generator
        :raises ValueError: If ``site_id`` is empty, a time is invalid, or
            ``end_time`` is before ``start_time``.
        """
        require_non_empty_str(site_id, "site_id")
        start = to_unix_seconds(start_time, "start_time")
        end = to_unix_seconds(end_time, "end_time")
        if end < start:
            raise ValueError("end_time must not be before start_time.")

        def windows():
            window_start = start
            while True:
                window_end = min(window_start + _ONE_DAY_SECONDS, end)
                yield from VerkadaRequestManager.iterate_paginated_results(
                    lambda **kwargs: self._get_guest_visits_page(**kwargs),
                    initial_params={"site_id": site_id, "start_time": window_start,
                                    "end_time": window_end},
                    items_key="visits",
                    next_token_key="next_page_token",
                )
                if window_end >= end:
                    return
                window_start = window_end

        return windows()

    @typechecked
    def get_guest_visits(self, site_id: str,
                         start_time: Timestamp,
                         end_time: Timestamp,
                         page_size: Optional[int] = None,
                         page_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of visits at a Guest site. Uses v1 (no v2 endpoint yet).

        :param site_id: The Guest site ID.
        :param start_time: Start of the range, as a timezone-aware ``datetime``
            or ISO 8601 string.
        :param end_time: End of the range; at most one day after ``start_time``.
            Use :meth:`get_all_guest_visits` for longer ranges.
        :param page_size: Maximum visits per page (1 to 200, server default 100).
        :param page_token: Token from a previous response.
        :return: ``{"visits": [...]}``.
        :raises ValueError: If ``site_id`` is empty, a time is invalid, the
            range exceeds one day, or ``page_size`` is outside 1-200.
        """
        require_non_empty_str(site_id, "site_id")
        start = to_unix_seconds(start_time, "start_time")
        end = to_unix_seconds(end_time, "end_time")
        if abs(end - start) > _ONE_DAY_SECONDS:
            raise ValueError("The time range between start_time and end_time must be "
                             "at most one day; use get_all_guest_visits for longer ranges.")
        return self._get_guest_visits_page(site_id, start, end, page_size, page_token)

    def _get_guest_visits_page(self, site_id: str, start_time: int, end_time: int,
                               page_size: Optional[int] = None,
                               page_token: Optional[str] = None) -> Dict[str, Any]:
        check_limit(page_size, 200, "page_size")
        params = remove_null_fields({
            "site_id": site_id,
            "start_time": start_time,
            "end_time": end_time,
            "page_size": page_size,
            "page_token": page_token,
        })
        return self.request_manager.get(GUEST_VISITS_ENDPOINT, params=params)

    @typechecked
    def create_guest_deny_list(self, filename: str, site_id: str) -> Dict[str, Any]:
        """
        Upload a deny list CSV for a Guest site, replacing any existing one.
        Uses v1 (no v2 endpoint yet).

        :param filename: Path to the deny list CSV.
        :param site_id: The Guest site ID.
        :return: The API response; ``base64_ascii_error_csv`` lists rows that failed.
        :raises ValueError: If ``filename`` or ``site_id`` is empty.
        """
        require_non_empty_str(filename, "filename")
        require_non_empty_str(site_id, "site_id")
        with open(filename, "rb") as file:
            encoded_csv = base64.b64encode(file.read()).decode("ascii")
        return self.request_manager.post(GUEST_DENY_LIST_ENDPOINT,
                                         params={"site_id": site_id},
                                         payload={"base64_ascii_deny_list_csv": encoded_csv})

    @typechecked
    def delete_guest_deny_list(self, site_id: str) -> Dict[str, Any]:
        """
        Delete a Guest site's deny list, including its photos. Uses v1 (no v2
        endpoint yet).

        :param site_id: The Guest site ID.
        :return: The API response.
        :raises ValueError: If ``site_id`` is empty.
        """
        require_non_empty_str(site_id, "site_id")
        return self.request_manager.delete(GUEST_DENY_LIST_ENDPOINT, params={"site_id": site_id})

    # ------------------------------------------------------------------
    # Guest events
    # ------------------------------------------------------------------

    @typechecked
    def get_all_guest_events(self, site_id: str,
                             start_time: Timestamp,
                             end_time: Timestamp) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every Guest event and event part at a site in a time range,
        walking all pages automatically.

        :param site_id: The Guest site ID.
        :param start_time: Start of the range, as a timezone-aware ``datetime``
            or ISO 8601 string.
        :param end_time: End of the range.
        :return: A generator that yields individual event part dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_guest_events(**kwargs),
            initial_params={"site_id": site_id, "start_time": start_time,
                            "end_time": end_time},
        )

    @typechecked
    def get_guest_events(self, site_id: str,
                         start_time: Timestamp,
                         end_time: Timestamp,
                         limit: Optional[int] = None,
                         cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of Guest events and event parts at a site in a time range.

        :param site_id: The Guest site ID.
        :param start_time: Start of the range, as a timezone-aware ``datetime``
            or ISO 8601 string.
        :param end_time: End of the range.
        :param limit: Maximum items per page (1 to 200, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``site_id`` is empty, a time is invalid, or
            ``limit`` is outside 1-200.
        """
        require_non_empty_str(site_id, "site_id")
        check_limit(limit, 200)
        params = remove_null_fields({
            "site_id": site_id,
            "start_time": to_iso8601(start_time, "start_time"),
            "end_time": to_iso8601(end_time, "end_time"),
            "limit": limit,
            "cursor": cursor,
        })
        return self.request_manager.get(V2_GUEST_EVENTS_ENDPOINT, params=params)

    @typechecked
    def create_guest_event(self, site_id: str, guest_type_id: str, host_id: str,
                           event_times: List[Dict[str, Timestamp]],
                           event_name: Optional[str] = None,
                           event_address: Optional[str] = None,
                           event_description: Optional[str] = None,
                           invitees: Optional[List[Dict[str, Any]]] = None,
                           rsvp_enabled: Optional[bool] = None,
                           walk_in_enabled: Optional[bool] = None) -> Dict[str, Any]:
        """
        Create a Guest event, optionally spanning several parts (days).

        :param site_id: The Guest site ID.
        :param guest_type_id: A guest type enabled for invites (see :meth:`get_guest_types`).
        :param host_id: The host ID (see :meth:`get_guest_hosts`).
        :param event_times: 1 to 30 ``{"start_time", "end_time"}`` parts, each a
            timezone-aware ``datetime`` or ISO 8601 string, in the future and
            within a year.
        :param event_name: Defaults to ``"New Event"``.
        :param event_address: Where the event takes place.
        :param event_description: A description of the event.
        :param invitees: Invitees, each with a ``full_name`` (first and last)
            and optional ``email``, ``phone_number`` and ``notes`` (at most 100 characters).
        :param rsvp_enabled: Generate an RSVP link. Defaults to False.
        :param walk_in_enabled: Allow walk-ins. Defaults to False.
        :return: The created event with its parts and invitees.
        :raises ValueError: If an ID is empty, or ``event_times`` or
            ``invitees`` is invalid.
        """
        require_non_empty_str(site_id, "site_id")
        require_non_empty_str(guest_type_id, "guest_type_id")
        require_non_empty_str(host_id, "host_id")
        if not 1 <= len(event_times) <= 30:
            raise ValueError("event_times must contain between 1 and 30 time spans.")
        normalized_times = []
        for idx, span in enumerate(event_times):
            if set(span) != {"start_time", "end_time"}:
                raise ValueError(f"event_times[{idx}] must have exactly start_time and end_time.")
            normalized_times.append({
                "start_time": to_iso8601(span["start_time"], f"event_times[{idx}].start_time"),
                "end_time": to_iso8601(span["end_time"], f"event_times[{idx}].end_time"),
            })
        for idx, invitee in enumerate(invitees or []):
            full_name = invitee.get("full_name")
            if not isinstance(full_name, str) or not full_name.strip():
                raise ValueError(f"invitees[{idx}].full_name must be a non-empty string.")
            if len(invitee.get("notes") or "") > 100:
                raise ValueError(f"invitees[{idx}].notes must be at most 100 characters.")
        payload = remove_null_fields({
            "site_id": site_id,
            "guest_type_id": guest_type_id,
            "host_id": host_id,
            "event_times": normalized_times,
            "event_name": event_name,
            "event_address": event_address,
            "event_description": event_description,
            "invitees": invitees,
            "rsvp_enabled": rsvp_enabled,
            "walk_in_enabled": walk_in_enabled,
        })
        return self.request_manager.post(V2_GUEST_EVENTS_ENDPOINT, payload=payload)

    @typechecked
    def get_guest_event(self, guest_event_id: str) -> Dict[str, Any]:
        """
        Returns a Guest event with its parts and invitees.

        :param guest_event_id: The Guest event ID.
        :return: The Guest event.
        :raises ValueError: If ``guest_event_id`` is empty.
        """
        url = f"{V2_GUEST_EVENTS_ENDPOINT}/{path_segment(guest_event_id, 'guest_event_id')}"
        return self.request_manager.get(url)

    @typechecked
    def delete_guest_event(self, guest_event_id: str) -> Dict[str, Any]:
        """
        Delete a Guest event.

        :param guest_event_id: The Guest event ID.
        :return: An empty dict (the API returns 204 No Content).
        :raises ValueError: If ``guest_event_id`` is empty.
        """
        url = f"{V2_GUEST_EVENTS_ENDPOINT}/{path_segment(guest_event_id, 'guest_event_id')}"
        return self.request_manager.delete(url)

    # ------------------------------------------------------------------
    # Hosts and guest types
    # ------------------------------------------------------------------

    @typechecked
    def get_all_guest_hosts(self, site_id: str) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every host at a Guest site, walking all pages automatically.

        :param site_id: The Guest site ID.
        :return: A generator that yields individual host dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_guest_hosts(**kwargs),
            initial_params={"site_id": site_id},
        )

    @typechecked
    def get_guest_hosts(self, site_id: str,
                        email: Optional[str] = None,
                        limit: Optional[int] = None,
                        cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of hosts at a Guest site, or the host with an email.

        :param site_id: The Guest site ID.
        :param email: Only return the host with this email.
        :param limit: Maximum hosts per page (1 to 200, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``site_id`` is empty or ``limit`` is outside 1-200.
        """
        require_non_empty_str(site_id, "site_id")
        check_limit(limit, 200)
        params = remove_null_fields({"site_id": site_id, "email": email,
                                     "limit": limit, "cursor": cursor})
        return self.request_manager.get(V2_GUEST_HOSTS_ENDPOINT, params=params)

    @typechecked
    def get_all_guest_types(self, site_id: str) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every guest type at a Guest site, walking all pages automatically.

        :param site_id: The Guest site ID.
        :return: A generator that yields individual guest type dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_guest_types(**kwargs),
            initial_params={"site_id": site_id},
        )

    @typechecked
    def get_guest_types(self, site_id: str,
                        limit: Optional[int] = None,
                        cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of guest types at a Guest site.

        Each item has a ``guest_type_id``, ``name`` and ``enabled_for_invites``.

        :param site_id: The Guest site ID.
        :param limit: Maximum guest types per page (1 to 200, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``site_id`` is empty or ``limit`` is outside 1-200.
        """
        require_non_empty_str(site_id, "site_id")
        check_limit(limit, 200)
        params = remove_null_fields({"site_id": site_id, "limit": limit, "cursor": cursor})
        return self.request_manager.get(V2_GUEST_TYPES_ENDPOINT, params=params)

    # ------------------------------------------------------------------
    # Approved lists
    # ------------------------------------------------------------------

    @typechecked
    def get_all_approved_lists(self, site_id: Optional[str] = None
                               ) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every approved list, walking all pages automatically.

        :param site_id: Only return lists applied to this site. Defaults to all.
        :return: A generator that yields individual approved list dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_approved_lists(**kwargs),
            initial_params={"site_id": site_id},
        )

    @typechecked
    def get_approved_lists(self, site_id: Optional[str] = None,
                           limit: Optional[int] = None,
                           cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of approved lists for the organization or a site.

        :param site_id: Only return lists applied to this site. Defaults to all.
        :param limit: Maximum lists per page (1 to 1000, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``limit`` is outside 1-1000.
        """
        check_limit(limit, 1000)
        params = remove_null_fields({"site_id": site_id, "limit": limit, "cursor": cursor})
        return self.request_manager.get(V2_GUEST_APPROVED_LISTS_ENDPOINT, params=params)

    @typechecked
    def get_all_approved_list_members(self, approved_list_id: str
                                      ) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every unexpired member of an approved list, walking all pages automatically.

        :param approved_list_id: The approved list ID.
        :return: A generator that yields individual person dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_approved_list_members(**kwargs),
            initial_params={"approved_list_id": approved_list_id},
            items_key="people",
        )

    @typechecked
    def get_approved_list_members(self, approved_list_id: str,
                                  limit: Optional[int] = None,
                                  cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of an approved list's unexpired members.

        :param approved_list_id: The approved list ID.
        :param limit: Maximum people per page (1 to 1000, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"people": [...], "cursor": str | None}``.
        :raises ValueError: If ``approved_list_id`` is empty or ``limit`` is outside 1-1000.
        """
        check_limit(limit, 1000)
        url = (f"{V2_GUEST_APPROVED_LISTS_ENDPOINT}/"
               f"{path_segment(approved_list_id, 'approved_list_id')}")
        params = remove_null_fields({"limit": limit, "cursor": cursor})
        return self.request_manager.get(url, params=params)

    @typechecked
    def add_people_to_approved_lists(self, people: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add people to approved lists. Idempotent: people are matched by
        ``external_id``, then by email, so repeating a call doesn't duplicate them.

        :param people: 1 to 100 people, each with ``full_name``, ``email`` and
            ``approved_list_ids`` (1 to 10), and optionally ``external_id``,
            ``phone_number``, ``address``, ``date_of_birth`` (``YYYY-MM-DD``)
            and an ISO 8601 ``expiration_timestamp``.
        :return: ``{"count": int}``, the number of records changed.
        :raises ValueError: If ``people`` doesn't have 1-100 entries.
        """
        _check_people_count(people)
        return self.request_manager.patch(f"{V2_GUEST_APPROVED_LISTS_ENDPOINT}/add",
                                          payload={"people": people})

    @typechecked
    def remove_people_from_approved_lists(self, people: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Remove people from approved lists.

        :param people: 1 to 100 entries, each with exactly one of ``person_id``
            or ``external_id``, and optional ``approved_list_ids`` (omit to
            remove the person from every list).
        :return: ``{"count": int}``, the number of records changed.
        :raises ValueError: If ``people`` doesn't have 1-100 entries.
        """
        _check_people_count(people)
        return self.request_manager.patch(f"{V2_GUEST_APPROVED_LISTS_ENDPOINT}/remove",
                                          payload={"people": people})

    @typechecked
    def reset_approved_list(self, approved_list_id: str) -> Dict[str, Any]:
        """
        Remove every member of an approved list.

        :param approved_list_id: The approved list ID.
        :return: ``{"count": int}``, the number of members removed.
        :raises ValueError: If ``approved_list_id`` is empty.
        """
        url = (f"{V2_GUEST_APPROVED_LISTS_ENDPOINT}/"
               f"{path_segment(approved_list_id, 'approved_list_id')}/reset")
        return self.request_manager.patch(url)


# ---------------------------------------------------------------------------
# Module-level default client — shared across all functional wrappers.
# ---------------------------------------------------------------------------
_default_workplace_client: Optional[WorkplaceClient] = None


def _get_default_client() -> WorkplaceClient:
    global _default_workplace_client
    if _default_workplace_client is None:
        _default_workplace_client = WorkplaceClient()
    return _default_workplace_client


_WRAPPER_NOTE = ("This is a functional wrapper for its equivalent method in the "
                 "WorkplaceClient. It reuses a module-level client configured from "
                 "VERKADA_API_KEY, making it best for one-off scripts. For "
                 "multiple API calls or a non-default key, instantiate a "
                 "WorkplaceClient directly.")


@copy_docstring_from(WorkplaceClient.get_guest_sites, note=_WRAPPER_NOTE)
@typechecked
def get_guest_sites():
    return _get_default_client().get_guest_sites()


@copy_docstring_from(WorkplaceClient.get_all_guest_visits, note=_WRAPPER_NOTE)
@typechecked
def get_all_guest_visits(site_id: str, start_time: Timestamp, end_time: Timestamp):
    return _get_default_client().get_all_guest_visits(site_id, start_time, end_time)


@copy_docstring_from(WorkplaceClient.get_guest_visits, note=_WRAPPER_NOTE)
@typechecked
def get_guest_visits(site_id: str, start_time: Timestamp, end_time: Timestamp,
                     page_size: Optional[int] = None, page_token: Optional[str] = None):
    return _get_default_client().get_guest_visits(site_id, start_time, end_time,
                                                  page_size, page_token)


@copy_docstring_from(WorkplaceClient.create_guest_deny_list, note=_WRAPPER_NOTE)
@typechecked
def create_guest_deny_list(filename: str, site_id: str):
    return _get_default_client().create_guest_deny_list(filename, site_id)


@copy_docstring_from(WorkplaceClient.delete_guest_deny_list, note=_WRAPPER_NOTE)
@typechecked
def delete_guest_deny_list(site_id: str):
    return _get_default_client().delete_guest_deny_list(site_id)


@copy_docstring_from(WorkplaceClient.get_all_guest_events, note=_WRAPPER_NOTE)
@typechecked
def get_all_guest_events(site_id: str, start_time: Timestamp, end_time: Timestamp):
    return _get_default_client().get_all_guest_events(site_id, start_time, end_time)


@copy_docstring_from(WorkplaceClient.get_guest_events, note=_WRAPPER_NOTE)
@typechecked
def get_guest_events(site_id: str, start_time: Timestamp, end_time: Timestamp,
                     limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().get_guest_events(site_id, start_time, end_time,
                                                  limit, cursor)


@copy_docstring_from(WorkplaceClient.create_guest_event, note=_WRAPPER_NOTE)
@typechecked
def create_guest_event(site_id: str, guest_type_id: str, host_id: str,
                       event_times: List[Dict[str, Timestamp]],
                       event_name: Optional[str] = None,
                       event_address: Optional[str] = None,
                       event_description: Optional[str] = None,
                       invitees: Optional[List[Dict[str, Any]]] = None,
                       rsvp_enabled: Optional[bool] = None,
                       walk_in_enabled: Optional[bool] = None):
    return _get_default_client().create_guest_event(
        site_id, guest_type_id, host_id, event_times, event_name, event_address,
        event_description, invitees, rsvp_enabled, walk_in_enabled)


@copy_docstring_from(WorkplaceClient.get_guest_event, note=_WRAPPER_NOTE)
@typechecked
def get_guest_event(guest_event_id: str):
    return _get_default_client().get_guest_event(guest_event_id)


@copy_docstring_from(WorkplaceClient.delete_guest_event, note=_WRAPPER_NOTE)
@typechecked
def delete_guest_event(guest_event_id: str):
    return _get_default_client().delete_guest_event(guest_event_id)


@copy_docstring_from(WorkplaceClient.get_all_guest_hosts, note=_WRAPPER_NOTE)
@typechecked
def get_all_guest_hosts(site_id: str):
    return _get_default_client().get_all_guest_hosts(site_id)


@copy_docstring_from(WorkplaceClient.get_guest_hosts, note=_WRAPPER_NOTE)
@typechecked
def get_guest_hosts(site_id: str, email: Optional[str] = None,
                    limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().get_guest_hosts(site_id, email, limit, cursor)


@copy_docstring_from(WorkplaceClient.get_all_guest_types, note=_WRAPPER_NOTE)
@typechecked
def get_all_guest_types(site_id: str):
    return _get_default_client().get_all_guest_types(site_id)


@copy_docstring_from(WorkplaceClient.get_guest_types, note=_WRAPPER_NOTE)
@typechecked
def get_guest_types(site_id: str, limit: Optional[int] = None,
                    cursor: Optional[str] = None):
    return _get_default_client().get_guest_types(site_id, limit, cursor)


@copy_docstring_from(WorkplaceClient.get_all_approved_lists, note=_WRAPPER_NOTE)
@typechecked
def get_all_approved_lists(site_id: Optional[str] = None):
    return _get_default_client().get_all_approved_lists(site_id)


@copy_docstring_from(WorkplaceClient.get_approved_lists, note=_WRAPPER_NOTE)
@typechecked
def get_approved_lists(site_id: Optional[str] = None, limit: Optional[int] = None,
                       cursor: Optional[str] = None):
    return _get_default_client().get_approved_lists(site_id, limit, cursor)


@copy_docstring_from(WorkplaceClient.get_all_approved_list_members, note=_WRAPPER_NOTE)
@typechecked
def get_all_approved_list_members(approved_list_id: str):
    return _get_default_client().get_all_approved_list_members(approved_list_id)


@copy_docstring_from(WorkplaceClient.get_approved_list_members, note=_WRAPPER_NOTE)
@typechecked
def get_approved_list_members(approved_list_id: str, limit: Optional[int] = None,
                              cursor: Optional[str] = None):
    return _get_default_client().get_approved_list_members(approved_list_id, limit, cursor)


@copy_docstring_from(WorkplaceClient.add_people_to_approved_lists, note=_WRAPPER_NOTE)
@typechecked
def add_people_to_approved_lists(people: List[Dict[str, Any]]):
    return _get_default_client().add_people_to_approved_lists(people)


@copy_docstring_from(WorkplaceClient.remove_people_from_approved_lists, note=_WRAPPER_NOTE)
@typechecked
def remove_people_from_approved_lists(people: List[Dict[str, Any]]):
    return _get_default_client().remove_people_from_approved_lists(people)


@copy_docstring_from(WorkplaceClient.reset_approved_list, note=_WRAPPER_NOTE)
@typechecked
def reset_approved_list(approved_list_id: str):
    return _get_default_client().reset_approved_list(approved_list_id)
