"""
Environmental Sensors API client and functional wrappers for pykada.

The :class:`SensorsClient` lists an organization's environmental sensors and
retrieves their alert history and time-series readings (temperature,
humidity, air quality, etc.) through Verkada's v2 Environment API.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Generator, List, Optional, Union

from typeguard import typechecked

from pykada.api_tokens import VerkadaTokenManager
from pykada.endpoints import V2_SENSOR_ALERTS_ENDPOINT, V2_SENSORS_ENDPOINT
from pykada.enums import SENSOR_FIELD_ENUM
from pykada.helpers import (
    check_limit,
    copy_docstring_from,
    path_segment,
    remove_null_fields,
    to_iso8601,
    to_iso8601_duration,
)
from pykada.verkada_client import BaseClient
from pykada.verkada_requests import VerkadaRequestManager

Timestamp = Union[datetime, str]
Duration = Union[timedelta, str]


def check_sensor_fields(fields):
    """
    Check if the provided sensor fields are valid.
    :param fields: List of sensor fields to check.
    """
    if not fields:
        return
    valid = set(SENSOR_FIELD_ENUM.values())
    invalid_fields = set(fields) - valid
    if invalid_fields:
        raise ValueError(
            f"Sensor field types {invalid_fields} are not in the "
            f"list of valid types: {list(valid)}"
        )


class SensorsClient(BaseClient):
    """
    Client for interacting with Verkada's Environmental Sensors API.
    This client provides methods to list sensors and retrieve sensor alerts
    and sensor data.
    """

    @typechecked
    def __init__(self,
                 api_key: Optional[str] = None,
                 token_manager: Optional[VerkadaTokenManager] = None,
                 request_manager: Optional[VerkadaRequestManager] = None,
                 api_version: Optional[str] = None):
        super().__init__(api_key, token_manager, request_manager, api_version)

    @typechecked
    def get_all_sensors(self) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every environmental sensor in the organization, walking all pages automatically.

        :return: A generator that yields individual sensor dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_sensors(**kwargs),
        )

    @typechecked
    def get_sensors(self,
                     limit: Optional[int] = None,
                     cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of the organization's environmental sensors.

        Each item includes the device's ID, name, serial number, model, online
        status, timezone, and the ``readings`` it reports. Those readings are
        the valid ``fields`` values for :meth:`get_sensor_data`.

        :param limit: Maximum sensors per page (1 to 200, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``limit`` is outside 1-200.
        """
        check_limit(limit, 200)
        params = remove_null_fields({"limit": limit, "cursor": cursor})
        return self.request_manager.get(V2_SENSORS_ENDPOINT, params=params)

    @typechecked
    def get_all_sensor_alerts(self,
                              device_ids: List[str],
                              start_time: Optional[Timestamp] = None,
                              end_time: Optional[Timestamp] = None,
                              fields: Optional[List[str]] = None
                              ) -> Generator[Dict[str, Any], None, None]:
        """
        Returns all alerts for a set of sensors over a time range, walking all pages automatically.

        :param device_ids: Sensor IDs to retrieve alerts for.
        :param start_time: Start of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to one hour before ``end_time``.
        :param end_time: End of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to now.
        :param fields: Only return alerts for these reading types
            (see :data:`pykada.enums.SENSOR_FIELD_ENUM`). Defaults to all.
        :return: A generator that yields individual sensor alert dictionaries.
        :rtype: Generator
        :raises ValueError: If ``device_ids`` is empty or ``fields`` is invalid.
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
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_sensor_alerts(**kwargs),
            initial_params=params,
        )

    @typechecked
    def get_sensor_alerts(self,
                          device_ids: List[str],
                          start_time: Optional[Timestamp] = None,
                          end_time: Optional[Timestamp] = None,
                          fields: Optional[List[str]] = None,
                          limit: Optional[int] = None,
                          cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of alerts for a set of sensors over a time range.

        Each alert includes the triggering device, the reading type, the
        threshold, the most extreme value seen, and RFC 3339 start/end times.

        :param device_ids: Sensor IDs to retrieve alerts for.
        :param start_time: Start of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to one hour before ``end_time``.
        :param end_time: End of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to now.
        :param fields: Only return alerts for these reading types
            (see :data:`pykada.enums.SENSOR_FIELD_ENUM`). Defaults to all.
        :param limit: Maximum alerts per page (1 to 200, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``device_ids`` is empty, ``fields`` is invalid,
            ``limit`` is outside 1-200, or a timestamp is invalid.
        """
        if not device_ids:
            raise ValueError("device_ids must be a non-empty list")
        check_sensor_fields(fields)
        check_limit(limit, 200)

        params = remove_null_fields({
            "device_ids": ",".join(device_ids),
            "start_time": to_iso8601(start_time, "start_time"),
            "end_time": to_iso8601(end_time, "end_time"),
            "fields": ",".join(fields) if fields else None,
            "limit": limit,
            "cursor": cursor,
        })
        return self.request_manager.get(V2_SENSOR_ALERTS_ENDPOINT, params=params)

    @typechecked
    def get_all_sensor_data(self,
                            device_id: str,
                            start_time: Optional[Timestamp] = None,
                            end_time: Optional[Timestamp] = None,
                            fields: Optional[List[str]] = None,
                            interval: Optional[Duration] = None
                            ) -> Generator[Dict[str, Any], None, None]:
        """
        Returns all readings for a sensor over a time range, walking all pages automatically.

        :param device_id: The sensor's device ID.
        :param start_time: Start of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to one hour before ``end_time``.
        :param end_time: End of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to now.
        :param fields: Reading types to include
            (see :data:`pykada.enums.SENSOR_FIELD_ENUM`). Defaults to all.
        :param interval: Spacing between readings, as a ``timedelta`` or ISO
            8601 duration such as ``"PT5M"``. Data is stored at 1-second
            resolution for 30 days and 5-minute resolution up to 365 days.
            Defaults to a resolution chosen from the time range.
        :return: A generator that yields individual reading dictionaries, each
            with an RFC 3339 ``timestamp``.
        :rtype: Generator
        :raises ValueError: If ``fields`` or ``interval`` is invalid.
        """
        check_sensor_fields(fields)
        params = {
            "device_id": device_id,
            "start_time": start_time,
            "end_time": end_time,
            "fields": fields,
            "interval": interval,
        }
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_sensor_data(**kwargs),
            initial_params=params,
        )

    @typechecked
    def get_sensor_data(self,
                        device_id: str,
                        start_time: Optional[Timestamp] = None,
                        end_time: Optional[Timestamp] = None,
                        fields: Optional[List[str]] = None,
                        interval: Optional[Duration] = None,
                        limit: Optional[int] = None,
                        cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of readings for a sensor over a time range.

        :param device_id: The sensor's device ID.
        :param start_time: Start of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to one hour before ``end_time``.
        :param end_time: End of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to now.
        :param fields: Reading types to include
            (see :data:`pykada.enums.SENSOR_FIELD_ENUM`). Defaults to all.
        :param interval: Spacing between readings, as a ``timedelta`` or ISO
            8601 duration such as ``"PT5M"``. Data is stored at 1-second
            resolution for 30 days and 5-minute resolution up to 365 days.
            Defaults to a resolution chosen from the time range.
        :param limit: Maximum readings per page (1 to 200, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: The device's ID, name, serial and ``interval``, plus
            ``items`` (readings in ascending time order) and ``cursor``.
        :raises ValueError: If ``device_id`` is empty, or ``fields``,
            ``interval``, ``limit``, or a timestamp is invalid.
        """
        check_sensor_fields(fields)
        check_limit(limit, 200)

        url = f"{V2_SENSORS_ENDPOINT}/{path_segment(device_id, 'device_id')}/data"
        params = remove_null_fields({
            "start_time": to_iso8601(start_time, "start_time"),
            "end_time": to_iso8601(end_time, "end_time"),
            "fields": ",".join(fields) if fields else None,
            "interval": to_iso8601_duration(interval, "interval"),
            "limit": limit,
            "cursor": cursor,
        })
        return self.request_manager.get(url, params=params)


# ---------------------------------------------------------------------------
# Module-level default client — shared across all functional wrappers.
# ---------------------------------------------------------------------------
_default_sensors_client: Optional[SensorsClient] = None


def _get_default_client() -> SensorsClient:
    global _default_sensors_client
    if _default_sensors_client is None:
        _default_sensors_client = SensorsClient()
    return _default_sensors_client


_WRAPPER_NOTE = ("This is a functional wrapper for its equivalent method in the "
                 "SensorsClient. It reuses a module-level client configured from "
                 "VERKADA_API_KEY, making it best for one-off scripts. For "
                 "multiple API calls or a non-default key, instantiate a "
                 "SensorsClient directly.")


@copy_docstring_from(SensorsClient.get_all_sensors, note=_WRAPPER_NOTE)
@typechecked
def get_all_sensors():
    return _get_default_client().get_all_sensors()


@copy_docstring_from(SensorsClient.get_sensors, note=_WRAPPER_NOTE)
@typechecked
def get_sensors(limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().get_sensors(limit, cursor)


@copy_docstring_from(SensorsClient.get_all_sensor_alerts, note=_WRAPPER_NOTE)
@typechecked
def get_all_sensor_alerts(device_ids: List[str],
                          start_time: Optional[Timestamp] = None,
                          end_time: Optional[Timestamp] = None,
                          fields: Optional[List[str]] = None):
    return _get_default_client().get_all_sensor_alerts(device_ids, start_time,
                                                       end_time, fields)


@copy_docstring_from(SensorsClient.get_sensor_alerts, note=_WRAPPER_NOTE)
@typechecked
def get_sensor_alerts(device_ids: List[str],
                      start_time: Optional[Timestamp] = None,
                      end_time: Optional[Timestamp] = None,
                      fields: Optional[List[str]] = None,
                      limit: Optional[int] = None,
                      cursor: Optional[str] = None):
    return _get_default_client().get_sensor_alerts(device_ids, start_time, end_time,
                                                   fields, limit, cursor)


@copy_docstring_from(SensorsClient.get_all_sensor_data, note=_WRAPPER_NOTE)
@typechecked
def get_all_sensor_data(device_id: str,
                        start_time: Optional[Timestamp] = None,
                        end_time: Optional[Timestamp] = None,
                        fields: Optional[List[str]] = None,
                        interval: Optional[Duration] = None):
    return _get_default_client().get_all_sensor_data(device_id, start_time, end_time,
                                                     fields, interval)


@copy_docstring_from(SensorsClient.get_sensor_data, note=_WRAPPER_NOTE)
@typechecked
def get_sensor_data(device_id: str,
                    start_time: Optional[Timestamp] = None,
                    end_time: Optional[Timestamp] = None,
                    fields: Optional[List[str]] = None,
                    interval: Optional[Duration] = None,
                    limit: Optional[int] = None,
                    cursor: Optional[str] = None):
    return _get_default_client().get_sensor_data(device_id, start_time, end_time,
                                                 fields, interval, limit, cursor)
