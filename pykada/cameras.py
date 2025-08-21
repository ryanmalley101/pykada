import base64
from typing import List, Any, Generator

from typeguard import typechecked

from pykada.endpoints import *
from pykada.helpers import remove_null_fields, verify_csv_columns, require_non_empty_str
from pykada.enums import VALID_OCCUPANCY_TRENDS_INTERVALS_ENUM, \
    VALID_OCCUPANCY_TRENDS_TYPES_ENUM, VALID_CLOUD_BACKUP_VIDEO_QUALITY_ENUM, \
    VALID_CLOUD_BACKUP_VIDEO_TO_UPLOAD_ENUM
from pykada.verkada_client import BaseClient
from pykada.verkada_requests import *

class CamerasClient(BaseClient):
    """
    Client for interacting with Verkada Cameras API.
    """
    def __init__(self,
                 api_key: Optional[str] = None,
                 token_manager: Optional[VerkadaTokenManager] = None):
        super().__init__(api_key, token_manager)


    @typechecked
    def get_camera_alerts(self,
                          start_time: Optional[int] = None,
                          end_time: Optional[int] = None,
                          include_image_url: Optional[bool] = None,
                          notification_type: Optional[List[str]] = None,
                          page_token: Optional[str] = None,
                          page_size: Optional[int] = None) -> dict:
        """

        :param start_time: Start time for the data (Unix timestamp in seconds).
        :type start_time: int or None
        :param end_time: End time for the data (Unix timestamp in seconds).
        :type end_time: int or None
        :param include_image_url:
        :type include_image_url:
        :param notification_type:
        :type notification_type:
        :param page_token:
        :type page_token:
        :param page_size:
        :type page_size:
        :return:
        :rtype:
        """
        params = {
            "start_time": start_time,
            "end_time": end_time,
            "include_image_url": "true" if include_image_url is True else (
                "false" if include_image_url is False else None),
            "page_token": page_token,
            "page_size": page_size,
            "notification_type": ",".join(map(str,
                                              notification_type)) if notification_type else None,
        }
        params = remove_null_fields(params)
        return self.request_manager.get(CAMERA_ALERTS_ENDPOINT, params=params)
    
    def get_all_camera_alerts(self,
                              start_time: Optional[int] = None,
                              end_time: Optional[int] = None,
                              include_image_url: Optional[bool] = None,
                              notification_type: Optional[List[str]] = None):
        """

        :param start_time: Start time for the data (Unix timestamp in seconds).
        :type start_time: int or None
        :param end_time: End time for the data (Unix timestamp in seconds).
        :type end_time: int or None
        :param include_image_url:
        :param notification_type:
        :return:
        :rtype:
        """
        return VerkadaRequestManager.iterate_paginated_results(
            lambda **kwargs: self.get_camera_alerts(**kwargs),
            initial_params={
                "start_time": start_time,
                "end_time": end_time,
                "include_image_url": include_image_url,
                "notification_type": notification_type
            }
        )
    
    @typechecked
    def create_lpoi(self,
                    license_plate: str,
                    description: str) -> dict:
        """

        :param license_plate: License plate to be added
        :param description: Short text description of the plate
        :return: object response from Verkada API
        """
        payload = {"license_plate": license_plate,
                   "description": description}
        return self.request_manager.post(LPOI_ENDPOINT, payload)
    
    def get_all_lpois(self):
        """

        :return:
        :rtype:
        """
        return VerkadaRequestManager.iterate_paginated_results(
            lambda **kwargs: self.get_lpois(**kwargs),
            items_key="license_plate_of_interest",
            next_token_key="next_page_token"
        )
    
    @typechecked
    def get_lpois(self, page_size: Optional[int] = None,
                  page_token: Optional[str] = None) -> dict:
        """

        :param page_size: int
        :type page_size: in
        :param page_token:
        :type page_token:
        :return:
        :rtype:
        """
        params = {"page_size": page_size, "page_token": page_token}
        params = remove_null_fields(params)
        return self.request_manager.get(LPOI_ENDPOINT, params=params)
    
    @typechecked
    def update_lpoi(self, license_plate: str,
                    description: str) -> dict:
        """

        :param license_plate:
        :type license_plate:
        :param description:
        :type description:
        :return:
        :rtype:
        """
        params = {"license_plate": license_plate}
        payload = {"description": description}
        return self.request_manager.patch(LPOI_ENDPOINT, params=params, payload=payload)
    
    @typechecked
    def delete_lpoi(self, license_plate: str) -> dict:
        """

        :param license_plate:
        :type license_plate:
        :return:
        :rtype:
        """
        params = {"license_plate": license_plate}
        return self.request_manager.delete(LPOI_ENDPOINT, params=params)

    @typechecked
    def create_bulk_lpois(self, filename: str) -> dict:
        """
        Creates a License Plates of Interest in bulk for an organization.
        Include The csv file containing license plates to be added to the License
        Plate of Interest list. The column headers for the csv file should be
        "License Plate", "Name" for creating LPOIs.

        :param filename: The .csv file for creating the bulk LPOIs
        :return: The created LPOI objects.
        """

        verify_csv_columns(filename, ['License Plate', 'Name'])

        headers = {
            "accept": "application/json",
        }

        with open(filename, 'rb') as f:
            files = {
                "file": (filename, f, "text/csv")
            }
            print(files)
            url = f"{LPOI_BATCH_ENDPOINT}"
            return self.request_manager.post(url, headers=headers, files=files)

    @typechecked
    def delete_bulk_lpois(self, filename: str) -> dict:
        """
        Deletes License Plates of Interest in bulk for an organization.
        Include The csv file containing license plates to be added to the License
        Plate of Interest list. The column header for the csv file should be
        "License Plate".

        :param filename: The .csv file for deleting the bulk LPOIs
        :return: The deleted LPOI objects.
        """
        verify_csv_columns(filename, ['License Plate'])

        headers = {
            "accept": "application/json",
        }

        with open(filename, 'rb') as f:
            files = {
                "file": (filename, f, "text/csv")
            }
            print(files)
            url = f"{LPOI_BATCH_ENDPOINT}"
            return self.request_manager.delete(url, headers=headers, files=files)
    
    def get_all_seen_license_plates(self, camera_id: str,
                                    license_plate: Optional[str] = None,
                                    start_time: Optional[int] = None,
                                    end_time: Optional[int] = None):
        """

        :param camera_id:
        :type camera_id:
        :param license_plate:
        :type license_plate:
        :param start_time: Start time for the data (Unix timestamp in seconds).
        :type start_time: int or None
        :param end_time: End time for the data (Unix timestamp in seconds).
        :type end_time: int or None
        :return:
        :rtype:
        """
        return VerkadaRequestManager.iterate_paginated_results(
            lambda **kwargs: self.get_seen_license_plates(**kwargs),
            initial_params={
                "camera_id": camera_id,
                "license_plate": license_plate,
                "start_time": start_time,
                "end_time": end_time
            },
            next_token_key="next_page_token",
            items_key="detections"
        )
    
    @typechecked
    def get_seen_license_plates(self, camera_id: str,
                                license_plate: Optional[str] = None,
                                start_time: Optional[int] = None,
                                end_time: Optional[int] = None,
                                page_size: Optional[int] = None,
                                page_token: Optional[str] = None) -> dict:
        """

        :param camera_id:
        :type camera_id:
        :param license_plate:
        :type license_plate:
        :param start_time: Start time for the data (Unix timestamp in seconds).
        :type start_time: int or None
        :param end_time: End time for the data (Unix timestamp in seconds).
        :type end_time: int or None
        :param page_size:
        :type page_size:
        :param page_token:
        :type page_token:
        :return:
        :rtype:
        """
        require_non_empty_str(camera_id, "camera_id")
        params = {
            "camera_id": camera_id,
            "license_plate": license_plate,
            "start_time": start_time,
            "end_time": end_time,
            "page_size": page_size,
            "page_token": page_token
        }
        params = remove_null_fields(params)
        return self.request_manager.get(LPR_PLATE_IMAGES_ENDPOINT, params=params)

    @typechecked
    def get_lpr_timestamps(self,
                           camera_id: str,
                           license_plate: str,
                           start_time: Optional[int] = None,
                           end_time: Optional[int] = None,
                           page_size: Optional[int] = None,
                           page_token: Optional[str] = None) -> dict:
        """
        Returns the timestamps for a certain license plate (only for LPR-enabled cameras_tests).

        :param camera_id: The unique identifier of the camera.
        :param license_plate: The license plate number.
        :param start_time: Start time for the data (Unix timestamp in seconds).
        :type start_time: int or None
        :param end_time: End time for the data (Unix timestamp in seconds).
        :type end_time: int or None
        :param page_size: Number of items per response.
        :param page_token: Pagination token for the next page.
        :return: A dictionary with timestamps for the given camera and license plate.
        """

        require_non_empty_str(camera_id, "camera_id")
        require_non_empty_str(license_plate, "license_plate")

        params = {
            "camera_id": camera_id,
            "license_plate": license_plate,
            "start_time": start_time,
            "end_time": end_time,
            "page_size": page_size,
            "page_token": page_token
        }
        params = remove_null_fields(params)
        url = f"{LPR_TIMESTAMPS_ENDPOINT}"
        return self.request_manager.get(url, params=params)

    def get_all_lpr_timestamps(self,
                               camera_id: str,
                               license_plate: str,
                               start_time: Optional[int] = None,
                               end_time: Optional[int] = None) \
            -> Generator[Any, None, None]:
        """

        :param camera_id:
        :type camera_id:
        :param license_plate:
        :type license_plate:
        :param start_time: Start time for the data (Unix timestamp in seconds).
        :type start_time: int or None
        :param end_time: End time for the data (Unix timestamp in seconds).
        :type end_time: int or None
        :param end_time:
        :type end_time:
        :return:
        :rtype:
        """
        return VerkadaRequestManager.iterate_paginated_results(
            lambda **kwargs: self.get_lpr_timestamps(**kwargs),
                initial_params={
                    "camera_id": camera_id,
                    "license_plate": license_plate,
                    "start_time": start_time if start_time else None,
                    "end_time": end_time if end_time else None
                },
                next_token_key="next_page_token",
                items_key="detections"
            )

    def get_all_object_counts(self, camera_id: str,
                              start_time: Optional[int] = None,
                              end_time: Optional[int] = None):
        """

        :param camera_id:
        :type camera_id:
        :param start_time: Start time for the data (Unix timestamp in seconds).
        :type start_time: int or None
        :param end_time: End time for the data (Unix timestamp in seconds).
        :type end_time: int or None
        :param end_time:
        :type end_time:
        :return:
        :rtype:
        """
        return VerkadaRequestManager.iterate_paginated_results(
            lambda **kwargs: self.get_object_counts(**kwargs),
            items_key="object_counts",
            next_token_key="next_page_token",
            initial_params={
                "camera_id":camera_id,
                "start_time": start_time,
                "end_time": end_time
            }
        )
    
    @typechecked
    def get_object_counts(self, camera_id: str,
                          start_time: Optional[int] = None,
                          end_time: Optional[int] = None,
                          page_size: Optional[int] = None,
                          page_token: Optional[str] = None) -> dict:
        """

        :param camera_id:
        :type camera_id:
        :param start_time: Start time for the data (Unix timestamp in seconds).
        :type start_time: int or None
        :param end_time: End time for the data (Unix timestamp in seconds).
        :type end_time: int or None
        :param page_size:
        :type page_size:
        :param page_token:
        :type page_token:
        :return:
        :rtype:
        """
        require_non_empty_str(camera_id, "camera_id")
        params = {
            "camera_id": camera_id,
            "start_time": start_time,
            "end_time": end_time,
            "page_size": page_size,
            "page_token": page_token
        }
        params = remove_null_fields(params)
        return self.request_manager.get(OBJECT_COUNT_ENDPOINT, params=params)
    
    @typechecked
    def set_object_position_mqtt(self, broker_cert: str,
                                 broker_host_port: str,
                                 camera_id: str,
                                 client_username: str = None,
                                 client_password: str = None) -> dict:
        """
        Sets the MQTT configuration for a particular camera.
    
        Object Position Events will be published to the specified MQTT broker.
    
        :param broker_cert: CA-signed certificate for TLS connection.
        :param broker_host_port: The host and port for the MQTT server.
        :param camera_id: The unique identifier of the camera.
        :param client_username: Optional username for the MQTT server.
        :param client_password: Optional password for the MQTT server.
        :return: The new MQTT configuration.
        """
        payload = {
            "broker_cert": broker_cert,
            "broker_host_port": broker_host_port,
            "camera_id": camera_id,
            "client_username": client_username,
            "client_password": client_password
        }
        url = f"{OBJECT_POSITION_MQTT_ENDPOINT}"
        return self.request_manager.post(url, payload)
    
    @typechecked
    def get_occupancy_trends(self, camera_id: str,
                             start_time: Optional[int] = None,
                             end_time: Optional[int] = None,
                             interval: Optional[str] = None,
                             type: Optional[str] = None,
                             preset_id: Optional[str] = None) -> dict:
        """
        Returns all occupancy trends data for a specified camera over a time range.
    
        :param preset_id:
        :type preset_id:
        :param camera_id: The unique identifier of the camera.
        :param start_time: Start time for the data (Unix timestamp in seconds).
        :type start_time: int or None
        :param end_time: End time for the data (Unix timestamp in seconds).
        :type end_time: int or None
        :param interval: Time interval (e.g., 15_minutes, 1_hour, etc.).
        :param type: Data type; for example, "person".
        :return: A JSON object with occupancy trends data.
        """
        if type not in VALID_OCCUPANCY_TRENDS_TYPES_ENUM.values():
            raise ValueError(f"Occupancy Trend Type {type} is not in the "
                             f"list of valid event types: "
                             f"{list(VALID_OCCUPANCY_TRENDS_TYPES_ENUM.values())}")
    
        if interval not in VALID_OCCUPANCY_TRENDS_INTERVALS_ENUM.values():
            raise ValueError(
                f"Occupancy Trend Interval {interval} is not in the "
                f"list of valid event types: "
                f"{list(VALID_OCCUPANCY_TRENDS_INTERVALS_ENUM.values())}")
    
        params = {
            "camera_id": camera_id,
            "start_time": start_time,
            "end_time": end_time,
            "interval": interval,
            "type": type,
            "preset_id": preset_id
        }
        params = remove_null_fields(params)
        url = f"{OBJECT_COUNT_ENDPOINT}"
        return self.request_manager.get(url, params=params)
    
    @typechecked
    def get_cloud_backup_settings(self, camera_id: str) -> dict:
        """
        Retrieves cloud backup settings for a specified camera.
    
        :param camera_id: The unique identifier of the camera.
        :return: A dictionary of the current cloud backup settings.
        """
        params = {"camera_id": camera_id}
        url = f"{CLOUD_BACKUP_ENDPOINT}"
        return self.request_manager.get(url, params=params)
    
    @typechecked
    def update_cloud_backup_settings(self, camera_id: str,
                                     days_to_preserve: str,
                                     enabled: int,
                                     time_to_preserve: str,
                                     upload_timeslot: str,
                                     video_quality: str,
                                     video_to_upload: str) -> dict:
        """
        Updates the cloud backup settings for a specified camera.
    
        :param camera_id: The unique identifier of the camera.
        :param days_to_preserve: Delimited list of booleans for each day (e.g., "0,1,1,1,1,1,0").
        :param enabled: 1 if cloud backup is enabled; otherwise, 0.
        :param time_to_preserve: Delimited list of start_time, end_time for footage backup (e.g., "3600,7200").
        :param upload_timeslot: Delimited list of start_time, end_time for upload schedule (e.g., "3600,7200").
        :param video_quality: Video quality ("STANDARD_QUALITY" or "HIGH_QUALITY").
        :param video_to_upload: Video type ("MOTION" or "ALL").
        :return: The updated cloud backup configuration.
        """
        require_non_empty_str(camera_id, "camera_id")
    
        if not isinstance(days_to_preserve, str) or len(
                days_to_preserve.split(',')) != 7:
            raise ValueError(
                "days_to_preserve must be a comma-delimited string of 7 values (0 or 1).")
        if any(day not in {"0", "1"} for day in
               days_to_preserve.split(',')):
            raise ValueError(
                "Each value in days_to_preserve must be either '0' or '1'.")
    
        if enabled not in {0, 1}:
            raise ValueError(
                "enabled must be 0 (disabled) or 1 (enabled).")
    
        if not isinstance(time_to_preserve, str) or len(
                time_to_preserve.split(',')) != 2:
            raise ValueError(
                "time_to_preserve must be a comma-delimited string of start_time and end_time.")
        try:
            start_time, end_time = map(int, time_to_preserve.split(','))
            if not (0 <= start_time < 86400 and 0 <= end_time <= 86400):
                raise ValueError
        except ValueError:
            raise ValueError(
                "start_time and end_time in time_to_preserve must be integers between 0 and 86400.")
    
        if not isinstance(upload_timeslot, str) or len(
                upload_timeslot.split(',')) != 2:
            raise ValueError(
                "upload_timeslot must be a comma-delimited string of start_time and end_time.")
        try:
            upload_start, upload_end = map(int, upload_timeslot.split(','))
            if not (
                    0 <= upload_start < 86400 and 0 <= upload_end <= 86400):
                raise ValueError
        except ValueError:
            raise ValueError(
                "start_time and end_time in upload_timeslot must be integers between 0 and 86400.")
    
        if video_quality not in VALID_CLOUD_BACKUP_VIDEO_QUALITY_ENUM.values():
            raise ValueError(
                f"video_quality must be one of {VALID_CLOUD_BACKUP_VIDEO_QUALITY_ENUM}.")
    
        if video_to_upload not in VALID_CLOUD_BACKUP_VIDEO_TO_UPLOAD_ENUM.values():
            raise ValueError(
                f"video_to_upload must be one of {VALID_CLOUD_BACKUP_VIDEO_TO_UPLOAD_ENUM.values()}.")
    
        if video_to_upload == "MOTION":
            video_quality = "HIGH_QUALITY"
    
        payload = {
            "camera_id": camera_id,
            "days_to_preserve": days_to_preserve,
            "enabled": enabled,
            "time_to_preserve": time_to_preserve,
            "upload_timeslot": upload_timeslot,
            "video_quality": video_quality,
            "video_to_upload": video_to_upload
        }
    
        url = f"{CLOUD_BACKUP_ENDPOINT}"
        return self.request_manager.post(url, payload)
    
    def get_all_camera_data(self):
        """

        :return:
        :rtype:
        """
        return VerkadaRequestManager.iterate_paginated_results(
            lambda **kwargs: self.get_camera_data(**kwargs),
            items_key="cameras_tests",
            next_token_key="next_page_token"
        )
    
    @typechecked
    def get_camera_data(self, page_size: Optional[int] = None,
                        page_token: Optional[str] = None) -> dict:
        """
        Returns details of all cameras_tests within the organization.
    
        :param page_size: The number of items per response.
        :param page_token: Pagination token for the next page.
        :return: A dictionary with camera device information.
        """
        params = {
            "page_size": page_size,
            "page_token": page_token
        }
        params = remove_null_fields(params)
        url = f"{CAMERA_DATA_ENDPOINT}"
        return self.request_manager.get(url, params=params)
    
    def get_footage_link(self, camera_id: str,
                         timestamp: Optional[int] = None) -> dict:
        """
        Returns a link to video footage for a specified camera at a given timestamp.
        """
        params = {"camera_id": camera_id, "timestamp": timestamp}
        params = remove_null_fields(params)
        url = f"{FOOTAGE_LINK_ENDPOINT}"
        return self.request_manager.get(url, params=params)
    
    @typechecked
    def get_historical_thumbnail(self, camera_id: str,
                                 timestamp: Optional[int] = None,
                                 resolution: Optional[
                                     str] = None) -> bytes:
        """
        Returns a thumbnail (low or high resolution) from a specified camera at a given time.
        """
        params = {"camera_id": camera_id, "timestamp": timestamp,
                  "resolution": resolution}
        params = remove_null_fields(params)
        url = f"{CAMERA_THUMBNAIL_ENDPOINT}"
        return self.request_manager.get_image(url, params=params)
    
    @typechecked
    def get_latest_thumbnail(self, camera_id: str,
                             resolution: Optional[str] = None) -> bytes:
        """
        Returns the latest thumbnail from a specified camera in low or high resolution.
        """
        params = {"camera_id": camera_id, "resolution": resolution}
        params = remove_null_fields(params)
        url = f"{LATEST_THUMBNAIL_ENDPOINT}"
        return self.request_manager.get_image(url, params=params)
    
    @typechecked
    def get_thumbnail_link(self, camera_id: str,
                           timestamp: Optional[int] = None,
                           expiry: Optional[int] = 3600) -> dict:
        """
        Returns a link to a thumbnail image from a specified camera at a given timestamp.
        """
        params = {"camera_id": camera_id, "timestamp": timestamp,
                  "expiry": expiry}
        params = remove_null_fields(params)
        url = f"{THUMBNAIL_LINK_ENDPOINT}"
        return self.request_manager.get(url, params=params)
    
    def get_all_pois(self):
        """
        Iterates through paginated results for Persons of Interest.
        """
        return VerkadaRequestManager.iterate_paginated_results(
            lambda **kwargs: self.get_pois(**kwargs),
            items_key="persons_of_interest",
            next_token_key="page_token"
        )
    
    @typechecked
    def get_pois(self, page_size: Optional[int] = None,
                 page_token: Optional[str] = None) -> dict:
        """
        Returns details for all Persons of Interest in the organization.
        """
        params = {"page_size": page_size, "page_token": page_token}
        params = remove_null_fields(params)
        url = f"{POI_ENDPOINT}"
        return self.request_manager.get(url, params=params)
    
    @typechecked
    def create_poi(self, image_url: str,
                   label: str) -> dict:
        """
        Creates a Person of Interest using a base64-encoded image and label.
        """
        with open(image_url, 'rb') as f:
            encoded_image = base64.b64encode(f.read()).decode('utf-8')
    
        payload = {"base64_image": encoded_image, "label": label}
        url = f"{POI_ENDPOINT}"
        return self.request_manager.post(url, payload=payload)
    
    @typechecked
    def update_poi(self, person_id: str,
                   label: str) -> dict:
        """
        Updates the label of a Person of Interest.
        """
        params = {"person_id": person_id}
        payload = {"label": label}
        url = f"{POI_ENDPOINT}"
        return self.request_manager.patch(url, params=params, payload=payload)
    
    @typechecked
    def delete_poi(self, person_id: str) -> dict:
        """
        Deletes a Person of Interest from the organization.
        """
        params = {"person_id": person_id}
        url = f"{POI_ENDPOINT}"
        return self.request_manager.delete(url, params=params)
    
    @typechecked
    def get_dashboard_occupancy_trend_data(self,
                                           dashboard_id: str,
                                           start_time: Optional[
                                               int] = None,
                                           end_time: Optional[int] = None,
                                           interval: Optional[
                                               str] = None) -> dict:
        """
        Returns occupancy trend data for a specified dashboard.
        """
        require_non_empty_str(dashboard_id, "dashboard_id")
        params = {
            "dashboard_id": dashboard_id,
            "start_time": start_time,
            "end_time": end_time,
            "interval": interval
        }
        params = remove_null_fields(params)
        return self.request_manager.get(DASHBOARD_OCCUPANCY_TRENDS_ENDPOINT,
                           params=params)
    
    @typechecked
    def get_occupancy_trend_enabled_cameras(self) -> dict:
        """
        Returns cameras_tests enabled for occupancy trends.
        """
        return self.request_manager.get(OCCUPANCY_TRENDS_ENABLED_CAMERAS_ENDPOINT)
    
    @typechecked
    def get_max_people_vehicle_counts(self, camera_id: str,
                                      start_time: Optional[int] = None,
                                      end_time: Optional[int] = None,
                                      search_zones: Optional[
                                          List[List[int]]] = None) -> dict:
        """
        Returns the maximum people and vehicle counts for a specified camera.
        """
        require_non_empty_str(camera_id, "camera_id")
        params = {
            "camera_id": camera_id,
            "start_time": start_time,
            "end_time": end_time,
            "search_zones": str(search_zones)
        }
        params = remove_null_fields(params)
        return self.request_manager.get(MAX_OBJECT_COUNT_ENDPOINT, params=params)
    
    @typechecked
    def get_camera_audio_status(self,
                                camera_id: str) -> dict:
        """
        Returns the audio status of a specified camera.
        """
        require_non_empty_str(camera_id, "camera_id")
        params = {"camera_id": camera_id}
        url = f"{CAMERA_AUDIO_ENDPOINT}"
        return self.request_manager.get(url, params=params)
    
    @typechecked
    def set_camera_audio_status(self, camera_id: str,
                                enable_audio: bool) -> dict:
        """
        Sets the audio status of a specified camera.
        """
        require_non_empty_str(camera_id, "camera_id")
        payload = {"camera_id": camera_id, "enable_audio": enable_audio}
        url = f"{CAMERA_AUDIO_ENDPOINT}"
        return self.request_manager.post(url, payload=payload)

    def get_viewing_stations(self) -> dict:
        """
        Returns a list of viewing stations in an organization.

        :return: A list of viewing stations within the organization
        :rtype: dict
        """
        return self.request_manager.get(f"{VIEWING_STATION_ENDPOINT}")


