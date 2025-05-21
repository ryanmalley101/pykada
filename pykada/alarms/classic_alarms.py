from typeguard import typechecked
from typing import Dict, Any, Optional, List

from pykada.endpoints import ALARMS_DEVICES_ENDPOINT, ALARMS_SITES_ENDPOINT
from pykada.verkada_requests import *


@typechecked
def get_alarm_devices(site_id: str, device_ids: Optional[List[str]] = None) -> \
Dict[str, Any]:
    """
    Retrieve alarm devices for a given site.

    Gets information about all devices in an alarm site specified by site_id.
    Optionally, a subset of devices can be returned by providing a list of device IDs.

    :param site_id: The unique identifier for the site. (Required)
    :param device_ids: Optional list of device unique identifiers to filter the results.
    :return: JSON response containing device information.
    :raises ValueError: If site_id is an empty string.
    """
    if not site_id or not site_id.strip():
        raise ValueError("site_id must be a non-empty string")

    params: Dict[str, Any] = {"site_id": site_id}
    if device_ids:
        params["device_ids"] = ",".join(device_ids)

    return get_request(ALARMS_DEVICES_ENDPOINT, params=params)


@typechecked
def get_alarm_site_information(site_ids: Optional[List[str]] = None) -> Dict[
    str, Any]:
    """
    Retrieve information about alarm sites.

    Returns information about a list of alarm sites. If no site_ids are provided,
    information on all sites will be returned.

    :param site_ids: Optional list of site unique identifiers.
    :return: JSON response containing site information.
    """
    params: Dict[str, Any] = {}
    if site_ids:
        params["site_ids"] = ",".join(site_ids)

    return get_request(ALARMS_SITES_ENDPOINT, params=params)
