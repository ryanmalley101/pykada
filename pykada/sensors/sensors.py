import numpy as np
from typeguard import typechecked
from typing import List, Dict, Any, Generator

from pykada.api_tokens import VerkadaTokenManager, get_default_token_manager
from pykada.endpoints import SENSOR_ALERT_ENDPOINT, SENSOR_DATA_ENDPOINT
from pykada.helpers import remove_null_fields, SENSOR_FIELD_ENUM
from pykada.verkada_requests import *

def check_sensor_fields(fields):
    """
    Check if the provided sensor fields are valid.
    :param fields: List of sensor fields to check.
    """
    if not fields:
        return
    invalid_fields = np.setdiff1d(fields, list(SENSOR_FIELD_ENUM.values()))
    if len(invalid_fields) > 0:
        raise ValueError(f"Sensor field types {invalid_fields} are not in the"
                         f"list of valid types: "
                         f"{list(SENSOR_FIELD_ENUM.values())}")


class SensorsClient:
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

    def get_all_sensor_alerts(
        self,
        device_ids: List[str],
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        fields: Optional[List[str]] = None
    ) -> Generator[Any, None, None]:
        """
        Returns all alerts for a set of sensors in an organization over a specified time range.

        :param device_ids: List of sensor IDs.
        :param start_time: Start time (Unix timestamp in seconds).
        :param end_time: End time (Unix timestamp in seconds).
        :param fields: List of sensor fields to filter alerts.
        :return: A dictionary representing the JSON response containing sensor alerts.
        :raises ValueError: If device_ids is an empty list.
        """
        if not device_ids:
            raise ValueError("device_ids must be a non-empty list")

        check_sensor_fields(fields)
        params = {
            "device_ids": device_ids,
            "start_time": start_time,
            "end_time": end_time,
            "fields": fields,
        }
        return iterate_paginated_results(
            get_sensor_alerts,
            items_key="alert_events",
            next_token_key="page_cursor",
            initial_params=params
        )


    @typechecked
    def get_sensor_alerts(self,
                          device_ids: List[str],
                          start_time: Optional[int] = None,
                          end_time: Optional[int] = None,
                          page_size: Optional[int] = None,
                          page_token: Optional[str] = None,
                          fields: Optional[List[str]] = None) -> Dict:
        """
        Returns all alerts for a set of sensors in an organization over a specified time range.

        :param device_ids: List of sensor IDs.
        :param start_time: Start time (Unix timestamp in seconds).
        :param end_time: End time (Unix timestamp in seconds).
        :param page_size: Number of items per page.
        :param page_token: Token for pagination.
        :param fields: List of sensor fields to filter alerts.
        :return: A dictionary representing the JSON response containing sensor alerts.
        :raises ValueError: If device_ids is an empty list.
        """
        if not device_ids:
            raise ValueError("device_ids must be a non-empty list")

        check_sensor_fields(fields)

        params = {
            "device_ids": ",".join(device_id for device_id in device_ids),
            "start_time": start_time,
            "end_time": end_time,
            "page_size": page_size,
            "page_token": page_token if page_token else None,
            "fields": ",".join(field for field in fields) if fields else None,
        }

        # Remove keys with a value of None.
        params = remove_null_fields(params)
        return get_request(SENSOR_ALERT_ENDPOINT, params=params, token_manager=self.token_manager)

    def get_all_sensor_data(
        self,
        device_id: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        fields: Optional[List[str]] = None,
        interval: Optional[str] = None
    ) -> Generator[Any, None, None]:
        """
        Returns sensor readings for a particular sensor over a specified time range.

        :param device_id: The unique identifier of the sensor.
        :param start_time: Start time for sensor data (Unix timestamp in seconds).
        :param end_time: End time for sensor data (Unix timestamp in seconds).
        :param fields: List of sensor fields to include in the response.
        :param interval: The time interval for the requested sensor data.
        Data is stored with 1 second intervals for 30 days, and
        with 5 minute intervals for data between 30 days and 365 days old.
        A valid value for this field is a number followed by a supported format.
        Supported formats are s, m, and h for seconds, minutes, and hours,
        respectively. For example, 5m would specify a 5 minutes interval for the
        data. If left blank, a default resolution will be calculated based on
        time range.
        :return: A dictionary representing the JSON response containing sensor data.
        """

        check_sensor_fields(fields)

        params = {
            "device_id": device_id,
            "start_time": start_time,
            "end_time": end_time,
            "fields": fields,
            "interval": interval if interval else None,
        }

        params = remove_null_fields(params)

        return iterate_paginated_results(
            get_sensor_data,
            items_key="data",
            next_token_key="page_cursor",
            initial_params=params
        )


    @typechecked
    def get_sensor_data(self,
                        device_id: str,
                        start_time: Optional[int] = None,
                        end_time: Optional[int] = None,
                        page_size: Optional[int] = None,
                        page_token: Optional[str] = None,
                        fields: Optional[List[str]] = None,
                        interval: Optional[str] = None) -> Dict:
        """
        Returns sensor readings for a particular sensor over a specified time range.

        :param device_id: The unique identifier of the sensor.
        :param start_time: Start time for sensor data (Unix timestamp in seconds).
        :param end_time: End time for sensor data (Unix timestamp in seconds).
        :param page_size: Number of items per page.
        :param page_token: Token for pagination.
        :param fields: List of sensor fields to include in the response.
        :param interval: The time interval for the requested sensor data.
        Data is stored with 1 second intervals for 30 days, and
        with 5 minute intervals for data between 30 days and 365 days old.
        A valid value for this field is a number followed by a supported format.
        Supported formats are s, m, and h for seconds, minutes, and hours,
        respectively. For example, 5m would specify a 5 minutes interval for the
        data. If left blank, a default resolution will be calculated based on
        time range.
        :return: A dictionary representing the JSON response containing sensor data.
        """

        check_sensor_fields(fields)

        params = {
            "device_id": device_id,
            "start_time": start_time,
            "end_time": end_time,
            "page_size": page_size,
            "page_token": page_token if page_token else None,
            "fields": ",".join(str(field) for field in fields) if fields else None,
            "interval": interval if interval else None,
        }
        params = remove_null_fields(params)
        return get_request(SENSOR_DATA_ENDPOINT, params=params, token_manager=self.token_manager)