@typechecked
def create_bulk_lpois(filename: str):
    """
    Creates a License Plates of Interest in bulk for an organization.
    Include The csv file containing license plates to be added to the License
    Plate of Interest list. The column headers for the csv file should be
    "License Plate", "Name" for creating LPOIs.

    :param filename: The .csv file for creating the bulk LPOIs
    :return: The created LPOI objects.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().create_bulk_lpois(filename)

@typechecked
def create_lpoi(license_plate: str, description: str):
    """
    No docstring found.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().create_lpoi(license_plate, description)

@typechecked
def create_poi(image_url: str, label: str):
    """
    Creates a Person of Interest using a base64-encoded image and label.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().create_poi(image_url, label)

@typechecked
def delete_bulk_lpois(filename: str):
    """
    Deletes License Plates of Interest in bulk for an organization.
    Include The csv file containing license plates to be added to the License
    Plate of Interest list. The column header for the csv file should be
    "License Plate".

    :param filename: The .csv file for deleting the bulk LPOIs
    :return: The deleted LPOI objects.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().delete_bulk_lpois(filename)

@typechecked
def delete_lpoi(license_plate: str):
    """
    No docstring found.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().delete_lpoi(license_plate)

@typechecked
def delete_poi(person_id: str):
    """
    Deletes a Person of Interest from the organization.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().delete_poi(person_id)

