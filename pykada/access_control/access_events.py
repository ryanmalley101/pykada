from typeguard import typechecked
from typing import Optional, Dict, Any, List
import time

from pykada.endpoints import ACCESS_EVENTS_ENDPOINT
from pykada.helpers import VALID_ACCESS_EVENT_TYPES_ENUM
from pykada.verkada_requests import *
import numpy as np


@typechecked
def get_access_events(
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    page_token: Optional[str] = None,
    page_size: Optional[int] = 100,
    event_type: Optional[List[str]] = None,
    site_id: Optional[str] = None,
    device_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve access events based on various filters.

    :param start_time: The start of the time range for requested events, as a Unix timestamp in seconds.
                       Defaults to one hour ago from the current time if not provided.
    :param end_time: The end of the time range for requested events, as a Unix timestamp in seconds.
                     Defaults to the current time if not provided.
    :param page_token: The pagination token used to fetch the next page of results.
    :param page_size: The number of items returned in a single response (0 to 200). Defaults to 100.
    :param event_type: One or multiple comma-separated event type values.
    :param site_id: One or multiple comma-separated site identifiers.
    :param device_id: One or multiple comma-separated device identifiers.
    :param user_id: One or multiple comma-separated user identifiers.
    :return: JSON response containing access events matching the provided filters.
    :raises ValueError: If page_size is not between 0 and 200.
    """
    current_time = int(time.time())
    if start_time is None:
        start_time = current_time - 3600  # default to one hour ago
    if end_time is None:
        end_time = current_time

    if (event_type):
        invalid_events = np.setdiff1d(event_type, list(VALID_ACCESS_EVENT_TYPES_ENUM.values()))
        if len(invalid_events) > 0:
            raise ValueError(f"Event types {invalid_events} are not in the "
                             f"list of valid event types: "
                             f"{list(VALID_ACCESS_EVENT_TYPES_ENUM.values())}")

    if page_size is not None and (page_size < 0 or page_size > 200):
        raise ValueError("page_size must be between 0 and 200")

    params = {
        "start_time": start_time,
        "end_time": end_time,
        "page_token": page_token,
        "page_size": page_size,
        "event_type": ",".join(map(str, event_type)) if event_type else None,
        "site_id": site_id,
        "device_id": device_id,
        "user_id": user_id,
    }
    # Remove keys with None values.
    params = {k: v for k, v in params.items() if v is not None}

    return get_request(ACCESS_EVENTS_ENDPOINT, params=params)
