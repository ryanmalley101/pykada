from typeguard import typechecked
from typing import Dict, Any, Optional, List

from pykada.api_tokens import VerkadaTokenManager, get_default_token_manager
from pykada.endpoints import ALARMS_DEVICES_ENDPOINT, ALARMS_SITES_ENDPOINT
from pykada.verkada_requests import *

class ClassicAlarmsClient:
    """
    Client for interacting with Verkada's Classic Alarms API.
    This client provides methods to retrieve alarm devices and site information.
    """

    def __init__(self, api_key=None,
                 token_manager: VerkadaTokenManager = None):
        if not api_key and not token_manager:
            raise ValueError(
                "Either api_key or token_manager must be provided.")
        if token_manager and api_key:
            raise ValueError("Cannot provide both api_key and token_manager. "
                             "Use one or the other.")
        # If api_key is provided, create a VerkadaTokenManager instance.
        if token_manager:
            if not isinstance(token_manager, VerkadaTokenManager):
                raise TypeError(
                    "token_manager must be an instance of VerkadaTokenManager.")
            self.token_manager = token_manager
            return

        # If api_key is provided, create a VerkadaTokenManager instance.
        if api_key and not isinstance(api_key, str):
            raise TypeError("api_key must be a string.")
        if api_key and not api_key.strip():
            raise ValueError("api_key must be a non-empty string.")
        if api_key and len(api_key) < 20:
            raise ValueError("api_key must be at least 20 characters long.")

        # Create a VerkadaTokenManager instance with the provided api_key.
        self.token_manager = VerkadaTokenManager(api_key=api_key) \
            if api_key else get_default_token_manager()

    @typechecked
    def get_alarm_devices(self, site_id: str, device_ids: Optional[List[str]] = None) -> \
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

        return get_request(ALARMS_DEVICES_ENDPOINT, params=params, token_manager=self.token_manager)


    @typechecked
    def get_alarm_site_information(self, site_ids: Optional[List[str]] = None)\
            -> Dict[str, Any]:
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

        return get_request(ALARMS_SITES_ENDPOINT, params=params, token_manager=self.token_manager)

@typechecked
def get_alarm_devices(site_id: str, device_ids: Optional[List[str]] = None):
    """
    Retrieve alarm devices for a given site.

    Gets information about all devices in an alarm site specified by site_id.
    Optionally, a subset of devices can be returned by providing a list of device IDs.

    :param site_id: The unique identifier for the site. (Required)
    :param device_ids: Optional list of device unique identifiers to filter the results.
    :return: JSON response containing device information.
    :raises ValueError: If site_id is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the ClassicAlarmsClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an ClassicAlarmsClient object directly for better performance.
    """
    return ClassicAlarmsClient().get_alarm_devices(site_id, device_ids)

@typechecked
def get_alarm_site_information(site_ids: Optional[List[str]] = None):
    """
    Retrieve information about alarm sites.

    Returns information about a list of alarm sites. If no site_ids are provided,
    information on all sites will be returned.

    :param site_ids: Optional list of site unique identifiers.
    :return: JSON response containing site information.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the ClassicAlarmsClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an ClassicAlarmsClient object directly for better performance.
    """
    return ClassicAlarmsClient().get_alarm_site_information(site_ids)