@typechecked
def get_all_camera_alerts(start_time: Optional[int] = None, end_time: Optional[int] = None, include_image_url: Optional[bool] = None, notification_type: Optional[List[str]] = None):
    """
    No docstring found.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_all_camera_alerts(start_time, end_time, include_image_url, notification_type)

@typechecked
def get_all_camera_data():
    """
    No docstring found.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_all_camera_data()

@typechecked
def get_all_lpois():
    """
    No docstring found.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_all_lpois()

@typechecked
def get_all_lpr_timestamps(camera_id: str, license_plate: str, start_time: Optional[int] = None, end_time: Optional[int] = None):
    """
    No docstring found.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_all_lpr_timestamps(camera_id, license_plate, start_time, end_time)

@typechecked
def get_all_object_counts(camera_id: str, start_time: Optional[int] = None, end_time: Optional[int] = None):
    """
    No docstring found.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_all_object_counts(camera_id, start_time, end_time)

@typechecked
def get_all_pois():
    """
    Iterates through paginated results for Persons of Interest.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_all_pois()

@typechecked
def get_all_seen_license_plates(camera_id: str, license_plate: Optional[str] = None, start_time: Optional[int] = None, end_time: Optional[int] = None):
    """
    No docstring found.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_all_seen_license_plates(camera_id, license_plate, start_time, end_time)

@typechecked
def get_camera_alerts(start_time: Optional[int] = None, end_time: Optional[int] = None, include_image_url: Optional[bool] = None, notification_type: Optional[List[str]] = None, page_token: Optional[str] = None, page_size: Optional[int] = None):
    """
    No docstring found.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_camera_alerts(start_time, end_time, include_image_url, notification_type, page_token, page_size)

