import numpy as np
from typeguard import typechecked
from typing import List, Optional, Dict, Union
from endpoints import SENSOR_ALERT_ENDPOINT, SENSOR_DATA_ENDPOINT
from helpers import remove_null_fields, SENSOR_FIELD_ENUM
from verkada_requests import *

def check_fields(fields):
    if not fields:
        return
    invalid_fields = np.setdiff1d(fields, list(SENSOR_FIELD_ENUM.values()))
    if len(invalid_fields) > 0:
        raise ValueError(f"Sensor field types {invalid_fields} are not in the"
                         f"list of valid types: "
                         f"{list(SENSOR_FIELD_ENUM.values())}")

@typechecked
def get_sensor_alerts(device_ids: List[Union[str, int]],
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

    check_fields(fields)
    params = {
        "device_ids": ",".join(str(id) for id in device_ids),
        "start_time": start_time,
        "end_time": end_time,
        "page_size": page_size,
        "page_token": page_token if page_token else None,
        "fields": ",".join(str(field) for field in fields) if fields else None,
    }
    # Remove keys with a value of None.
    params = remove_null_fields(params)
    return get_request(SENSOR_ALERT_ENDPOINT, params=params)


@typechecked
def get_sensor_data(device_id: str,
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
    :param interval: Time interval for the sensor data (e.g., "5m" for 5 minutes).
    :return: A dictionary representing the JSON response containing sensor data.
    """

    check_fields(fields)

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
    return get_request(SENSOR_DATA_ENDPOINT, params=params)
