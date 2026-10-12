"""
Events API client and functional wrappers for pykada.

The :class:`EventsClient` reads the unified v2 event feed, which returns
camera, access control, sensor, and intercom events from one endpoint. It
replaces the v1 camera alerts and access events endpoints.

Each event has ``event_id``, ``device_id``, ``device_type``, ``event_type``,
an RFC 3339 ``timestamp``, and a product-specific ``event_info`` object;
``device_type`` (``"camera"``, ``"access_control"``, ``"sensor"`` or
``"intercom"``) tells you which ``event_info`` shape to expect.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Generator, List, Optional, Union

from typeguard import typechecked

from pykada.api_tokens import VerkadaTokenManager
from pykada.endpoints import V2_EVENTS_ENDPOINT
from pykada.enums import EVENT_PRODUCT_TYPES_ENUM
from pykada.helpers import copy_docstring_from, remove_null_fields, to_iso8601
from pykada.verkada_client import BaseClient
from pykada.verkada_requests import VerkadaRequestManager

Timestamp = Union[datetime, str]


def _check_product_types(product_types: Optional[List[str]]) -> None:
    if not product_types:
        return
    valid = set(EVENT_PRODUCT_TYPES_ENUM.values())
    invalid = set(product_types) - valid
    if invalid:
        raise ValueError(
            f"Product types {invalid} are not in the list of valid types: "
            f"{sorted(valid)}"
        )


def _join(values: Optional[List[str]]) -> Optional[str]:
    return ",".join(values) if values else None


class EventsClient(BaseClient):
    """
    Client for Verkada's unified v2 Events API.

    Use it for anything that previously used camera alerts
    (``/cameras/v1/alerts``) or access events (``/events/v1/access``).
    """

    def __init__(self,
                 api_key: Optional[str] = None,
                 token_manager: Optional[VerkadaTokenManager] = None,
                 request_manager: Optional[VerkadaRequestManager] = None,
                 api_version: Optional[str] = None):
        super().__init__(api_key, token_manager, request_manager, api_version)

    @typechecked
    def get_all_events(self,
                       start_time: Optional[Timestamp] = None,
                       end_time: Optional[Timestamp] = None,
                       product_types: Optional[List[str]] = None,
                       event_types: Optional[List[str]] = None,
                       device_ids: Optional[List[str]] = None,
                       site_ids: Optional[List[str]] = None
                       ) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every matching event in a time range, walking all pages automatically.

        If ``end_time`` is omitted it is pinned to the current time before the
        first request, so events arriving while paginating can't shift items
        between pages.

        :param start_time: Start of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to one hour before ``end_time``.
        :param end_time: End of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to now.
        :param product_types: Only return events from these products
            (see :data:`pykada.enums.EVENT_PRODUCT_TYPES_ENUM`). Defaults to all.
        :param event_types: Only return these event types, e.g. ``["motion"]``.
            Valid values depend on the product; see
            :data:`pykada.enums.CAMERA_EVENT_TYPES_ENUM`,
            :data:`pykada.enums.VALID_ACCESS_EVENT_TYPES_ENUM` and
            :data:`pykada.enums.SENSOR_EVENT_TYPES_ENUM`.
        :param device_ids: Only return events from these devices.
        :param site_ids: Only return events from these sites (applies to
            access control events).
        :return: A generator that yields individual event dictionaries.
        :rtype: Generator
        :raises ValueError: If ``product_types`` contains an unknown value.
        """
        _check_product_types(product_types)
        if end_time is None:
            end_time = datetime.now(timezone.utc)
        params = {
            "start_time": start_time,
            "end_time": end_time,
            "product_types": product_types,
            "event_types": event_types,
            "device_ids": device_ids,
            "site_ids": site_ids,
        }
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_events(**kwargs),
            initial_params=params,
        )

    @typechecked
    def get_events(self,
                   start_time: Optional[Timestamp] = None,
                   end_time: Optional[Timestamp] = None,
                   product_types: Optional[List[str]] = None,
                   event_types: Optional[List[str]] = None,
                   device_ids: Optional[List[str]] = None,
                   site_ids: Optional[List[str]] = None,
                   limit: Optional[int] = None,
                   cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of events from cameras, access control, sensors and intercoms.

        Unlike the v1 access events endpoint, there is no ``user_id`` filter;
        filter on ``event["event_info"]["user_info"]`` client-side instead.
        Camera events no longer include image URLs.

        :param start_time: Start of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to one hour before ``end_time``.
        :param end_time: End of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to now.
        :param product_types: Only return events from these products
            (see :data:`pykada.enums.EVENT_PRODUCT_TYPES_ENUM`). Defaults to all.
        :param event_types: Only return these event types, e.g. ``["motion"]``.
            Valid values depend on the product; see
            :data:`pykada.enums.CAMERA_EVENT_TYPES_ENUM`,
            :data:`pykada.enums.VALID_ACCESS_EVENT_TYPES_ENUM` and
            :data:`pykada.enums.SENSOR_EVENT_TYPES_ENUM`.
        :param device_ids: Only return events from these devices.
        :param site_ids: Only return events from these sites (applies to
            access control events).
        :param limit: Maximum events per page (1 to 200, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``product_types`` contains an unknown value,
            ``limit`` is outside 1-200, or a timestamp is invalid.
        """
        _check_product_types(product_types)
        if limit is not None and not 1 <= limit <= 200:
            raise ValueError("limit must be between 1 and 200")

        params = remove_null_fields({
            "start_time": to_iso8601(start_time, "start_time"),
            "end_time": to_iso8601(end_time, "end_time"),
            "product_types": _join(product_types),
            "event_types": _join(event_types),
            "device_ids": _join(device_ids),
            "site_ids": _join(site_ids),
            "limit": limit,
            "cursor": cursor,
        })
        return self.request_manager.get(V2_EVENTS_ENDPOINT, params=params)


# ---------------------------------------------------------------------------
# Module-level default client — shared across all functional wrappers.
# ---------------------------------------------------------------------------
_default_events_client: Optional[EventsClient] = None


def _get_default_client() -> EventsClient:
    global _default_events_client
    if _default_events_client is None:
        _default_events_client = EventsClient()
    return _default_events_client


_WRAPPER_NOTE = ("This is a functional wrapper for its equivalent method in the "
                 "EventsClient. It reuses a module-level client configured from "
                 "VERKADA_API_KEY, making it best for one-off scripts. For "
                 "multiple API calls or a non-default key, instantiate an "
                 "EventsClient directly.")


@copy_docstring_from(EventsClient.get_all_events, note=_WRAPPER_NOTE)
@typechecked
def get_all_events(start_time: Optional[Timestamp] = None,
                   end_time: Optional[Timestamp] = None,
                   product_types: Optional[List[str]] = None,
                   event_types: Optional[List[str]] = None,
                   device_ids: Optional[List[str]] = None,
                   site_ids: Optional[List[str]] = None):
    return _get_default_client().get_all_events(start_time, end_time, product_types,
                                                event_types, device_ids, site_ids)


@copy_docstring_from(EventsClient.get_events, note=_WRAPPER_NOTE)
@typechecked
def get_events(start_time: Optional[Timestamp] = None,
               end_time: Optional[Timestamp] = None,
               product_types: Optional[List[str]] = None,
               event_types: Optional[List[str]] = None,
               device_ids: Optional[List[str]] = None,
               site_ids: Optional[List[str]] = None,
               limit: Optional[int] = None,
               cursor: Optional[str] = None):
    return _get_default_client().get_events(start_time, end_time, product_types,
                                            event_types, device_ids, site_ids,
                                            limit, cursor)