@typechecked
def get_camera_audio_status(camera_id: str):
    """
    Returns the audio status of a specified camera.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_camera_audio_status(camera_id)

@typechecked
def get_camera_data(page_size: Optional[int] = None, page_token: Optional[str] = None):
    """
    Returns details of all cameras_tests within the organization.

    :param page_size: The number of items per response.
    :param page_token: Pagination token for the next page.
    :return: A dictionary with camera device information.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_camera_data(page_size, page_token)

@typechecked
def get_cloud_backup_settings(camera_id: str):
    """
    Retrieves cloud backup settings for a specified camera.

    :param camera_id: The unique identifier of the camera.
    :return: A dictionary of the current cloud backup settings.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_cloud_backup_settings(camera_id)

@typechecked
def get_dashboard_occupancy_trend_data(dashboard_id: str, start_time: Optional[int] = None, end_time: Optional[int] = None, interval: Optional[str] = None):
    """
    Returns occupancy trend data for a specified dashboard.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_dashboard_occupancy_trend_data(dashboard_id, start_time, end_time, interval)

@typechecked
def get_footage_link(camera_id: str, timestamp: Optional[int] = None):
    """
    Returns a link to video footage for a specified camera at a given timestamp.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_footage_link(camera_id, timestamp)

@typechecked
def get_historical_thumbnail(camera_id: str, timestamp: Optional[int] = None, resolution: Optional[str] = None):
    """
    Returns a thumbnail (low or high resolution) from a specified camera at a given time.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_historical_thumbnail(camera_id, timestamp, resolution)

