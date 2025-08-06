import base64
from typing import List, Any, Generator

from typeguard import typechecked

from pykada.api_tokens import get_default_token_manager, VerkadaTokenManager
from pykada.endpoints import *
from pykada.helpers import remove_null_fields, verify_csv_columns, require_non_empty_str, \
    VALID_OCCUPANCY_TRENDS_TYPES_ENUM, VALID_OCCUPANCY_TRENDS_INTERVALS_ENUM, \
    VALID_CLOUD_BACKUP_VIDEO_QUALITY_ENUM, \
    VALID_CLOUD_BACKUP_VIDEO_TO_UPLOAD_ENUM
from pykada.verkada_requests import *

class CamerasClient:

    def __init__(self, api_key = None):
        self.token_manager = VerkadaTokenManager(api_key=api_key) \
            if api_key else get_default_token_manager()


    @typechecked
    def get_camera_alerts(self,
                          start_time: Optional[int] = None,
                          end_time: Optional[int] = None,
                          include_image_url: Optional[bool] = None,
                          notification_type: Optional[List[str]] = None,
                          page_token: Optional[str] = None,
                          page_size: Optional[int] = None) -> dict:
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
        return get_request(CAMERA_ALERTS_ENDPOINT, params=params,
                           token_manager=self.token_manager)
    
    def get_all_camera_alerts(self,
                              start_time: Optional[int] = None,
                              end_time: Optional[int] = None,
                              include_image_url: Optional[bool] = None,
                              notification_type: Optional[List[str]] = None):
        return iterate_paginated_results(
            lambda **kwargs: self.get_camera_alerts(**kwargs),
            initial_params={
                "start_time": start_time,
                "end_time": end_time,
                "include_image_url": include_image_url,
                "notification_type": notification_type
            }
        )
    
    @typechecked
    def create_lpoi(self, license_plate: str,
                    description: str) -> dict:
        payload = {"license_plate": license_plate,
                   "description": description}
        return post_request(LPOI_ENDPOINT, payload,
                            token_manager=self.token_manager)
    
    def get_all_lpois(self):
        return iterate_paginated_results(
            lambda **kwargs: self.get_lpois(**kwargs),
            items_key="license_plate_of_interest",
            next_token_key="next_page_token"
        )
    
    @typechecked
    def get_lpois(self, page_size: Optional[int] = None,
                  page_token: Optional[str] = None) -> dict:
        params = {"page_size": page_size, "page_token": page_token}
        params = remove_null_fields(params)
        return get_request(LPOI_ENDPOINT, params=params,
                           token_manager=self.token_manager)
    
    @typechecked
    def update_lpoi(self, license_plate: str,
                    description: str) -> dict:
        params = {"license_plate": license_plate}
        payload = {"description": description}
        return patch_request(LPOI_ENDPOINT, params=params, payload=payload,
                             token_manager=self.token_manager)
    
    @typechecked
    def delete_lpoi(self, license_plate: str) -> dict:
        params = {"license_plate": license_plate}
        return delete_request(LPOI_ENDPOINT, params=params,
                              token_manager=self.token_manager)

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
            return post_request(url, headers=headers, files=files, token_manager=self.token_manager)

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
            return delete_request(url, headers=headers, files=files, token_manager=self.token_manager)
    
    def get_all_seen_license_plates(self, camera_id: str,
                                    license_plate: Optional[str] = None,
                                    start_time: Optional[int] = None,
                                    end_time: Optional[int] = None):
        return iterate_paginated_results(
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
        return get_request(LPR_PLATE_IMAGES_ENDPOINT, params=params,
                           token_manager=self.token_manager)

    @typechecked
    def get_lpr_timestamps(self,
                           camera_id: str,
                           license_plate: str,
                           start_time: Optional[int] = None,
                           end_time: Optional[int] = None,
                           page_size: Optional[int] = None,
                           page_token: Optional[str] = None) -> dict:
        """
        Returns the timestamps for a certain license plate (only for LPR-enabled cameras).

        :param camera_id: The unique identifier of the camera.
        :param license_plate: The license plate number.
        :param start_time: Start of the time range (Unix timestamp in seconds).
        :param end_time: End of the time range (Unix timestamp in seconds).
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
        return get_request(url, params=params, token_manager=self.token_manager)

    def get_all_lpr_timestamps(self,
                               camera_id: str,
                               license_plate: str,
                               start_time: Optional[int] = None,
                               end_time: Optional[int] = None) \
            -> Generator[Any, None, None]:
        return iterate_paginated_results(
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
        return iterate_paginated_results(
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
        require_non_empty_str(camera_id, "camera_id")
        params = {
            "camera_id": camera_id,
            "start_time": start_time,
            "end_time": end_time,
            "page_size": page_size,
            "page_token": page_token
        }
        params = remove_null_fields(params)
        return get_request(OBJECT_COUNT_ENDPOINT, params=params,
                           token_manager=self.token_manager)
    
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
        return post_request(url, payload)
    
    @typechecked
    def get_occupancy_trends(self, camera_id: str,
                             start_time: Optional[int] = None,
                             end_time: Optional[int] = None,
                             interval: Optional[str] = None,
                             type: Optional[str] = None,
                             preset_id: Optional[str] = None) -> dict:
        """
        Returns all occupancy trends data for a specified camera over a time range.
    
        :param camera_id: The unique identifier of the camera.
        :param start_time: Start time for the data (Unix timestamp in seconds).
        :param end_time: End time for the data (Unix timestamp in seconds).
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
        return get_request(url, params=params)
    
    @typechecked
    def get_cloud_backup_settings(self, camera_id: str) -> dict:
        """
        Retrieves cloud backup settings for a specified camera.
    
        :param camera_id: The unique identifier of the camera.
        :return: A dictionary of the current cloud backup settings.
        """
        params = {"camera_id": camera_id}
        url = f"{CLOUD_BACKUP_ENDPOINT}"
        return get_request(url, params=params)
    
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
        return post_request(url, payload)
    
    def get_all_camera_data(self):
        return iterate_paginated_results(
            lambda **kwargs: self.get_camera_data(**kwargs),
            items_key="cameras",
            next_token_key="next_page_token"
        )
    
    @typechecked
    def get_camera_data(self, page_size: Optional[int] = None,
                        page_token: Optional[str] = None) -> dict:
        """
        Returns details of all cameras within the organization.
    
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
        return get_request(url, params=params)
    
    def get_footage_link(self, camera_id: str,
                         timestamp: Optional[int] = None) -> dict:
        """
        Returns a link to video footage for a specified camera at a given timestamp.
        """
        params = {"camera_id": camera_id, "timestamp": timestamp}
        params = remove_null_fields(params)
        url = f"{FOOTAGE_LINK_ENDPOINT}"
        return get_request(url, params=params, token_manager=self.token_manager)
    
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
        return get_request_image(url, params=params,
                                 token_manager=self.token_manager)
    
    @typechecked
    def get_latest_thumbnail(self, camera_id: str,
                             resolution: Optional[str] = None) -> bytes:
        """
        Returns the latest thumbnail from a specified camera in low or high resolution.
        """
        params = {"camera_id": camera_id, "resolution": resolution}
        params = remove_null_fields(params)
        url = f"{LATEST_THUMBNAIL_ENDPOINT}"
        return get_request_image(url, params=params,
                                 token_manager=self.token_manager)
    
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
        return get_request(url, params=params, token_manager=self.token_manager)
    
    def get_all_pois(self):
        """
        Iterates through paginated results for Persons of Interest.
        """
        return iterate_paginated_results(
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
        return get_request(url, params=params, token_manager=self.token_manager)
    
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
        return post_request(url, payload=payload,
                            token_manager=self.token_manager)
    
    @typechecked
    def update_poi(self, person_id: str,
                   label: str) -> dict:
        """
        Updates the label of a Person of Interest.
        """
        params = {"person_id": person_id}
        payload = {"label": label}
        url = f"{POI_ENDPOINT}"
        return patch_request(url, params=params, payload=payload,
                             token_manager=self.token_manager)
    
    @typechecked
    def delete_poi(self, person_id: str) -> dict:
        """
        Deletes a Person of Interest from the organization.
        """
        params = {"person_id": person_id}
        url = f"{POI_ENDPOINT}"
        return delete_request(url, params=params,
                              token_manager=self.token_manager)
    
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
        return get_request(DASHBOARD_OCCUPANCY_TRENDS_ENDPOINT,
                           params=params, token_manager=self.token_manager)
    
    @typechecked
    def get_occupancy_trend_enabled_cameras(self) -> dict:
        """
        Returns cameras enabled for occupancy trends.
        """
        return get_request(OCCUPANCY_TRENDS_ENABLED_CAMERAS_ENDPOINT,
                           token_manager=self.token_manager)
    
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
        return get_request(MAX_OBJECT_COUNT_ENDPOINT, params=params,
                           token_manager=self.token_manager)
    
    @typechecked
    def get_camera_audio_status(self,
                                camera_id: str) -> dict:
        """
        Returns the audio status of a specified camera.
        """
        require_non_empty_str(camera_id, "camera_id")
        params = {"camera_id": camera_id}
        url = f"{CAMERA_AUDIO_ENDPOINT}"
        return get_request(url, params=params, token_manager=self.token_manager)
    
    @typechecked
    def set_camera_audio_status(self, camera_id: str,
                                enable_audio: bool) -> dict:
        """
        Sets the audio status of a specified camera.
        """
        require_non_empty_str(camera_id, "camera_id")
        payload = {"camera_id": camera_id, "enable_audio": enable_audio}
        url = f"{CAMERA_AUDIO_ENDPOINT}"
        return post_request(url, payload=payload,
                            token_manager=self.token_manager)

def get_camera_alert(*args, **kwargs) -> dict:
    return CamerasClient().get_camera_alerts(*args, **kwargs)

def create_lpoi(*args, **kwargs) -> dict:
    return CamerasClient().create_lpoi(*args, **kwargs)

def get_all_camera_alerts(*args, **kwargs) -> Generator[Any, None, None]:
    return CamerasClient().get_all_camera_alerts(*args, **kwargs)

def get_all_lpois(*args, **kwargs) -> Generator[Any, None, None]:
    return CamerasClient().get_all_lpois()

def get_all_seen_license_plates(*args, **kwargs) -> Generator[Any, None, None]:
    return CamerasClient().get_all_seen_license_plates(*args, **kwargs)

def get_all_lpr_timestamps(*args, **kwargs) -> Generator[Any, None, None]:
    return CamerasClient().get_all_lpr_timestamps(*args, **kwargs)

def get_all_object_counts(*args, **kwargs) -> Generator[Any, None, None]:
    return CamerasClient().get_all_object_counts(*args, **kwargs)

def get_all_camera_data(*args, **kwargs) -> Generator[Any, None, None]:
    return CamerasClient().get_all_camera_data()

def get_all_pois(*args, **kwargs) -> Generator[Any, None, None]:
    return CamerasClient().get_all_pois()

def get_lpois(*args, **kwargs) -> dict:
    return CamerasClient().get_lpois(*args, **kwargs)

def update_lpoi(*args, **kwargs) -> dict:
    return CamerasClient().update_lpoi(*args, **kwargs)

def delete_lpoi(*args, **kwargs) -> dict:
    return CamerasClient().delete_lpoi(*args, **kwargs)

def create_bulk_lpois(*args, **kwargs) -> dict:
    return CamerasClient().create_bulk_lpois(*args, **kwargs)

def delete_bulk_lpois(*args, **kwargs) -> dict:
    return CamerasClient().delete_bulk_lpois(*args, **kwargs)

def get_seen_license_plates(*args, **kwargs) -> dict:
    return CamerasClient().get_seen_license_plates(*args, **kwargs)

def get_lpr_timestamps(*args, **kwargs) -> dict:
    return CamerasClient().get_lpr_timestamps(*args, **kwargs)

def get_object_counts(*args, **kwargs) -> dict:
    return CamerasClient().get_object_counts(*args, **kwargs)

def set_object_position_mqtt(*args, **kwargs) -> dict:
    return CamerasClient().set_object_position_mqtt(*args, **kwargs)

def get_occupancy_trends(*args, **kwargs) -> dict:
    return CamerasClient().get_occupancy_trends(*args, **kwargs)

def get_cloud_backup_settings(*args, **kwargs) -> dict:
    return CamerasClient().get_cloud_backup_settings(*args, **kwargs)

def update_cloud_backup_settings(*args, **kwargs) -> dict:
    return CamerasClient().update_cloud_backup_settings(*args, **kwargs)

def get_camera_data(*args, **kwargs) -> dict:
    return CamerasClient().get_camera_data(*args, **kwargs)

def get_footage_link(*args, **kwargs) -> dict:
    return CamerasClient().get_footage_link(*args, **kwargs)

def get_historical_thumbnail(*args, **kwargs) -> bytes:
    return CamerasClient().get_historical_thumbnail(*args, **kwargs)

def get_latest_thumbnail(*args, **kwargs) -> bytes:
    return CamerasClient().get_latest_thumbnail(*args, **kwargs)

def get_thumbnail_link(*args, **kwargs) -> dict:
    return CamerasClient().get_thumbnail_link(*args, **kwargs)

def get_pois(*args, **kwargs) -> dict:
    return CamerasClient().get_pois(*args, **kwargs)

def create_poi(*args, **kwargs) -> dict:
    return CamerasClient().create_poi(*args, **kwargs)

def update_poi(*args, **kwargs) -> dict:
    return CamerasClient().update_poi(*args, **kwargs)

def delete_poi(*args, **kwargs) -> dict:
    return CamerasClient().delete_poi(*args, **kwargs)

def get_dashboard_occupancy_trend_data(*args, **kwargs) -> dict:
    return CamerasClient().get_dashboard_occupancy_trend_data(*args, **kwargs)

def get_occupancy_trend_enabled_cameras(*args, **kwargs) -> dict:
    return CamerasClient().get_occupancy_trend_enabled_cameras(*args, **kwargs)

def get_max_people_vehicle_counts(*args, **kwargs) -> dict:
    return CamerasClient().get_max_people_vehicle_counts(*args, **kwargs)

def get_camera_audio_status(*args, **kwargs) -> dict:
    return CamerasClient().get_camera_audio_status(*args, **kwargs)

def set_camera_audio_status(*args, **kwargs) -> dict:
    return CamerasClient().set_camera_audio_status(*args, **kwargs)