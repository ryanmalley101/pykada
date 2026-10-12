"""
Cameras API client and functional wrappers for pykada.

The :class:`CamerasClient` provides access to camera metadata and sites,
footage links and thumbnails, license plate recognition (LPR), people lists
and persons of interest, cloud backup settings, occupancy and object-count
analytics, operational dashboards, PTZ presets, audio, and viewing stations
through Verkada's v2 Cameras and Analytics APIs.

Module-level functional wrappers (e.g. :func:`get_camera_data`) share a single
lazily-initialized :class:`CamerasClient` instance so token caching and
connection pooling are preserved across calls.
"""
import base64
import json
import re
from datetime import datetime, time, timedelta
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

from typeguard import typechecked

from pykada.endpoints import (
    LPOI_BATCH_ENDPOINT,
    V2_ANALYTICS_CAMERAS_ENDPOINT,
    V2_CAMERA_SITES_ENDPOINT,
    V2_CAMERAS_ENDPOINT,
    V2_FOOTAGE_LINK_ENDPOINT,
    V2_LPOI_ENDPOINT,
    V2_LPR_ZONES_ENDPOINT,
    V2_NCIC_PLATE_SEARCH_ENDPOINT,
    V2_OCCUPANCY_TRENDS_CAMERAS_ENDPOINT,
    V2_OPERATIONAL_DASHBOARD_ENDPOINT,
    V2_PEOPLE_LIST_ENDPOINT,
    V2_PEOPLE_LISTS_ENDPOINT,
    V2_POI_ENDPOINT,
    V2_SMART_LIST_ENDPOINT,
    V2_SMART_LISTS_ENDPOINT,
    V2_STREAMING_TOKEN_ENDPOINT,
    V2_THUMBNAIL_ENDPOINT,
    V2_THUMBNAIL_LINK_ENDPOINT,
    V2_VIEWING_STATIONS_ENDPOINT,
)
from pykada.enums import (
    DASHBOARD_INTERVAL_ENUM,
    DASHBOARD_WIDGET_TYPES_ENUM,
    LPR_ZONE_VEHICLE_STATUS_ENUM,
    VALID_CLOUD_BACKUP_VIDEO_QUALITY_ENUM,
    VALID_CLOUD_BACKUP_VIDEO_TO_UPLOAD_ENUM,
    VALID_IMAGE_RESOLUTION_ENUM,
    VALID_OCCUPANCY_TRENDS_INTERVALS_ENUM,
    VALID_OCCUPANCY_TRENDS_TYPES_ENUM,
    WEEKDAY_FULL_ENUM,
)
from pykada.helpers import (
    check_limit,
    copy_docstring_from,
    path_segment,
    remove_null_fields,
    require_choice,
    require_non_empty_str,
    to_iso8601,
    to_iso8601_duration,
    verify_csv_columns,
)
from pykada.verkada_client import BaseClient
from pykada.verkada_requests import VerkadaRequestManager

Timestamp = Union[datetime, str]
Duration = Union[timedelta, str]
TimeOfDay = Union[time, str]
#: A daily ``(start, end)`` window, each end a ``datetime.time`` or ``"HH:MM:SS"``.
Window = Tuple[TimeOfDay, TimeOfDay]

_TIME_OF_DAY_RE = re.compile(r"^(?:(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d|24:00:00)$")


def _time_of_day(value: TimeOfDay, field_name: str) -> str:
    if isinstance(value, time):
        return value.strftime("%H:%M:%S")
    if not _TIME_OF_DAY_RE.match(value):
        raise ValueError(
            f"{field_name} must be a time of day as 'HH:MM:SS' "
            f"('24:00:00' for midnight at the end of the day); got {value!r}."
        )
    return value


def _window(window: Optional[Window], field_name: str) -> Optional[Dict[str, str]]:
    """Convert a ``(start, end)`` pair to the v2 ``{start_time, end_time}`` object."""
    if window is None:
        return None
    start = _time_of_day(window[0], f"{field_name} start")
    end = _time_of_day(window[1], f"{field_name} end")
    # Fixed-width HH:MM:SS strings sort chronologically
    if end <= start:
        raise ValueError(f"{field_name} must end after it starts; got {start}-{end}.")
    return {"start_time": start, "end_time": end}


def _check_time_window(start_time, end_time) -> None:
    if (start_time is None) != (end_time is None):
        raise ValueError("start_time and end_time must be specified together.")