@typechecked
def get_latest_thumbnail(camera_id: str, resolution: Optional[str] = None):
    """
    Returns the latest thumbnail from a specified camera in low or high resolution.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_latest_thumbnail(camera_id, resolution)

@typechecked
def get_lpois(page_size: Optional[int] = None, page_token: Optional[str] = None):
    """
    No docstring found.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_lpois(page_size, page_token)

@typechecked
def get_lpr_timestamps(camera_id: str, license_plate: str, start_time: Optional[int] = None, end_time: Optional[int] = None, page_size: Optional[int] = None, page_token: Optional[str] = None):
    """
    Returns the timestamps for a certain license plate (only for LPR-enabled cameras_tests).

    :param camera_id: The unique identifier of the camera.
    :param license_plate: The license plate number.
    :param start_time: Start of the time range (Unix timestamp in seconds).
    :param end_time: End of the time range (Unix timestamp in seconds).
    :param page_size: Number of items per response.
    :param page_token: Pagination token for the next page.
    :return: A dictionary with timestamps for the given camera and license plate.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_lpr_timestamps(camera_id, license_plate, start_time, end_time, page_size, page_token)

@typechecked
def get_max_people_vehicle_counts(camera_id: str, start_time: Optional[int] = None, end_time: Optional[int] = None, search_zones: Optional[List[List[int]]] = None):
    """
    Returns the maximum people and vehicle counts for a specified camera.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_max_people_vehicle_counts(camera_id, start_time, end_time, search_zones)