@typechecked
def get_all_sensor_alerts(device_ids: List[str], start_time: Optional[int] = None, end_time: Optional[int] = None, fields: Optional[List[str]] = None):
    """
    Returns all alerts for a set of sensors in an organization over a specified time range.

    :param device_ids: List of sensor IDs.
    :param start_time: Start time (Unix timestamp in seconds).
    :param end_time: End time (Unix timestamp in seconds).
    :param fields: List of sensor fields to filter alerts.
    :return: A dictionary representing the JSON response containing sensor alerts.
    :raises ValueError: If device_ids is an empty list.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the SensorsClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a SensorsClient object directly for better performance.
    """
    return SensorsClient().get_all_sensor_alerts(device_ids, start_time, end_time, fields)

@typechecked
def get_all_sensor_data(device_id: str, start_time: Optional[int] = None, end_time: Optional[int] = None, fields: Optional[List[str]] = None, interval: Optional[str] = None):
    """
    Returns sensor readings for a particular sensor over a specified time range.

    :param device_id: The unique identifier of the sensor.
    :param start_time: Start time for sensor data (Unix timestamp in seconds).
    :param end_time: End time for sensor data (Unix timestamp in seconds).
    :param fields: List of sensor fields to include in the response.
    :param interval: The time interval for the requested sensor data.
    Data is stored with 1 second intervals for 30 days, and
    with 5 minute intervals for data between 30 days and 365 days old.
    A valid value for this field is a number followed by a supported format.
    Supported formats are s, m, and h for seconds, minutes, and hours,
    respectively. For example, 5m would specify a 5 minutes interval for the
    data. If left blank, a default resolution will be calculated based on
    time range.
    :return: A dictionary representing the JSON response containing sensor data.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the SensorsClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a SensorsClient object directly for better performance.
    """
    return SensorsClient().get_all_sensor_data(device_id, start_time, end_time, fields, interval)

@typechecked
def get_sensor_alerts(device_ids: List[str], start_time: Optional[int] = None, end_time: Optional[int] = None, page_size: Optional[int] = None, page_token: Optional[str] = None, fields: Optional[List[str]] = None):
    """
    Returns all alerts for a set of sensors in an organization over a specified time range.

    :param device_ids: List of sensor IDs.
    :param start_time: Start time (Unix timestamp in seconds).
    :param end_time: End time (Unix timestamp in seconds).
    :param page_size: Number of items per page.
    :param page_token: Token for pagination.
    :param fields: List of sensor fields to filter alerts.
    :return: A dictionary representing the JSON response containing sensor alerts.
    :raises ValueError: If device_ids is an empty list.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the SensorsClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a SensorsClient object directly for better performance.
    """
    return SensorsClient().get_sensor_alerts(device_ids, start_time, end_time, page_size, page_token, fields)

@typechecked
def get_sensor_data(device_id: str, start_time: Optional[int] = None, end_time: Optional[int] = None, page_size: Optional[int] = None, page_token: Optional[str] = None, fields: Optional[List[str]] = None, interval: Optional[str] = None):
    """
    Returns sensor readings for a particular sensor over a specified time range.

    :param device_id: The unique identifier of the sensor.
    :param start_time: Start time for sensor data (Unix timestamp in seconds).
    :param end_time: End time for sensor data (Unix timestamp in seconds).
    :param page_size: Number of items per page.
    :param page_token: Token for pagination.
    :param fields: List of sensor fields to include in the response.
    :param interval: The time interval for the requested sensor data.
    Data is stored with 1 second intervals for 30 days, and
    with 5 minute intervals for data between 30 days and 365 days old.
    A valid value for this field is a number followed by a supported format.
    Supported formats are s, m, and h for seconds, minutes, and hours,
    respectively. For example, 5m would specify a 5 minutes interval for the
    data. If left blank, a default resolution will be calculated based on
    time range.
    :return: A dictionary representing the JSON response containing sensor data.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the SensorsClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a SensorsClient object directly for better performance.
    """
    return SensorsClient().get_sensor_data(device_id, start_time, end_time, page_size, page_token, fields, interval)