class CamerasClient(BaseClient):
    """
    Client for interacting with Verkada Cameras API.
    """

    # ------------------------------------------------------------------
    # Camera devices and sites
    # ------------------------------------------------------------------

    @typechecked
    def get_all_camera_data(self, site_ids: Optional[List[str]] = None
                            ) -> Generator[Dict[str, Any], None, None]:
        """
        Returns details for all cameras in the organization, walking all pages automatically.

        :param site_ids: Only return cameras at these sites (including their
            sub-sites). Use :meth:`get_camera_sites` to look up site IDs.
        :return: A generator that yields individual camera detail dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_camera_data(**kwargs),
            initial_params={"site_ids": site_ids},
        )

    @typechecked
    def get_camera_data(self,
                        site_ids: Optional[List[str]] = None,
                        limit: Optional[int] = None,
                        cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of camera details for the organization.

        Each camera includes its name, site, location, model, serial, MAC, local
        IP, retention, firmware status and update schedule, connection status,
        coordinates, and analytics flags. Timestamps are RFC 3339.

        :param site_ids: Only return cameras at these sites (including their
            sub-sites). Use :meth:`get_camera_sites` to look up site IDs.
        :param limit: Maximum cameras per page (1 to 200, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``limit`` is outside 1-200.
        """
        check_limit(limit, 200)
        params = remove_null_fields({
            "site_id": ",".join(site_ids) if site_ids else None,
            "limit": limit,
            "cursor": cursor,
        })
        return self.request_manager.get(V2_CAMERAS_ENDPOINT, params=params)

    @typechecked
    def get_all_camera_sites(self) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every camera site (camera group) in the organization, walking all pages automatically.

        :return: A generator that yields individual site dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_camera_sites(**kwargs),
        )

    @typechecked
    def get_camera_sites(self,
                         limit: Optional[int] = None,
                         cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of camera sites (camera groups) in the organization.

        Each site has a ``site_id``, ``name``, ``parent_site_id`` and full
        hierarchy ``path`` (e.g. ``"Austin / Floor 1"``).

        :param limit: Maximum sites per page (1 to 200, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``limit`` is outside 1-200.
        """
        check_limit(limit, 200)
        params = remove_null_fields({"limit": limit, "cursor": cursor})
        return self.request_manager.get(V2_CAMERA_SITES_ENDPOINT, params=params)

    # ------------------------------------------------------------------
    # Footage, thumbnails and streaming
    # ------------------------------------------------------------------

    @typechecked
    def get_footage_link(self, camera_id: str,
                         timestamp: Optional[Timestamp] = None) -> Dict[str, Any]:
        """
        Returns a Command link to video footage for a camera.

        :param camera_id: The unique identifier of the camera.
        :param timestamp: Where playback starts, as a timezone-aware
            ``datetime`` or ISO 8601 string. Omit for a live link.
        :return: ``{"url": str}``.
        :raises ValueError: If ``camera_id`` is empty or ``timestamp`` is invalid.
        """
        require_non_empty_str(camera_id, "camera_id")
        params = remove_null_fields({
            "camera_id": camera_id,
            "timestamp": to_iso8601(timestamp, "timestamp"),
        })
        return self.request_manager.get(V2_FOOTAGE_LINK_ENDPOINT, params=params)

    @typechecked
    def get_historical_thumbnail(self, camera_id: str,
                                 timestamp: Optional[Timestamp] = None,
                                 resolution: Optional[str] = None,
                                 start_time: Optional[Timestamp] = None,
                                 end_time: Optional[Timestamp] = None) -> bytes:
        """
        Returns a thumbnail image from a camera at or near a given time.

        By default the search covers one hour either side of ``timestamp``;
        pass ``start_time`` and ``end_time`` together to bound it (at most four
        hours, low-res only). The response's ``X-Verkada-Timestamp`` header
        holds the actual capture time but isn't exposed here.

        :param camera_id: The unique identifier of the camera.
        :param timestamp: Approximate capture time, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to now.
        :param resolution: ``"low-res"`` (default) or ``"hi-res"``
            (see :data:`pykada.enums.VALID_IMAGE_RESOLUTION_ENUM`).
        :param start_time: Inclusive start of the search window.
        :param end_time: Inclusive end of the search window.
        :return: Raw JPEG image bytes.
        :raises ValueError: If ``camera_id`` is empty, ``resolution`` is invalid,
            only one of ``start_time``/``end_time`` is given, or a window is
            combined with ``"hi-res"``.
        """
        require_non_empty_str(camera_id, "camera_id")
        require_choice(resolution, VALID_IMAGE_RESOLUTION_ENUM, "resolution")
        _check_time_window(start_time, end_time)
        if start_time is not None and resolution == VALID_IMAGE_RESOLUTION_ENUM["HI_RES"]:
            raise ValueError("start_time/end_time are not supported with hi-res thumbnails.")
        params = remove_null_fields({
            "camera_id": camera_id,
            "timestamp": to_iso8601(timestamp, "timestamp"),
            "resolution": resolution,
            "start_time": to_iso8601(start_time, "start_time"),
            "end_time": to_iso8601(end_time, "end_time"),
        })
        return self.request_manager.get_image(V2_THUMBNAIL_ENDPOINT, params=params)

    @typechecked
    def get_latest_thumbnail(self, camera_id: str,
                             resolution: Optional[str] = None) -> bytes:
        """
        Returns the most recent thumbnail image from a camera.

        :param camera_id: The unique identifier of the camera.
        :param resolution: ``"low-res"`` (default) or ``"hi-res"``
            (see :data:`pykada.enums.VALID_IMAGE_RESOLUTION_ENUM`).
        :return: Raw JPEG image bytes.
        :raises ValueError: If ``camera_id`` is empty or ``resolution`` is invalid.
        """
        require_choice(resolution, VALID_IMAGE_RESOLUTION_ENUM, "resolution")
        url = (f"{V2_CAMERAS_ENDPOINT}/{path_segment(camera_id, 'camera_id')}"
               f"/footage/thumbnails/latest")
        params = remove_null_fields({"resolution": resolution})
        return self.request_manager.get_image(url, params=params)

    @typechecked
    def get_thumbnail_link(self, camera_id: str,
                           timestamp: Optional[Timestamp] = None,
                           expiry: Optional[Duration] = None,
                           start_time: Optional[Timestamp] = None,
                           end_time: Optional[Timestamp] = None) -> Dict[str, Any]:
        """
        Returns a pre-signed link to a thumbnail image from a camera.

        :param camera_id: The unique identifier of the camera.
        :param timestamp: Capture time, as a timezone-aware ``datetime`` or
            ISO 8601 string. Defaults to now.
        :param expiry: How long the link stays valid, as a ``timedelta`` or ISO
            8601 duration (``"PT1H"`` to ``"P7D"``). Defaults to one day.
        :param start_time: Inclusive start of a window (at most four hours) to
            search for the nearest snapshot. Requires ``end_time``.
        :param end_time: Inclusive end of the search window. Requires ``start_time``.
        :return: ``{"url": str, "timestamp": str, "expiry": str}`` with RFC
            3339 capture and expiry times.
        :raises ValueError: If ``camera_id`` is empty, a time is invalid, or
            only one of ``start_time``/``end_time`` is given.
        """
        require_non_empty_str(camera_id, "camera_id")
        _check_time_window(start_time, end_time)
        params = remove_null_fields({
            "camera_id": camera_id,
            "timestamp": to_iso8601(timestamp, "timestamp"),
            "expiry": to_iso8601_duration(expiry, "expiry"),
            "start_time": to_iso8601(start_time, "start_time"),
            "end_time": to_iso8601(end_time, "end_time"),
        })
        return self.request_manager.get(V2_THUMBNAIL_LINK_ENDPOINT, params=params)

    @typechecked
    def get_streaming_token(self,
                            exclude_accessible_resources: Optional[bool] = None
                            ) -> Dict[str, Any]:
        """
        Retrieve a short-lived JWT for streaming live or historical footage.

        This endpoint authenticates with the API key itself rather than the
        session token. To build playlist URLs, use :class:`StreamingClient`,
        which fetches and caches this JWT for you.

        :param exclude_accessible_resources: If True, omits ``accessible_cameras``
            and ``accessible_sites`` from the response to reduce payload size.
        :return: ``jwt``, ``expires_in`` (ISO 8601 duration), ``expires_at``
            (RFC 3339), ``permission``, and optionally the accessible resources.
        """
        params = remove_null_fields(
            {"exclude_accessible_resources": exclude_accessible_resources})
        headers = {"x-api-key": self.request_manager.token_manager.api_key}
        return self.request_manager.get(V2_STREAMING_TOKEN_ENDPOINT,
                                        headers=headers, params=params)

    # ------------------------------------------------------------------
    # License Plates of Interest
    # ------------------------------------------------------------------

    @typechecked
    def create_lpoi(self, license_plate: str, description: str) -> Dict[str, Any]:
        """
        Create a License Plate of Interest.

        :param license_plate: The plate number (1 to 11 characters).
        :param description: A description of the plate.
        :return: The created LPOI, with an RFC 3339 ``created_at``.
        :raises ValueError: If ``license_plate`` is empty or over 11 characters.
        """
        require_non_empty_str(license_plate, "license_plate")
        if len(license_plate) > 11:
            raise ValueError("license_plate must be at most 11 characters.")
        payload = {"license_plate": license_plate, "description": description}
        return self.request_manager.post(V2_LPOI_ENDPOINT, payload=payload)

    @typechecked
    def get_all_lpois(self) -> Generator[Dict[str, Any], None, None]:
        """
        Returns all License Plates of Interest for the organization, walking all pages automatically.

        :return: A generator that yields individual LPOI dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_lpois(**kwargs),
            default_limit=1000,
        )

    @typechecked
    def get_lpois(self,
                  limit: Optional[int] = None,
                  cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of License Plates of Interest.

        :param limit: Maximum plates per page (1 to 10000, server default 1000).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``limit`` is outside 1-10000.
        """
        check_limit(limit, 10000)
        params = remove_null_fields({"limit": limit, "cursor": cursor})
        return self.request_manager.get(V2_LPOI_ENDPOINT, params=params)

    @typechecked
    def update_lpoi(self, license_plate: str, description: str) -> Dict[str, Any]:
        """
        Update the description of a License Plate of Interest.

        :param license_plate: The plate number to update.
        :param description: The new description.
        :return: The updated LPOI.
        :raises ValueError: If ``license_plate`` is empty.
        """
        url = f"{V2_LPOI_ENDPOINT}/{path_segment(license_plate, 'license_plate')}"
        return self.request_manager.patch(url, payload={"description": description})

    @typechecked
    def delete_lpoi(self, license_plate: str) -> Dict[str, Any]:
        """
        Delete a License Plate of Interest.

        :param license_plate: The plate number to remove.
        :return: An empty dict (the API returns 204 No Content).
        :raises ValueError: If ``license_plate`` is empty.
        """
        url = f"{V2_LPOI_ENDPOINT}/{path_segment(license_plate, 'license_plate')}"
        return self.request_manager.delete(url)

    @typechecked
    def create_bulk_lpois(self, filename: str) -> Dict[str, Any]:
        """
        Create License Plates of Interest in bulk from a CSV file.

        The CSV must have exactly the columns ``License Plate`` and ``Name``.
        This uses the v1 batch endpoint; v2 has no bulk equivalent yet.

        :param filename: Path to the CSV file.
        :return: ``{"addedMs": int}``, the upload time.
        :raises FileNotFoundError: If the file doesn't exist.
        :raises ValueError: If the CSV columns are wrong.
        """
        verify_csv_columns(filename, ['License Plate', 'Name'])
        with open(filename, 'rb') as f:
            files = {"file": (filename, f, "text/csv")}
            return self.request_manager.post(LPOI_BATCH_ENDPOINT, files=files)

    @typechecked
    def delete_bulk_lpois(self, filename: str) -> Dict[str, Any]:
        """
        Delete License Plates of Interest in bulk from a CSV file.

        The CSV must have exactly one column, ``License Plate``.
        This uses the v1 batch endpoint; v2 has no bulk equivalent yet.

        :param filename: Path to the CSV file.
        :return: ``{"addedMs": int}``, the upload time.
        :raises FileNotFoundError: If the file doesn't exist.
        :raises ValueError: If the CSV columns are wrong.
        """
        verify_csv_columns(filename, ['License Plate'])
        with open(filename, 'rb') as f:
            files = {"file": (filename, f, "text/csv")}
            return self.request_manager.delete(LPOI_BATCH_ENDPOINT, files=files)

    # ------------------------------------------------------------------
    # License Plate Recognition
    # ------------------------------------------------------------------

    @typechecked
    def get_all_seen_license_plates(self, camera_id: str,
                                    license_plate: Optional[str] = None,
                                    start_time: Optional[Timestamp] = None,
                                    end_time: Optional[Timestamp] = None
                                    ) -> Generator[Dict[str, Any], None, None]:
        """
        Returns all license plate detections for an LPR camera, walking all pages automatically.

        :param camera_id: The unique identifier of the LPR-enabled camera.
        :param license_plate: Only return detections of this plate.
        :param start_time: Start of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to 24 hours ago.
        :param end_time: End of the time range. Defaults to now.
        :return: A generator that yields individual detection dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_seen_license_plates(**kwargs),
            initial_params={
                "camera_id": camera_id,
                "license_plate": license_plate,
                "start_time": start_time,
                "end_time": end_time,
            },
        )

    @typechecked
    def get_seen_license_plates(self, camera_id: str,
                                license_plate: Optional[str] = None,
                                start_time: Optional[Timestamp] = None,
                                end_time: Optional[Timestamp] = None,
                                limit: Optional[int] = None,
                                cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of license plate detections, with images, for an LPR camera.

        Each item has ``license_plate``, an RFC 3339 ``detected_at``,
        ``image_url`` and, if available, ``vehicle_image_url``.

        :param camera_id: The unique identifier of the LPR-enabled camera.
        :param license_plate: Only return detections of this plate.
        :param start_time: Start of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to 24 hours ago.
        :param end_time: End of the time range. Defaults to now.
        :param limit: Maximum detections per page (1 to 200, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``camera_id`` is empty, ``limit`` is outside
            1-200, or a timestamp is invalid.
        """
        check_limit(limit, 200)
        url = f"{V2_CAMERAS_ENDPOINT}/{path_segment(camera_id, 'camera_id')}/lpr/images"
        params = remove_null_fields({
            "license_plate": license_plate,
            "start_time": to_iso8601(start_time, "start_time"),
            "end_time": to_iso8601(end_time, "end_time"),
            "limit": limit,
            "cursor": cursor,
        })
        return self.request_manager.get(url, params=params)

    @typechecked
    def get_all_lpr_timestamps(self, camera_id: str,
                               license_plate: str,
                               start_time: Optional[Timestamp] = None,
                               end_time: Optional[Timestamp] = None
                               ) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every time a plate was seen by an LPR camera, walking all pages automatically.

        :param camera_id: The unique identifier of the LPR-enabled camera.
        :param license_plate: The plate number to look up.
        :param start_time: Start of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to 24 hours ago.
        :param end_time: End of the time range. Defaults to now.
        :return: A generator that yields ``{"detected_at": str}`` dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_lpr_timestamps(**kwargs),
            initial_params={
                "camera_id": camera_id,
                "license_plate": license_plate,
                "start_time": start_time,
                "end_time": end_time,
            },
        )

    @typechecked
    def get_lpr_timestamps(self, camera_id: str,
                           license_plate: str,
                           start_time: Optional[Timestamp] = None,
                           end_time: Optional[Timestamp] = None,
                           limit: Optional[int] = None,
                           cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of times a plate was seen by an LPR camera.

        :param camera_id: The unique identifier of the LPR-enabled camera.
        :param license_plate: The plate number to look up.
        :param start_time: Start of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to 24 hours ago.
        :param end_time: End of the time range. Defaults to now.
        :param limit: Maximum detections per page (1 to 200, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [{"detected_at": str}, ...], "cursor": str | None}``.
        :raises ValueError: If ``camera_id`` or ``license_plate`` is empty,
            ``limit`` is outside 1-200, or a timestamp is invalid.
        """
        check_limit(limit, 200)
        url = (f"{V2_CAMERAS_ENDPOINT}/{path_segment(camera_id, 'camera_id')}"
               f"/lpr/{path_segment(license_plate, 'license_plate')}/timestamps")
        params = remove_null_fields({
            "start_time": to_iso8601(start_time, "start_time"),
            "end_time": to_iso8601(end_time, "end_time"),
            "limit": limit,
            "cursor": cursor,
        })
        return self.request_manager.get(url, params=params)

    @typechecked
    def get_all_lpr_zones(self) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every LPR zone in the organization, walking all pages automatically.

        :return: A generator that yields individual zone dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_lpr_zones(**kwargs),
            default_limit=200,
        )

    @typechecked
    def get_lpr_zones(self,
                      limit: Optional[int] = None,
                      cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of License Plate Recognition zones.

        Each zone has a ``zone_id``, ``zone_name``, ``preview_camera_id`` and
        RFC 3339 ``created_at``/``updated_at``.

        :param limit: Maximum zones per page (1 to 200, server default 200).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``limit`` is outside 1-200.
        """
        check_limit(limit, 200)
        params = remove_null_fields({"limit": limit, "cursor": cursor})
        return self.request_manager.get(V2_LPR_ZONES_ENDPOINT, params=params)

    @typechecked
    def get_lpr_zone_metrics(self, zone_id: str,
                             start_time: Timestamp,
                             end_time: Timestamp) -> Dict[str, Any]:
        """
        Returns aggregated metrics for an LPR zone over a time range.

        Includes end-of-range ``occupancy``, ``entries``, ``exits``,
        ``unique_visitors``, and median/max/average time in zone as ISO 8601
        durations.

        :param zone_id: The unique identifier of the zone.
        :param start_time: Inclusive start of the range, as a timezone-aware
            ``datetime`` or ISO 8601 string.
        :param end_time: Exclusive end of the range.
        :return: The zone metrics.
        :raises ValueError: If ``zone_id`` is empty or a timestamp is invalid.
        """
        url = f"{V2_LPR_ZONES_ENDPOINT}/{path_segment(zone_id, 'zone_id')}/metrics"
        params = {
            "start_time": to_iso8601(start_time, "start_time"),
            "end_time": to_iso8601(end_time, "end_time"),
        }
        return self.request_manager.get(url, params=params)

    @typechecked
    def get_all_lpr_zone_records(self, zone_id: str,
                                 start_time: Optional[Timestamp] = None,
                                 end_time: Optional[Timestamp] = None,
                                 vehicle_status: Optional[str] = None
                                 ) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every visit record for an LPR zone, walking all pages automatically.

        :param zone_id: The unique identifier of the zone.
        :param start_time: Start of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to 24 hours ago.
        :param end_time: End of the time range. Defaults to now.
        :param vehicle_status: ``"still_in"`` or ``"departed"``
            (see :data:`pykada.enums.LPR_ZONE_VEHICLE_STATUS_ENUM`). Defaults to both.
        :return: A generator that yields individual visit record dictionaries.
        :rtype: Generator
        :raises ValueError: If ``vehicle_status`` is invalid.
        """
        require_choice(vehicle_status, LPR_ZONE_VEHICLE_STATUS_ENUM, "vehicle_status")
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_lpr_zone_records(**kwargs),
            initial_params={
                "zone_id": zone_id,
                "start_time": start_time,
                "end_time": end_time,
                "vehicle_status": vehicle_status,
            },
        )

    @typechecked
    def get_lpr_zone_records(self, zone_id: str,
                             start_time: Optional[Timestamp] = None,
                             end_time: Optional[Timestamp] = None,
                             vehicle_status: Optional[str] = None,
                             limit: Optional[int] = None,
                             cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of visit records for an LPR zone.

        Each record has the plate, entry/exit times and cameras, an ISO 8601
        ``dwell_time``, ``vehicle_status``, and plate/vehicle thumbnail URLs.

        :param zone_id: The unique identifier of the zone.
        :param start_time: Start of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to 24 hours ago.
        :param end_time: End of the time range. Defaults to now.
        :param vehicle_status: ``"still_in"`` or ``"departed"``
            (see :data:`pykada.enums.LPR_ZONE_VEHICLE_STATUS_ENUM`). Defaults to both.
        :param limit: Maximum records per page (1 to 100, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``zone_id`` is empty, ``vehicle_status`` or a
            timestamp is invalid, or ``limit`` is outside 1-100.
        """
        require_choice(vehicle_status, LPR_ZONE_VEHICLE_STATUS_ENUM, "vehicle_status")
        check_limit(limit, 100)
        url = f"{V2_LPR_ZONES_ENDPOINT}/{path_segment(zone_id, 'zone_id')}/records"
        params = remove_null_fields({
            "start_time": to_iso8601(start_time, "start_time"),
            "end_time": to_iso8601(end_time, "end_time"),
            "vehicle_status": vehicle_status,
            "limit": limit,
            "cursor": cursor,
        })
        return self.request_manager.get(url, params=params)

    @typechecked
    def search_all_ncic_license_plates(self,
                                       start_time: Timestamp,
                                       end_time: Timestamp,
                                       license_plate: Optional[str] = None,
                                       geo_fence: Optional[List[Tuple[float, float]]] = None
                                       ) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every matching license plate read, walking all pages automatically.

        See :meth:`search_ncic_license_plates` for parameters. Only available to
        organizations with CJIS access enabled.

        :return: A generator that yields individual plate read dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.search_ncic_license_plates(**kwargs),
            initial_params={
                "start_time": start_time,
                "end_time": end_time,
                "license_plate": license_plate,
                "geo_fence": geo_fence,
            },
        )

    @typechecked
    def search_ncic_license_plates(self,
                                   start_time: Timestamp,
                                   end_time: Timestamp,
                                   license_plate: Optional[str] = None,
                                   geo_fence: Optional[List[Tuple[float, float]]] = None,
                                   limit: Optional[int] = None,
                                   cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Search license plate reads across the organization (NCIC), newest first.

        Only available to organizations with CJIS (Criminal Justice
        Information Services) access enabled; others get a 403. The time range
        may span at most three years.

        :param start_time: Start of the search, as a timezone-aware
            ``datetime`` or ISO 8601 string.
        :param end_time: End of the search.
        :param license_plate: Plate pattern; ``*`` is a wildcard, e.g.
            ``"ABC*"`` (starts with), ``"*123"`` (ends with), ``"*BC1*"`` (contains).
        :param geo_fence: Polygon of 3 to 700 ``(latitude, longitude)`` points;
            only reads from cameras inside it are returned.
        :param limit: Maximum reads per page (1 to 1000, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``geo_fence`` has fewer than 3 or more than 700
            points, ``limit`` is outside 1-1000, or a timestamp is invalid.
        """
        check_limit(limit, 1000)
        if geo_fence is not None and not 3 <= len(geo_fence) <= 700:
            raise ValueError("geo_fence must have between 3 and 700 points.")
        payload = remove_null_fields({
            "start_time": to_iso8601(start_time, "start_time"),
            "end_time": to_iso8601(end_time, "end_time"),
            "license_plate": license_plate,
            "geo_fence": [{"latitude": lat, "longitude": lon} for lat, lon in geo_fence]
            if geo_fence is not None else None,
            "limit": limit,
            "cursor": cursor,
        })
        return self.request_manager.post(V2_NCIC_PLATE_SEARCH_ENDPOINT, payload=payload)

    # ------------------------------------------------------------------
    # Persons of Interest, People Lists and Smart Lists
    # ------------------------------------------------------------------

    @typechecked
    def get_all_pois(self) -> Generator[Dict[str, Any], None, None]:
        """
        Returns all Persons of Interest in the organization, walking all pages automatically.

        :return: A generator that yields individual POI dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_pois(**kwargs),
        )

    @typechecked
    def get_pois(self,
                 limit: Optional[int] = None,
                 cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of Persons of Interest.

        Each item has ``person_id``, ``label``, and RFC 3339 ``created_at`` and
        ``last_seen_at``.

        :param limit: Maximum people per page (1 to 200, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``limit`` is outside 1-200.
        """
        check_limit(limit, 200)
        params = remove_null_fields({"limit": limit, "cursor": cursor})
        return self.request_manager.get(V2_POI_ENDPOINT, params=params)

    @typechecked
    def create_poi(self, image_path: str, label: str) -> Dict[str, Any]:
        """
        Create a Person of Interest from a face image file.

        :param image_path: Local path to a JPEG or PNG image of the person's face.
        :param label: A name or label for the person.
        :return: The created POI.
        :raises ValueError: If ``label`` is empty.
        :raises FileNotFoundError: If ``image_path`` doesn't exist.
        """
        require_non_empty_str(label, "label")
        with open(image_path, 'rb') as f:
            encoded_image = base64.b64encode(f.read()).decode('utf-8')
        payload = {"base64_image": encoded_image, "label": label}
        return self.request_manager.post(V2_POI_ENDPOINT, payload=payload)

    @typechecked
    def update_poi(self, person_id: str, label: str) -> Dict[str, Any]:
        """
        Update the label of a Person of Interest.

        :param person_id: The unique identifier of the Person of Interest.
        :param label: The new label.
        :return: The updated POI.
        :raises ValueError: If ``person_id`` or ``label`` is empty.
        """
        require_non_empty_str(label, "label")
        url = f"{V2_POI_ENDPOINT}/{path_segment(person_id, 'person_id')}"
        return self.request_manager.patch(url, payload={"label": label})

    @typechecked
    def delete_poi(self, person_id: str) -> Dict[str, Any]:
        """
        Delete a Person of Interest.

        :param person_id: The unique identifier of the Person of Interest.
        :return: An empty dict (the API returns 204 No Content).
        :raises ValueError: If ``person_id`` is empty.
        """
        url = f"{V2_POI_ENDPOINT}/{path_segment(person_id, 'person_id')}"
        return self.request_manager.delete(url)

    @typechecked
    def get_all_people_lists(self) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every People List in the organization, walking all pages automatically.

        :return: A generator that yields individual People List dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_people_lists(**kwargs),
        )

    @typechecked
    def get_people_lists(self,
                         limit: Optional[int] = None,
                         cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of People Lists.

        Each item has ``list_id``, ``name``, ``is_public`` and, for system
        lists, ``system_list_category``.

        :param limit: Maximum lists per page (1 to 1000, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``limit`` is outside 1-1000.
        """
        check_limit(limit, 1000)
        params = remove_null_fields({"limit": limit, "cursor": cursor})
        return self.request_manager.get(V2_PEOPLE_LISTS_ENDPOINT, params=params)

    @typechecked
    def delete_people_list(self, list_id: str) -> Dict[str, Any]:
        """
        Delete a People List.

        Identities that belong only to this list are deleted too; identities
        shared with other lists are just removed from this one. System lists
        can't be deleted.

        :param list_id: The unique identifier of the People List.
        :return: The API response (empty on success).
        :raises ValueError: If ``list_id`` is empty.
        """
        url = f"{V2_PEOPLE_LIST_ENDPOINT}/{path_segment(list_id, 'list_id')}"
        return self.request_manager.delete(url)

    @typechecked
    def get_all_smart_lists(self) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every Smart List in the organization, walking all pages automatically.

        :return: A generator that yields individual Smart List dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_smart_lists(**kwargs),
        )

    @typechecked
    def get_smart_lists(self,
                        limit: Optional[int] = None,
                        cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of Smart Lists.

        Each item has ``list_id``, ``name``, ``is_public``, ``camera_ids``,
        ``allowed_people_list_ids`` and ``onboarding_complete``.

        :param limit: Maximum lists per page (1 to 1000, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``limit`` is outside 1-1000.
        """
        check_limit(limit, 1000)
        params = remove_null_fields({"limit": limit, "cursor": cursor})
        return self.request_manager.get(V2_SMART_LISTS_ENDPOINT, params=params)

    @typechecked
    def delete_smart_list(self, list_id: str) -> Dict[str, Any]:
        """
        Delete a Smart List and the whitelisted identities that belong only to it.

        :param list_id: The unique identifier of the Smart List.
        :return: The API response (empty on success).
        :raises ValueError: If ``list_id`` is empty.
        """
        url = f"{V2_SMART_LIST_ENDPOINT}/{path_segment(list_id, 'list_id')}"
        return self.request_manager.delete(url)

    # ------------------------------------------------------------------
    # Analytics: object counts, occupancy trends, MQTT
    # ------------------------------------------------------------------

    @typechecked
    def get_all_object_counts(self, camera_id: str,
                              start_time: Optional[Timestamp] = None,
                              end_time: Optional[Timestamp] = None
                              ) -> Generator[Dict[str, Any], None, None]:
        """
        Returns all people/vehicle count samples for a camera, walking all pages automatically.

        :param camera_id: The unique identifier of the camera.
        :param start_time: Start of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to one hour ago.
        :param end_time: End of the time range. Defaults to now.
        :return: A generator that yields individual count sample dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_object_counts(**kwargs),
            initial_params={
                "camera_id": camera_id,
                "start_time": start_time,
                "end_time": end_time,
            },
        )

    @typechecked
    def get_object_counts(self, camera_id: str,
                          start_time: Optional[Timestamp] = None,
                          end_time: Optional[Timestamp] = None,
                          limit: Optional[int] = None,
                          cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of people/vehicle count samples for a camera.

        Each item has an RFC 3339 ``detected_at``, ``people_count`` and
        ``vehicle_count``.

        :param camera_id: The unique identifier of the camera.
        :param start_time: Start of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to one hour ago.
        :param end_time: End of the time range. Defaults to now.
        :param limit: Maximum samples per page (1 to 200, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``camera_id`` is empty, ``limit`` is outside
            1-200, or a timestamp is invalid.
        """
        check_limit(limit, 200)
        url = (f"{V2_CAMERAS_ENDPOINT}/{path_segment(camera_id, 'camera_id')}"
               f"/analytics/object_counts")
        params = remove_null_fields({
            "start_time": to_iso8601(start_time, "start_time"),
            "end_time": to_iso8601(end_time, "end_time"),
            "limit": limit,
            "cursor": cursor,
        })
        return self.request_manager.get(url, params=params)

    @typechecked
    def get_max_people_vehicle_counts(self, camera_id: str,
                                      start_time: Optional[Timestamp] = None,
                                      end_time: Optional[Timestamp] = None,
                                      search_zones: Optional[List[List[int]]] = None
                                      ) -> Dict[str, Any]:
        """
        Returns the peak people and vehicle counts for a camera over a time range.

        :param camera_id: The unique identifier of the camera.
        :param start_time: Start of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to now; if only
            ``start_time`` is given it is also used as the end.
        :param end_time: End of the time range. Requires ``start_time``.
        :param search_zones: Grid cells to count in, as ``[x, y]`` pairs from
            ``[0, 0]`` to ``[9, 9]``, e.g. ``[[3, 3], [3, 4], [4, 3], [4, 4]]``.
            Defaults to the whole frame.
        :return: ``{"people_count": int, "vehicle_count": int}``.
        :raises ValueError: If ``camera_id`` is empty, ``end_time`` is given
            without ``start_time``, or a timestamp is invalid.
        """
        if end_time is not None and start_time is None:
            raise ValueError("end_time can only be used together with start_time.")
        url = (f"{V2_CAMERAS_ENDPOINT}/{path_segment(camera_id, 'camera_id')}"
               f"/analytics/max_object_counts")
        params = remove_null_fields({
            "start_time": to_iso8601(start_time, "start_time"),
            "end_time": to_iso8601(end_time, "end_time"),
            "search_zones": json.dumps(search_zones, separators=(",", ":"))
            if search_zones is not None else None,
        })
        return self.request_manager.get(url, params=params)

    @typechecked
    def get_occupancy_trends(self, camera_id: str,
                             start_time: Optional[Timestamp] = None,
                             end_time: Optional[Timestamp] = None,
                             interval: Optional[str] = None,
                             trend_type: Optional[str] = None,
                             preset_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns occupancy trends (in/out counts) for a camera over a time range.

        :param camera_id: The unique identifier of the camera.
        :param start_time: Start of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to one hour ago.
        :param end_time: End of the time range. Defaults to now.
        :param interval: Bucket width: ``"15_minutes"``, ``"1_hour"`` (default)
            or ``"1_day"`` (see :data:`pykada.enums.VALID_OCCUPANCY_TRENDS_INTERVALS_ENUM`).
        :param trend_type: Object class counted: ``"person"`` (default) or
            ``"vehicle"`` (see :data:`pykada.enums.VALID_OCCUPANCY_TRENDS_TYPES_ENUM`).
        :param preset_id: The camera line preset to query. See
            :meth:`get_occupancy_trend_enabled_cameras`.
        :return: The queried range and ``trends`` with ``trend_in`` and
            ``trend_out`` lists of ``{start_time, end_time, count}`` buckets.
        :raises ValueError: If ``camera_id`` is empty, or ``interval``,
            ``trend_type`` or a timestamp is invalid.
        """
        require_choice(interval, VALID_OCCUPANCY_TRENDS_INTERVALS_ENUM, "interval")
        require_choice(trend_type, VALID_OCCUPANCY_TRENDS_TYPES_ENUM, "trend_type")
        url = (f"{V2_CAMERAS_ENDPOINT}/{path_segment(camera_id, 'camera_id')}"
               f"/occupancy_trends")
        params = remove_null_fields({
            "start_time": to_iso8601(start_time, "start_time"),
            "end_time": to_iso8601(end_time, "end_time"),
            "interval": interval,
            "type": trend_type,
            "preset_id": preset_id,
        })
        return self.request_manager.get(url, params=params)

    @typechecked
    def get_all_occupancy_trend_enabled_cameras(self) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every camera with occupancy trend line presets, walking all pages automatically.

        :return: A generator that yields ``{"camera_id", "presets"}`` dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_occupancy_trend_enabled_cameras(**kwargs),
        )

    @typechecked
    def get_occupancy_trend_enabled_cameras(self,
                                            limit: Optional[int] = None,
                                            cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of cameras with occupancy trend line presets.

        Each item has a ``camera_id`` and ``presets``, each with a
        ``preset_id`` and the ``object_class`` it counts.

        :param limit: Maximum cameras per page (1 to 200, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``limit`` is outside 1-200.
        """
        check_limit(limit, 200)
        params = remove_null_fields({"limit": limit, "cursor": cursor})
        return self.request_manager.get(V2_OCCUPANCY_TRENDS_CAMERAS_ENDPOINT, params=params)

    @typechecked
    def get_object_position_mqtt(self, camera_id: str) -> Dict[str, Any]:
        """
        Returns a camera's Object Position MQTT broker configuration.

        :param camera_id: The unique identifier of the camera.
        :return: ``camera_id``, ``broker_host_port``, ``broker_cert`` and
            ``client_username`` (``None`` where unset). The password is never returned.
        :raises ValueError: If ``camera_id`` is empty.
        """
        url = (f"{V2_ANALYTICS_CAMERAS_ENDPOINT}/{path_segment(camera_id, 'camera_id')}"
               f"/mqtt_configs")
        return self.request_manager.get(url)

    @typechecked
    def set_object_position_mqtt(self, camera_id: str,
                                 broker_host_port: str,
                                 broker_cert: str,
                                 client_username: Optional[str] = None,
                                 client_password: Optional[str] = None) -> Dict[str, Any]:
        """
        Replace a camera's Object Position MQTT broker configuration.

        Object Position Events from the camera are published to this broker.

        :param camera_id: The unique identifier of the camera.
        :param broker_host_port: Broker ``host:port``; the host may be an IP or
            hostname. Only ports 443 (recommended), 123 and 53 are supported.
        :param broker_cert: CA-signed certificate for the TLS connection.
        :param client_username: Optional MQTT client username.
        :param client_password: Optional MQTT client password (never echoed back).
        :return: The new configuration, without the password.
        :raises ValueError: If ``camera_id`` is empty.
        """
        url = (f"{V2_ANALYTICS_CAMERAS_ENDPOINT}/{path_segment(camera_id, 'camera_id')}"
               f"/mqtt_configs")
        payload = remove_null_fields({
            "broker_host_port": broker_host_port,
            "broker_cert": broker_cert,
            "client_username": client_username,
            "client_password": client_password,
        })
        return self.request_manager.put(url, payload=payload)

    # ------------------------------------------------------------------
    # Operational dashboards
    # ------------------------------------------------------------------

    @typechecked
    def get_all_dashboards(self) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every operational dashboard in the organization, walking all pages automatically.

        :return: A generator that yields individual dashboard dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_dashboards(**kwargs),
        )

    @typechecked
    def get_dashboards(self,
                       limit: Optional[int] = None,
                       cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of operational dashboards, regardless of who they're shared with.

        Each dashboard has a ``dashboard_id``, ``dashboard_name``, ``timezone``,
        ``site_ids`` and ``widgets`` (``widget_id``, ``widget_name``,
        ``widget_type``) to use with :meth:`get_dashboard_widget_trends`.

        :param limit: Maximum dashboards per page (1 to 200, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``limit`` is outside 1-200.
        """
        check_limit(limit, 200)
        params = remove_null_fields({"limit": limit, "cursor": cursor})
        return self.request_manager.get(V2_OPERATIONAL_DASHBOARD_ENDPOINT, params=params)

    @typechecked
    def get_dashboard_occupancy_trend_data(self, dashboard_id: str,
                                           start_time: Optional[Timestamp] = None,
                                           end_time: Optional[Timestamp] = None,
                                           interval: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns occupancy trends for an operational dashboard over a time range.

        :param dashboard_id: The unique identifier of the dashboard.
        :param start_time: Start of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to one hour ago.
        :param end_time: End of the time range. Defaults to now.
        :param interval: Bucket width: ``"PT15M"``, ``"PT1H"`` (default) or
            ``"PT1D"`` (see :data:`pykada.enums.DASHBOARD_INTERVAL_ENUM`).
        :return: The dashboard and range, plus ``in_counts``, ``out_counts``
            and ``net_occupancy`` lists of ``{start_time, end_time, value}`` buckets.
        :raises ValueError: If ``dashboard_id`` is empty, or ``interval`` or a
            timestamp is invalid.
        """
        require_choice(interval, DASHBOARD_INTERVAL_ENUM, "interval")
        url = (f"{V2_OPERATIONAL_DASHBOARD_ENDPOINT}/"
               f"{path_segment(dashboard_id, 'dashboard_id')}/occupancy_trends")
        params = remove_null_fields({
            "start_time": to_iso8601(start_time, "start_time"),
            "end_time": to_iso8601(end_time, "end_time"),
            "interval": interval,
        })
        return self.request_manager.get(url, params=params)

    @typechecked
    def get_dashboard_widget_trends(self, dashboard_id: str,
                                    start_time: Optional[Timestamp] = None,
                                    end_time: Optional[Timestamp] = None,
                                    interval: Optional[str] = None,
                                    site_ids: Optional[List[str]] = None,
                                    widget_ids: Optional[List[str]] = None,
                                    widget_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Returns trend data for the widgets on an operational dashboard.

        :param dashboard_id: The unique identifier of the dashboard.
        :param start_time: Start of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to the start of the last
            full bucket.
        :param end_time: End of the time range. Defaults to the end of the last
            full bucket.
        :param interval: Bucket width: ``"PT15M"``, ``"PT1H"`` (default) or
            ``"PT1D"`` (see :data:`pykada.enums.DASHBOARD_INTERVAL_ENUM`).
        :param site_ids: Only include these sites. Defaults to all on the dashboard.
        :param widget_ids: Only include these widgets. Defaults to all.
        :param widget_types: Only include these widget types
            (see :data:`pykada.enums.DASHBOARD_WIDGET_TYPES_ENUM`). Defaults to all.
        :return: The dashboard, range and ``widgets`` with their data.
        :raises ValueError: If ``dashboard_id`` is empty, or ``interval``,
            ``widget_types`` or a timestamp is invalid.
        """
        require_choice(interval, DASHBOARD_INTERVAL_ENUM, "interval")
        require_choice(widget_types, DASHBOARD_WIDGET_TYPES_ENUM, "widget_types")
        url = (f"{V2_OPERATIONAL_DASHBOARD_ENDPOINT}/"
               f"{path_segment(dashboard_id, 'dashboard_id')}/widget_trends/query")
        payload = remove_null_fields({
            "start_time": to_iso8601(start_time, "start_time"),
            "end_time": to_iso8601(end_time, "end_time"),
            "interval": interval,
            "site_ids": site_ids,
            "widget_ids": widget_ids,
            "widget_types": widget_types,
        })
        return self.request_manager.post(url, payload=payload)

    # ------------------------------------------------------------------
    # Cloud backup
    # ------------------------------------------------------------------

    @typechecked
    def get_cloud_backup_settings(self, camera_id: str) -> Dict[str, Any]:
        """
        Returns a camera's cloud backup settings and the latest backed-up segment times.

        :param camera_id: The unique identifier of the camera.
        :return: ``enabled``, ``video_to_upload``, ``video_quality``,
            ``backup_days`` (full weekday names), ``backup_window`` and
            ``upload_window`` (``{start_time, end_time}`` as ``HH:MM:SS``), and
            RFC 3339 ``latest_standard_quality_segment_time`` /
            ``latest_high_quality_segment_time`` (``None`` if nothing is backed up).
        :raises ValueError: If ``camera_id`` is empty.
        """
        url = (f"{V2_CAMERAS_ENDPOINT}/{path_segment(camera_id, 'camera_id')}"
               f"/cloud_backup/settings")
        return self.request_manager.get(url)

    @staticmethod
    def _cloud_backup_body(enabled, video_to_upload, video_quality,
                           backup_days, backup_window, upload_window) -> dict:
        require_choice(video_to_upload, VALID_CLOUD_BACKUP_VIDEO_TO_UPLOAD_ENUM,
                       "video_to_upload")
        require_choice(video_quality, VALID_CLOUD_BACKUP_VIDEO_QUALITY_ENUM,
                       "video_quality")
        require_choice(backup_days, WEEKDAY_FULL_ENUM, "backup_days")
        return remove_null_fields({
            "enabled": enabled,
            "video_to_upload": video_to_upload,
            "video_quality": video_quality,
            "backup_days": backup_days,
            "backup_window": _window(backup_window, "backup_window"),
            "upload_window": _window(upload_window, "upload_window"),
        })

    @typechecked
    def replace_cloud_backup_settings(self, camera_id: str,
                                      enabled: bool,
                                      video_to_upload: str,
                                      video_quality: str,
                                      backup_days: List[str],
                                      backup_window: Window,
                                      upload_window: Window) -> Dict[str, Any]:
        """
        Replace all of a camera's cloud backup settings.

        Every setting is required. To change only some, use
        :meth:`update_cloud_backup_settings`. Re-enabling backup on a camera
        that was previously enabled resumes from when it was disabled.

        :param camera_id: The unique identifier of the camera.
        :param enabled: Whether cloud backup is enabled.
        :param video_to_upload: ``"MOTION"`` (only footage with motion) or
            ``"ALL"`` (see :data:`pykada.enums.VALID_CLOUD_BACKUP_VIDEO_TO_UPLOAD_ENUM`).
        :param video_quality: ``"STANDARD_QUALITY"`` or ``"HIGH_QUALITY"``
            (see :data:`pykada.enums.VALID_CLOUD_BACKUP_VIDEO_QUALITY_ENUM`).
        :param backup_days: Full weekday names whose footage is backed up, e.g.
            ``["Monday", "Friday"]`` (see :data:`pykada.enums.WEEKDAY_FULL_ENUM`).
            An empty list backs up no days.
        :param backup_window: Daily ``(start, end)`` window of footage to back
            up, each a ``datetime.time`` or ``"HH:MM:SS"``. Use ``"24:00:00"``
            for a window that runs to midnight.
        :param upload_window: Daily ``(start, end)`` window when uploads may run,
            e.g. ``("01:00:00", "05:00:00")`` to keep traffic off business hours.
        :return: The settings now in effect.
        :raises ValueError: If ``camera_id`` is empty, an enum value or weekday
            is invalid, or a window is malformed or doesn't end after it starts.
        """
        url = (f"{V2_CAMERAS_ENDPOINT}/{path_segment(camera_id, 'camera_id')}"
               f"/cloud_backup/settings")
        payload = self._cloud_backup_body(enabled, video_to_upload, video_quality,
                                          backup_days, backup_window, upload_window)
        return self.request_manager.put(url, payload=payload)

    @typechecked
    def update_cloud_backup_settings(self, camera_id: str,
                                     enabled: Optional[bool] = None,
                                     video_to_upload: Optional[str] = None,
                                     video_quality: Optional[str] = None,
                                     backup_days: Optional[List[str]] = None,
                                     backup_window: Optional[Window] = None,
                                     upload_window: Optional[Window] = None) -> Dict[str, Any]:
        """
        Change some of a camera's cloud backup settings, leaving the rest as they are.

        At least one setting is required. ``backup_days`` replaces the existing
        list rather than adding to it. See :meth:`replace_cloud_backup_settings`
        for the meaning of each setting.

        :param camera_id: The unique identifier of the camera.
        :param enabled: Whether cloud backup is enabled.
        :param video_to_upload: ``"MOTION"`` or ``"ALL"``.
        :param video_quality: ``"STANDARD_QUALITY"`` or ``"HIGH_QUALITY"``.
        :param backup_days: Full weekday names whose footage is backed up.
        :param backup_window: Daily ``(start, end)`` window of footage to back up.
        :param upload_window: Daily ``(start, end)`` window when uploads may run.
        :return: The full set of settings now in effect.
        :raises ValueError: If ``camera_id`` is empty, no setting is given, an
            enum value or weekday is invalid, or a window is malformed.
        """
        url = (f"{V2_CAMERAS_ENDPOINT}/{path_segment(camera_id, 'camera_id')}"
               f"/cloud_backup/settings")
        payload = self._cloud_backup_body(enabled, video_to_upload, video_quality,
                                          backup_days, backup_window, upload_window)
        if not payload:
            raise ValueError("At least one cloud backup setting must be provided.")
        return self.request_manager.patch(url, payload=payload)

    # ------------------------------------------------------------------
    # PTZ, audio and viewing stations
    # ------------------------------------------------------------------

    @typechecked
    def get_ptz_presets(self, camera_id: str) -> Dict[str, Any]:
        """
        Returns a PTZ camera's saved preset positions, in the order shown in Command.

        Each item has a ``preset_id``, ``is_home`` (the idle position, shown as
        'H' in Command), 1-based ``position`` and RFC 3339 ``created_at``.
        Positions shift when presets change, so store ``preset_id``.

        :param camera_id: The unique identifier of the PTZ camera.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``camera_id`` is empty.
        """
        url = f"{V2_CAMERAS_ENDPOINT}/{path_segment(camera_id, 'camera_id')}/ptz/presets"
        return self.request_manager.get(url)

    @typechecked
    def move_camera_to_ptz_preset(self, camera_id: str, preset_id: str) -> Dict[str, Any]:
        """
        Move a PTZ camera to one of its saved presets.

        The camera starts moving once the request is accepted and may take a
        few seconds to arrive. Raises ``VerkadaNotFoundError`` if the preset
        doesn't exist and ``VerkadaConflictError`` if the camera is offline.

        :param camera_id: The unique identifier of the PTZ camera.
        :param preset_id: The preset to move to (from :meth:`get_ptz_presets`).
        :return: The API response (empty on success).
        :raises ValueError: If ``camera_id`` or ``preset_id`` is empty.
        """
        require_non_empty_str(preset_id, "preset_id")
        url = f"{V2_CAMERAS_ENDPOINT}/{path_segment(camera_id, 'camera_id')}/ptz/position"
        return self.request_manager.post(url, payload={"preset_id": preset_id})

    @typechecked
    def get_camera_audio_status(self, camera_id: str) -> Dict[str, Any]:
        """
        Returns whether audio recording is enabled on a camera.

        Requires a "Camera Audio" API key. If audio is disabled for the whole
        organization, ``enabled`` is ``False`` regardless of the camera setting.

        :param camera_id: The unique identifier of the camera.
        :return: ``{"camera_id": str, "enabled": bool}``.
        :raises ValueError: If ``camera_id`` is empty.
        """
        url = f"{V2_CAMERAS_ENDPOINT}/{path_segment(camera_id, 'camera_id')}/audio"
        return self.request_manager.get(url)

    @typechecked
    def set_camera_audio_status(self, camera_id: str, enabled: bool) -> Dict[str, Any]:
        """
        Enable or disable audio recording on a camera.

        Requires a "Camera Audio" API key, audio enabled in Feature Manager,
        and a camera model that supports audio (otherwise
        ``VerkadaBadRequestError``).

        :param camera_id: The unique identifier of the camera.
        :param enabled: ``True`` to enable audio recording; ``False`` to disable it.
        :return: The API response (empty on success).
        :raises ValueError: If ``camera_id`` is empty.
        """
        url = f"{V2_CAMERAS_ENDPOINT}/{path_segment(camera_id, 'camera_id')}/audio"
        return self.request_manager.post(url, payload={"enabled": enabled})

    @typechecked
    def get_all_viewing_stations(self) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every Viewing Station in the organization, walking all pages automatically.

        :return: A generator that yields individual Viewing Station dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_viewing_stations(**kwargs),
        )

    @typechecked
    def get_viewing_stations(self,
                             limit: Optional[int] = None,
                             cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of Viewing Stations.

        Each item has the device ID, serial, status, name, app version, IP,
        RFC 3339 ``last_seen_at``, location, coordinates, site and timezone.

        :param limit: Maximum stations per page (1 to 200, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``limit`` is outside 1-200.
        """
        check_limit(limit, 200)
        params = remove_null_fields({"limit": limit, "cursor": cursor})
        return self.request_manager.get(V2_VIEWING_STATIONS_ENDPOINT, params=params)


# ---------------------------------------------------------------------------
# Module-level default client — shared across all functional wrappers so that
# token caching and connection pooling work across multiple calls.
# ---------------------------------------------------------------------------
_default_cameras_client: Optional[CamerasClient] = None


def _get_default_client() -> CamerasClient:
    global _default_cameras_client
    if _default_cameras_client is None:
        _default_cameras_client = CamerasClient()
    return _default_cameras_client


_WRAPPER_NOTE = ("This is a functional wrapper for its equivalent method in the "
                 "CamerasClient. It reuses a module-level client configured from "
                 "VERKADA_API_KEY, making it best for one-off scripts. For "
                 "multiple API calls or a non-default key, instantiate a "
                 "CamerasClient directly.")


# Camera devices and sites

@copy_docstring_from(CamerasClient.get_all_camera_data, note=_WRAPPER_NOTE)
@typechecked
def get_all_camera_data(site_ids: Optional[List[str]] = None):
    return _get_default_client().get_all_camera_data(site_ids)


@copy_docstring_from(CamerasClient.get_camera_data, note=_WRAPPER_NOTE)
@typechecked
def get_camera_data(site_ids: Optional[List[str]] = None, limit: Optional[int] = None,
                    cursor: Optional[str] = None):
    return _get_default_client().get_camera_data(site_ids, limit, cursor)


@copy_docstring_from(CamerasClient.get_all_camera_sites, note=_WRAPPER_NOTE)
@typechecked
def get_all_camera_sites():
    return _get_default_client().get_all_camera_sites()


@copy_docstring_from(CamerasClient.get_camera_sites, note=_WRAPPER_NOTE)
@typechecked
def get_camera_sites(limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().get_camera_sites(limit, cursor)


# Footage, thumbnails and streaming

@copy_docstring_from(CamerasClient.get_footage_link, note=_WRAPPER_NOTE)
@typechecked
def get_footage_link(camera_id: str, timestamp: Optional[Timestamp] = None):
    return _get_default_client().get_footage_link(camera_id, timestamp)


@copy_docstring_from(CamerasClient.get_historical_thumbnail, note=_WRAPPER_NOTE)
@typechecked
def get_historical_thumbnail(camera_id: str, timestamp: Optional[Timestamp] = None,
                             resolution: Optional[str] = None,
                             start_time: Optional[Timestamp] = None,
                             end_time: Optional[Timestamp] = None):
    return _get_default_client().get_historical_thumbnail(camera_id, timestamp, resolution,
                                                          start_time, end_time)


@copy_docstring_from(CamerasClient.get_latest_thumbnail, note=_WRAPPER_NOTE)
@typechecked
def get_latest_thumbnail(camera_id: str, resolution: Optional[str] = None):
    return _get_default_client().get_latest_thumbnail(camera_id, resolution)


@copy_docstring_from(CamerasClient.get_thumbnail_link, note=_WRAPPER_NOTE)
@typechecked
def get_thumbnail_link(camera_id: str, timestamp: Optional[Timestamp] = None,
                       expiry: Optional[Duration] = None,
                       start_time: Optional[Timestamp] = None,
                       end_time: Optional[Timestamp] = None):
    return _get_default_client().get_thumbnail_link(camera_id, timestamp, expiry,
                                                    start_time, end_time)


@copy_docstring_from(CamerasClient.get_streaming_token, note=_WRAPPER_NOTE)
@typechecked
def get_streaming_token(exclude_accessible_resources: Optional[bool] = None):
    return _get_default_client().get_streaming_token(exclude_accessible_resources)


# License Plates of Interest

@copy_docstring_from(CamerasClient.create_lpoi, note=_WRAPPER_NOTE)
@typechecked
def create_lpoi(license_plate: str, description: str):
    return _get_default_client().create_lpoi(license_plate, description)


@copy_docstring_from(CamerasClient.get_all_lpois, note=_WRAPPER_NOTE)
@typechecked
def get_all_lpois():
    return _get_default_client().get_all_lpois()


@copy_docstring_from(CamerasClient.get_lpois, note=_WRAPPER_NOTE)
@typechecked
def get_lpois(limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().get_lpois(limit, cursor)


@copy_docstring_from(CamerasClient.update_lpoi, note=_WRAPPER_NOTE)
@typechecked
def update_lpoi(license_plate: str, description: str):
    return _get_default_client().update_lpoi(license_plate, description)


@copy_docstring_from(CamerasClient.delete_lpoi, note=_WRAPPER_NOTE)
@typechecked
def delete_lpoi(license_plate: str):
    return _get_default_client().delete_lpoi(license_plate)


@copy_docstring_from(CamerasClient.create_bulk_lpois, note=_WRAPPER_NOTE)
@typechecked
def create_bulk_lpois(filename: str):
    return _get_default_client().create_bulk_lpois(filename)


@copy_docstring_from(CamerasClient.delete_bulk_lpois, note=_WRAPPER_NOTE)
@typechecked
def delete_bulk_lpois(filename: str):
    return _get_default_client().delete_bulk_lpois(filename)


# License Plate Recognition

@copy_docstring_from(CamerasClient.get_all_seen_license_plates, note=_WRAPPER_NOTE)
@typechecked
def get_all_seen_license_plates(camera_id: str, license_plate: Optional[str] = None,
                                start_time: Optional[Timestamp] = None,
                                end_time: Optional[Timestamp] = None):
    return _get_default_client().get_all_seen_license_plates(camera_id, license_plate,
                                                             start_time, end_time)


@copy_docstring_from(CamerasClient.get_seen_license_plates, note=_WRAPPER_NOTE)
@typechecked
def get_seen_license_plates(camera_id: str, license_plate: Optional[str] = None,
                            start_time: Optional[Timestamp] = None,
                            end_time: Optional[Timestamp] = None,
                            limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().get_seen_license_plates(camera_id, license_plate,
                                                         start_time, end_time, limit, cursor)


@copy_docstring_from(CamerasClient.get_all_lpr_timestamps, note=_WRAPPER_NOTE)
@typechecked
def get_all_lpr_timestamps(camera_id: str, license_plate: str,
                           start_time: Optional[Timestamp] = None,
                           end_time: Optional[Timestamp] = None):
    return _get_default_client().get_all_lpr_timestamps(camera_id, license_plate,
                                                        start_time, end_time)


@copy_docstring_from(CamerasClient.get_lpr_timestamps, note=_WRAPPER_NOTE)
@typechecked
def get_lpr_timestamps(camera_id: str, license_plate: str,
                       start_time: Optional[Timestamp] = None,
                       end_time: Optional[Timestamp] = None,
                       limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().get_lpr_timestamps(camera_id, license_plate,
                                                    start_time, end_time, limit, cursor)


@copy_docstring_from(CamerasClient.get_all_lpr_zones, note=_WRAPPER_NOTE)
@typechecked
def get_all_lpr_zones():
    return _get_default_client().get_all_lpr_zones()


@copy_docstring_from(CamerasClient.get_lpr_zones, note=_WRAPPER_NOTE)
@typechecked
def get_lpr_zones(limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().get_lpr_zones(limit, cursor)


@copy_docstring_from(CamerasClient.get_lpr_zone_metrics, note=_WRAPPER_NOTE)
@typechecked
def get_lpr_zone_metrics(zone_id: str, start_time: Timestamp, end_time: Timestamp):
    return _get_default_client().get_lpr_zone_metrics(zone_id, start_time, end_time)


@copy_docstring_from(CamerasClient.get_all_lpr_zone_records, note=_WRAPPER_NOTE)
@typechecked
def get_all_lpr_zone_records(zone_id: str, start_time: Optional[Timestamp] = None,
                             end_time: Optional[Timestamp] = None,
                             vehicle_status: Optional[str] = None):
    return _get_default_client().get_all_lpr_zone_records(zone_id, start_time, end_time,
                                                          vehicle_status)


@copy_docstring_from(CamerasClient.get_lpr_zone_records, note=_WRAPPER_NOTE)
@typechecked
def get_lpr_zone_records(zone_id: str, start_time: Optional[Timestamp] = None,
                         end_time: Optional[Timestamp] = None,
                         vehicle_status: Optional[str] = None,
                         limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().get_lpr_zone_records(zone_id, start_time, end_time,
                                                      vehicle_status, limit, cursor)


@copy_docstring_from(CamerasClient.search_all_ncic_license_plates, note=_WRAPPER_NOTE)
@typechecked
def search_all_ncic_license_plates(start_time: Timestamp, end_time: Timestamp,
                                   license_plate: Optional[str] = None,
                                   geo_fence: Optional[List[Tuple[float, float]]] = None):
    return _get_default_client().search_all_ncic_license_plates(start_time, end_time,
                                                                license_plate, geo_fence)


@copy_docstring_from(CamerasClient.search_ncic_license_plates, note=_WRAPPER_NOTE)
@typechecked
def search_ncic_license_plates(start_time: Timestamp, end_time: Timestamp,
                               license_plate: Optional[str] = None,
                               geo_fence: Optional[List[Tuple[float, float]]] = None,
                               limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().search_ncic_license_plates(start_time, end_time,
                                                            license_plate, geo_fence,
                                                            limit, cursor)


# Persons of Interest, People Lists and Smart Lists

@copy_docstring_from(CamerasClient.get_all_pois, note=_WRAPPER_NOTE)
@typechecked
def get_all_pois():
    return _get_default_client().get_all_pois()


@copy_docstring_from(CamerasClient.get_pois, note=_WRAPPER_NOTE)
@typechecked
def get_pois(limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().get_pois(limit, cursor)


@copy_docstring_from(CamerasClient.create_poi, note=_WRAPPER_NOTE)
@typechecked
def create_poi(image_path: str, label: str):
    return _get_default_client().create_poi(image_path, label)


@copy_docstring_from(CamerasClient.update_poi, note=_WRAPPER_NOTE)
@typechecked
def update_poi(person_id: str, label: str):
    return _get_default_client().update_poi(person_id, label)


@copy_docstring_from(CamerasClient.delete_poi, note=_WRAPPER_NOTE)
@typechecked
def delete_poi(person_id: str):
    return _get_default_client().delete_poi(person_id)


@copy_docstring_from(CamerasClient.get_all_people_lists, note=_WRAPPER_NOTE)
@typechecked
def get_all_people_lists():
    return _get_default_client().get_all_people_lists()


@copy_docstring_from(CamerasClient.get_people_lists, note=_WRAPPER_NOTE)
@typechecked
def get_people_lists(limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().get_people_lists(limit, cursor)


@copy_docstring_from(CamerasClient.delete_people_list, note=_WRAPPER_NOTE)
@typechecked
def delete_people_list(list_id: str):
    return _get_default_client().delete_people_list(list_id)


@copy_docstring_from(CamerasClient.get_all_smart_lists, note=_WRAPPER_NOTE)
@typechecked
def get_all_smart_lists():
    return _get_default_client().get_all_smart_lists()


@copy_docstring_from(CamerasClient.get_smart_lists, note=_WRAPPER_NOTE)
@typechecked
def get_smart_lists(limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().get_smart_lists(limit, cursor)


@copy_docstring_from(CamerasClient.delete_smart_list, note=_WRAPPER_NOTE)
@typechecked
def delete_smart_list(list_id: str):
    return _get_default_client().delete_smart_list(list_id)


# Analytics

@copy_docstring_from(CamerasClient.get_all_object_counts, note=_WRAPPER_NOTE)
@typechecked
def get_all_object_counts(camera_id: str, start_time: Optional[Timestamp] = None,
                          end_time: Optional[Timestamp] = None):
    return _get_default_client().get_all_object_counts(camera_id, start_time, end_time)


@copy_docstring_from(CamerasClient.get_object_counts, note=_WRAPPER_NOTE)
@typechecked
def get_object_counts(camera_id: str, start_time: Optional[Timestamp] = None,
                      end_time: Optional[Timestamp] = None,
                      limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().get_object_counts(camera_id, start_time, end_time,
                                                   limit, cursor)


@copy_docstring_from(CamerasClient.get_max_people_vehicle_counts, note=_WRAPPER_NOTE)
@typechecked
def get_max_people_vehicle_counts(camera_id: str, start_time: Optional[Timestamp] = None,
                                  end_time: Optional[Timestamp] = None,
                                  search_zones: Optional[List[List[int]]] = None):
    return _get_default_client().get_max_people_vehicle_counts(camera_id, start_time,
                                                               end_time, search_zones)


@copy_docstring_from(CamerasClient.get_occupancy_trends, note=_WRAPPER_NOTE)
@typechecked
def get_occupancy_trends(camera_id: str, start_time: Optional[Timestamp] = None,
                         end_time: Optional[Timestamp] = None,
                         interval: Optional[str] = None,
                         trend_type: Optional[str] = None,
                         preset_id: Optional[str] = None):
    return _get_default_client().get_occupancy_trends(camera_id, start_time, end_time,
                                                      interval, trend_type, preset_id)


@copy_docstring_from(CamerasClient.get_all_occupancy_trend_enabled_cameras,
                     note=_WRAPPER_NOTE)
@typechecked
def get_all_occupancy_trend_enabled_cameras():
    return _get_default_client().get_all_occupancy_trend_enabled_cameras()


@copy_docstring_from(CamerasClient.get_occupancy_trend_enabled_cameras, note=_WRAPPER_NOTE)
@typechecked
def get_occupancy_trend_enabled_cameras(limit: Optional[int] = None,
                                        cursor: Optional[str] = None):
    return _get_default_client().get_occupancy_trend_enabled_cameras(limit, cursor)


@copy_docstring_from(CamerasClient.get_object_position_mqtt, note=_WRAPPER_NOTE)
@typechecked
def get_object_position_mqtt(camera_id: str):
    return _get_default_client().get_object_position_mqtt(camera_id)


@copy_docstring_from(CamerasClient.set_object_position_mqtt, note=_WRAPPER_NOTE)
@typechecked
def set_object_position_mqtt(camera_id: str, broker_host_port: str, broker_cert: str,
                             client_username: Optional[str] = None,
                             client_password: Optional[str] = None):
    return _get_default_client().set_object_position_mqtt(camera_id, broker_host_port,
                                                          broker_cert, client_username,
                                                          client_password)


# Operational dashboards

@copy_docstring_from(CamerasClient.get_all_dashboards, note=_WRAPPER_NOTE)
@typechecked
def get_all_dashboards():
    return _get_default_client().get_all_dashboards()


@copy_docstring_from(CamerasClient.get_dashboards, note=_WRAPPER_NOTE)
@typechecked
def get_dashboards(limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().get_dashboards(limit, cursor)


@copy_docstring_from(CamerasClient.get_dashboard_occupancy_trend_data, note=_WRAPPER_NOTE)
@typechecked
def get_dashboard_occupancy_trend_data(dashboard_id: str,
                                       start_time: Optional[Timestamp] = None,
                                       end_time: Optional[Timestamp] = None,
                                       interval: Optional[str] = None):
    return _get_default_client().get_dashboard_occupancy_trend_data(dashboard_id, start_time,
                                                                    end_time, interval)


@copy_docstring_from(CamerasClient.get_dashboard_widget_trends, note=_WRAPPER_NOTE)
@typechecked
def get_dashboard_widget_trends(dashboard_id: str,
                                start_time: Optional[Timestamp] = None,
                                end_time: Optional[Timestamp] = None,
                                interval: Optional[str] = None,
                                site_ids: Optional[List[str]] = None,
                                widget_ids: Optional[List[str]] = None,
                                widget_types: Optional[List[str]] = None):
    return _get_default_client().get_dashboard_widget_trends(dashboard_id, start_time,
                                                             end_time, interval, site_ids,
                                                             widget_ids, widget_types)


# Cloud backup

@copy_docstring_from(CamerasClient.get_cloud_backup_settings, note=_WRAPPER_NOTE)
@typechecked
def get_cloud_backup_settings(camera_id: str):
    return _get_default_client().get_cloud_backup_settings(camera_id)


@copy_docstring_from(CamerasClient.replace_cloud_backup_settings, note=_WRAPPER_NOTE)
@typechecked
def replace_cloud_backup_settings(camera_id: str, enabled: bool, video_to_upload: str,
                                  video_quality: str, backup_days: List[str],
                                  backup_window: Window, upload_window: Window):
    return _get_default_client().replace_cloud_backup_settings(
        camera_id, enabled, video_to_upload, video_quality, backup_days,
        backup_window, upload_window)


@copy_docstring_from(CamerasClient.update_cloud_backup_settings, note=_WRAPPER_NOTE)
@typechecked
def update_cloud_backup_settings(camera_id: str, enabled: Optional[bool] = None,
                                 video_to_upload: Optional[str] = None,
                                 video_quality: Optional[str] = None,
                                 backup_days: Optional[List[str]] = None,
                                 backup_window: Optional[Window] = None,
                                 upload_window: Optional[Window] = None):
    return _get_default_client().update_cloud_backup_settings(
        camera_id, enabled, video_to_upload, video_quality, backup_days,
        backup_window, upload_window)


# PTZ, audio and viewing stations

@copy_docstring_from(CamerasClient.get_ptz_presets, note=_WRAPPER_NOTE)
@typechecked
def get_ptz_presets(camera_id: str):
    return _get_default_client().get_ptz_presets(camera_id)


@copy_docstring_from(CamerasClient.move_camera_to_ptz_preset, note=_WRAPPER_NOTE)
@typechecked
def move_camera_to_ptz_preset(camera_id: str, preset_id: str):
    return _get_default_client().move_camera_to_ptz_preset(camera_id, preset_id)


@copy_docstring_from(CamerasClient.get_camera_audio_status, note=_WRAPPER_NOTE)
@typechecked
def get_camera_audio_status(camera_id: str):
    return _get_default_client().get_camera_audio_status(camera_id)


@copy_docstring_from(CamerasClient.set_camera_audio_status, note=_WRAPPER_NOTE)
@typechecked
def set_camera_audio_status(camera_id: str, enabled: bool):
    return _get_default_client().set_camera_audio_status(camera_id, enabled)


@copy_docstring_from(CamerasClient.get_all_viewing_stations, note=_WRAPPER_NOTE)
@typechecked
def get_all_viewing_stations():
    return _get_default_client().get_all_viewing_stations()


@copy_docstring_from(CamerasClient.get_viewing_stations, note=_WRAPPER_NOTE)
@typechecked
def get_viewing_stations(limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().get_viewing_stations(limit, cursor)