@typechecked
def get_object_counts(camera_id: str, start_time: Optional[int] = None, end_time: Optional[int] = None, page_size: Optional[int] = None, page_token: Optional[str] = None):
    """
    No docstring found.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_object_counts(camera_id, start_time, end_time, page_size, page_token)

@typechecked
def get_occupancy_trend_enabled_cameras():
    """
    Returns cameras_tests enabled for occupancy trends.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_occupancy_trend_enabled_cameras()

@typechecked
def get_occupancy_trends(camera_id: str, start_time: Optional[int] = None, end_time: Optional[int] = None, interval: Optional[str] = None, type: Optional[str] = None, preset_id: Optional[str] = None):
    """
    Returns all occupancy trends data for a specified camera over a time range.

    :param preset_id:
    :type preset_id:
    :param camera_id: The unique identifier of the camera.
    :param start_time: Start time for the data (Unix timestamp in seconds).
    :type start_time: int or None
    :param end_time: End time for the data (Unix timestamp in seconds).
    :type end_time: int or None
    :param interval: Time interval (e.g., 15_minutes, 1_hour, etc.).
    :param type: Data type; for example, "person".
    :return: A JSON object with occupancy trends data.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_occupancy_trends(camera_id, start_time, end_time, interval, type, preset_id)

@typechecked
def get_pois(page_size: Optional[int] = None, page_token: Optional[str] = None):
    """
    Returns details for all Persons of Interest in the organization.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_pois(page_size, page_token)

@typechecked
def get_seen_license_plates(camera_id: str, license_plate: Optional[str] = None, start_time: Optional[int] = None, end_time: Optional[int] = None, page_size: Optional[int] = None, page_token: Optional[str] = None):
    """
    No docstring found.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_seen_license_plates(camera_id, license_plate, start_time, end_time, page_size, page_token)

@typechecked
def get_thumbnail_link(camera_id: str, timestamp: Optional[int] = None, expiry: Optional[int] = 3600):
    """
    Returns a link to a thumbnail image from a specified camera at a given timestamp.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().get_thumbnail_link(camera_id, timestamp, expiry)

@typechecked
def set_camera_audio_status(camera_id: str, enable_audio: bool):
    """
    Sets the audio status of a specified camera.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().set_camera_audio_status(camera_id, enable_audio)

@typechecked
def set_object_position_mqtt(broker_cert: str, broker_host_port: str, camera_id: str, client_username: str = None, client_password: str = None):
    """
    Sets the MQTT configuration for a particular camera.

    Object Position Events will be published to the specified MQTT broker.

    :param broker_cert: CA-signed certificate for TLS connection.
    :param broker_host_port: The host and port for the MQTT server.
    :param camera_id: The unique identifier of the camera.
    :param client_username: Optional username for the MQTT server.
    :param client_password: Optional password for the MQTT server.
    :return: The new MQTT configuration.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().set_object_position_mqtt(broker_cert, broker_host_port, camera_id, client_username, client_password)

@typechecked
def update_cloud_backup_settings(camera_id: str, days_to_preserve: str, enabled: int, time_to_preserve: str, upload_timeslot: str, video_quality: str, video_to_upload: str):
    """
    Updates the cloud backup settings for a specified camera.

    :param camera_id: The unique identifier of the camera.
    :param days_to_preserve: Delimited list of booleans for each day (e.g., "0,1,1,1,1,1,0").
    :param enabled: 1 if cloud backup is enabled; otherwise, 0.
    :param time_to_preserve: Delimited list of start_time, end_time for footage backup (e.g., "3600,7200").
    :param upload_timeslot: Delimited list of start_time, end_time for upload schedule (e.g., "3600,7200").
    :param video_quality: Video quality ("STANDARD_QUALITY" or "HIGH_QUALITY").
    :param video_to_upload: Video type ("MOTION" or "ALL").
    :return: The updated cloud backup configuration.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().update_cloud_backup_settings(camera_id, days_to_preserve, enabled, time_to_preserve, upload_timeslot, video_quality, video_to_upload)

@typechecked
def update_lpoi(license_plate: str, description: str):
    """
    No docstring found.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().update_lpoi(license_plate, description)

@typechecked
def update_poi(person_id: str, label: str):
    """
    Updates the label of a Person of Interest.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the CamerasClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a CamerasClient object directly for better performance.
    """
    return CamerasClient().update_poi(person_id, label)


def get_viewing_stations():
    """
    Returns a list of viewing stations in an organization.

    :return: A list of viewing stations within the organization
    :rtype: dict

    ---

    **Note:** This is a functional wrapper for its equivalent method in the ViewingStationClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a ViewingStationClient object directly for better performance.
    """
    return CamerasClient().get_viewing_stations()
