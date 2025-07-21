import base64
from typing import Optional, List, Any, Generator

from typeguard import typechecked
from pykada.endpoints import *
from pykada.helpers import remove_null_fields, iterate_paginated_results, \
    verify_csv_columns, require_non_empty_str, \
    VALID_OCCUPANCY_TRENDS_TYPES_ENUM, VALID_OCCUPANCY_TRENDS_INTERVALS_ENUM, \
    VALID_CLOUD_BACKUP_VIDEO_QUALITY_ENUM, \
    VALID_CLOUD_BACKUP_VIDEO_TO_UPLOAD_ENUM
from pykada.verkada_requests import *

def get_all_camera_alerts(start_time: Optional[int] = None,
                      end_time: Optional[int] = None,
                      include_image_url: Optional[bool] = None,
                      notification_type: Optional[List[str]] = None):
    return iterate_paginated_results(
        get_camera_alerts,
        initial_params={
            "start_time": start_time if start_time else None,
            "end_time": end_time if end_time else None,
            "include_image_url": include_image_url if include_image_url else None,
            "notification_type": notification_type if notification_type else None
        }
    )


@typechecked
def get_camera_alerts(start_time: Optional[int] = None,
                      end_time: Optional[int] = None,
                      include_image_url: Optional[bool] = None,
                      notification_type: Optional[List[str]] = None,
                      page_token: Optional[str] = None,
                      page_size: Optional[int] = None) -> dict:
    """
    Returns alerts for an organization within a specified time range.

    Alert types include camera offline, camera online, tamper, motion, crowd,
    and Person of Interest alerts.

    Motion alerts include whether people and/or vehicles were detected.
    Crowd alerts include the threshold set for the camera that detected the crowd and whether people or vehicles were detected.
    Person of Interest alerts include the label set for the person.

    :param start_time: The start of the time range for requested notifications.
                       Formatted as a Unix timestamp in seconds.
    :param end_time: The end of the time range for requested notifications.
                     Formatted as a Unix timestamp in seconds.
    :param include_image_url: Flag to include/exclude image URL for notification.
    :param page_token: The pagination token used to fetch the next page of results.
    :param page_size: The number of items returned in a single response.
    :param notification_type: A list of one or more values from person_of_interest, tamper, crowd,
                              motion, camera_offline, camera_online.
    :return: Notification list JSON object.
    """


    params = {
        "start_time": start_time,
        "end_time": end_time,
        "include_image_url": "true" if include_image_url is True else ("false" if include_image_url is False else None),
        "page_token": page_token,
        "page_size": page_size,
        "notification_type": ",".join(map(str, notification_type)) if notification_type else None,
    }
    params = remove_null_fields(params)
    return get_request(CAMERA_ALERTS_ENDPOINT, params=params)


@typechecked
def create_lpoi(license_plate: str, description: str) -> dict:
    """
    Creates a License Plate of Interest for an organization.

    :param license_plate: The license plate number for the new LPOI.
    :param description: The description for the new LPOI.
    :return: The created LPOI object.
    """
    payload = {"license_plate": license_plate, "description": description}
    url = f"{LPOI_ENDPOINT}"
    return post_request(url, payload)


def get_all_lpois():
    return iterate_paginated_results(
        get_lpois,
        items_key="license_plate_of_interest",
        next_token_key="next_page_token"
    )

@typechecked
def get_lpois(page_size: Optional[int] = None, page_token: Optional[str] = None) -> dict:
    """
    Returns creation time, description, and license plate number for all License Plates of Interest.

    :param page_size: The number of items returned in a single response.
    :param page_token: The pagination token used to fetch the next page of results.
    :return: All LPOI objects in the organization.
    """
    params = {
        "page_size": page_size,
        "page_token": page_token
    }
    params = remove_null_fields(params)
    url = f"{LPOI_ENDPOINT}"
    return get_request(url, params=params)

@typechecked
def update_lpoi(license_plate: str, description: str) -> dict:
    """
    Updates a license plate description from License Plates of Interest.

    :param license_plate: The license plate number of the License Plate of Interest.
    :param description: The new description for the license plate.
    :return: The updated LPOI object.
    """
    params = {"license_plate": license_plate}
    payload = {"description": description}
    url = f"{LPOI_ENDPOINT}"
    return patch_request(url, params=params, payload=payload)


@typechecked
def delete_lpoi(license_plate: str) -> dict:
    """
    Deletes a license plate from License Plates of Interest using a specified license plate number.

    :param license_plate: The license plate number of the License Plate of Interest.
    :return: The deleted LPOI object.
    """
    params = {"license_plate": license_plate}
    return delete_request(LPOI_ENDPOINT, params=params)

@typechecked
def create_bulk_lpois(filename: str) -> dict:
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
        return post_request(url, headers=headers, files=files)


@typechecked
def delete_bulk_lpois(filename: str) -> dict:
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
        return delete_request(url, headers=headers, files=files)


def get_all_seen_license_plates(camera_id: str,
                           license_plate: Optional[str] = None,
                           start_time: Optional[int] = None,
                           end_time: Optional[int] = None)\
        -> Generator[Any, None, None]:
    return iterate_paginated_results(
        get_seen_license_plates,
        initial_params={
            "camera_id": camera_id,
            "license_plate": license_plate,
            "start_time": start_time if start_time else None,
            "end_time": end_time if end_time else None
        },
        next_token_key="next_page_token",
        items_key="detections"
    )

@typechecked
def get_seen_license_plates(camera_id: str,
                           license_plate: Optional[str] = None,
                           start_time: Optional[int] = None,
                           end_time: Optional[int] = None,
                           page_size: Optional[int] = None,
                           page_token: Optional[str] = None) -> dict:
    """
    Returns the timestamps, detected license plate numbers, and images of all
    license plates seen by a camera.

    :param camera_id: The unique identifier of the camera.
    :param license_plate: License plate number to filter by.
    :param start_time: Start of the time range (Unix timestamp in seconds).
    :param end_time: End of the time range (Unix timestamp in seconds).
    :param page_size: Number of items per response.
    :param page_token: Pagination token for the next page.
    :return: A dictionary with timestamps for the given camera and license plate.
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
    url = f"{LPR_PLATE_IMAGES_ENDPOINT}"
    return get_request(url, params=params)

def get_all_lpr_timestamps(camera_id: str,
                           license_plate: str,
                           start_time: Optional[int] = None,
                           end_time: Optional[int] = None)\
        -> Generator[Any, None, None]:
    return iterate_paginated_results(
        get_lpr_timestamps,
        initial_params={
            "camera_id": camera_id,
            "license_plate": license_plate,
            "start_time": start_time if start_time else None,
            "end_time": end_time if end_time else None
        },
        next_token_key = "next_page_token",
        items_key = "detections"
    )

@typechecked
def get_lpr_timestamps(camera_id: str,
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
    return get_request(url, params=params)

def get_all_object_counts(camera_id: str, start_time: Optional[int] = None,
                      end_time: Optional[int] = None):
    params = {
        "camera_id":camera_id,
        "start_time": start_time,
        "end_time": end_time
    }

    return iterate_paginated_results(get_object_counts,
                                     items_key="object_counts",
                                     next_token_key="next_page_token",
                                     initial_params=params)

@typechecked
def get_object_counts(camera_id: str, start_time: Optional[int] = None,
                      end_time: Optional[int] = None, page_size: Optional[int] = None,
                      page_token: Optional[str] = None) -> dict:
    """
    Returns the count of people and vehicles within a specified time range.

    :param camera_id: The unique identifier of the camera.
    :param start_time: Start of the time range (Unix timestamp in seconds).
    :param end_time: End of the time range (Unix timestamp in seconds).
    :param page_size: Number of items per response.
    :param page_token: Pagination token for the next page.
    :return: A dictionary with people/vehicle count objects.
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
    url = f"{OBJECT_COUNT_ENDPOINT}"
    return get_request(url, params=params)


@typechecked
def set_object_position_mqtt(broker_cert: str, broker_host_port: str,
                             camera_id: str, client_username: str = None,
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

# TODO: Add Preset ID field
@typechecked
def get_occupancy_trends(camera_id: str,
                         start_time: Optional[int] = None,
                         end_time: Optional[int] = None,
                         interval: Optional[str] = None,
                         type: Optional[str] = None,
                         preset_id: Optional[str]=None) -> dict:
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
        raise ValueError(f"Occupancy Trend Interval {interval} is not in the "
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
def get_cloud_backup_settings(camera_id: str) -> dict:
    """
    Retrieves cloud backup settings for a specified camera.

    :param camera_id: The unique identifier of the camera.
    :return: A dictionary of the current cloud backup settings.
    """
    params = {"camera_id": camera_id}
    url = f"{CLOUD_BACKUP_ENDPOINT}"
    return get_request(url, params=params)


@typechecked
def update_cloud_backup_settings(camera_id: str,
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
    # Validate camera_id
    require_non_empty_str(camera_id, "camera_id")

    # Validate days_to_preserve
    if not isinstance(days_to_preserve, str) or len(days_to_preserve.split(',')) != 7:
        raise ValueError("days_to_preserve must be a comma-delimited string of 7 values (0 or 1).")
    if any(day not in {"0", "1"} for day in days_to_preserve.split(',')):
        raise ValueError("Each value in days_to_preserve must be either '0' or '1'.")

    # Validate enabled
    if enabled not in {0, 1}:
        raise ValueError("enabled must be 0 (disabled) or 1 (enabled).")

    # Validate time_to_preserve
    if not isinstance(time_to_preserve, str) or len(time_to_preserve.split(',')) != 2:
        raise ValueError("time_to_preserve must be a comma-delimited string of start_time and end_time.")
    try:
        start_time, end_time = map(int, time_to_preserve.split(','))
        if not (0 <= start_time < 86400 and 0 <= end_time <= 86400):
            raise ValueError
    except ValueError:
        raise ValueError("start_time and end_time in time_to_preserve must be integers between 0 and 86400.")

    # Validate upload_timeslot
    if not isinstance(upload_timeslot, str) or len(upload_timeslot.split(',')) != 2:
        raise ValueError("upload_timeslot must be a comma-delimited string of start_time and end_time.")
    try:
        upload_start, upload_end = map(int, upload_timeslot.split(','))
        if not (0 <= upload_start < 86400 and 0 <= upload_end <= 86400):
            raise ValueError
    except ValueError:
        raise ValueError("start_time and end_time in upload_timeslot must be integers between 0 and 86400.")

    # Validate video_quality
    if video_quality not in VALID_CLOUD_BACKUP_VIDEO_QUALITY_ENUM.values():
        raise ValueError(f"video_quality must be one of {VALID_CLOUD_BACKUP_VIDEO_QUALITY_ENUM}.")

    # Validate video_to_upload
    if video_to_upload not in VALID_CLOUD_BACKUP_VIDEO_TO_UPLOAD_ENUM.values():
        raise ValueError(f"video_to_upload must be one of {VALID_CLOUD_BACKUP_VIDEO_TO_UPLOAD_ENUM.values()}.")

    # Adjust video_quality if video_to_upload is "MOTION"
    if video_to_upload == "MOTION":
        video_quality = "HIGH_QUALITY"

    # Prepare payload
    payload = {
        "camera_id": camera_id,
        "days_to_preserve": days_to_preserve,
        "enabled": enabled,
        "time_to_preserve": time_to_preserve,
        "upload_timeslot": upload_timeslot,
        "video_quality": video_quality,
        "video_to_upload": video_to_upload
    }

    # Send request
    url = f"{CLOUD_BACKUP_ENDPOINT}"
    return post_request(url, payload)

@typechecked
def get_all_camera_data():
    return iterate_paginated_results(
        get_camera_data,
        items_key="cameras",
        next_token_key="next_page_token"
    )

@typechecked
def get_camera_data(page_size: Optional[int] = None, page_token: Optional[str] = None) -> dict:
    """
    Returns details of all cameras within the organization.

    :param page_size: The number of items per response.
    :param page_token: Pagination token for the next page.
    :return: A dictionary with camera device information.
    """
    print(f"Fetching camera data... {page_token}")
    params = {
        "page_size": page_size,
        "page_token": page_token
    }
    params = remove_null_fields(params)
    url = f"{CAMERA_DATA_ENDPOINT}"
    return get_request(url, params=params)


@typechecked
def get_footage_link(camera_id: str, timestamp: Optional[int] = None) -> dict:
    """
    Returns a link to video footage for a specified camera at a given timestamp.

    :param camera_id: The unique identifier of the camera.
    :param timestamp: The timestamp (Unix timestamp in seconds); if not provided, returns a live link.
    :return: A dictionary containing the footage link.
    """
    params = {"camera_id": camera_id, "timestamp": timestamp}
    params = remove_null_fields(params)
    url = f"{FOOTAGE_LINK_ENDPOINT}"
    return get_request(url, params=params)


@typechecked
def get_historical_thumbnail(camera_id: str, timestamp: int = None,
                             resolution: str = None) -> bytes:
    """
    Returns a thumbnail (low or high resolution) from a specified camera at a given time.

    :param camera_id: The unique identifier of the camera.
    :param timestamp: The timestamp (Unix timestamp in seconds); if not provided, returns a live link.
    :param resolution: Either "low-res" or "high-res".
    :return: Raw byte output of the thumbnail image.
    """
    params = {"camera_id": camera_id, "timestamp": timestamp, "resolution": resolution}
    params = remove_null_fields(params)
    url = f"{CAMERA_THUMBNAIL_ENDPOINT}"
    return get_request_image(url, params=params)


@typechecked
def get_latest_thumbnail(camera_id: str, resolution: Optional[str] = None) -> bytes:
    """
    Returns the latest thumbnail from a specified camera in low or high resolution.

    :param camera_id: The unique identifier of the camera.
    :param resolution: Either "low-res" or "high-res".
    :return: Raw byte output of the latest thumbnail image.
    """
    params = {"camera_id": camera_id, "resolution": resolution}
    params = remove_null_fields(params)
    url = f"{LATEST_THUMBNAIL_ENDPOINT}"
    return get_request_image(url, params=params)


@typechecked
def get_thumbnail_link(camera_id: str,
                       timestamp: Optional[int] = None,
                       expiry: Optional[int] = 3600) -> dict:
    """
    Returns a link to a thumbnail image from a specified camera at a given timestamp.

    :param camera_id: The unique identifier of the camera.
    :param timestamp: The timestamp (Unix timestamp in seconds); if not provided, returns a live link.
    :param expiry: The expiry duration for the link (Unix timestamp in seconds).
    :return: A dictionary containing the thumbnail link.
    """
    params = {"camera_id": camera_id, "timestamp": timestamp, "expiry": expiry}
    params = remove_null_fields(params)
    url = f"{THUMBNAIL_LINK_ENDPOINT}"
    return get_request(url, params=params)


def get_all_pois():
    return iterate_paginated_results(
        get_pois,
        # items_key="persons_of_interest",
        # next_token_key="page_token"
    )

@typechecked
def get_pois(page_size: Optional[int] = 0,
             page_token: Optional[int] = "") -> dict:
    """
    Returns details for all Persons of Interest in the organization.

    :param page_size: The number of items per response.
    :param page_token: Pagination token for the next page.

    :return: A dictionary containing POI objects.
    """
    url = f"{POI_ENDPOINT}"
    return get_request(url)


@typechecked
def create_poi(image_url: str, label: str) -> dict:
    """
    Creates a Person of Interest using a base64-encoded image and label.

    :param image_url: The location of the POI image
    :param label: A descriptive label for the POI.
    :return: The newly created POI object.
    """
    with open(image_url, 'rb') as f:
        encoded_image = base64.b64encode(f.read()).decode('utf-8')

    payload = {"base64_image": encoded_image, "label": label}
    url = f"{POI_ENDPOINT}"
    return post_request(url, payload)


@typechecked
def update_poi(person_id: str, label: str) -> dict:
    """
    Updates the label of a Person of Interest.

    :param person_id: The unique identifier of the POI.
    :param label: The new label for the POI.
    :return: The updated POI object.
    """
    params = {"person_id": person_id}
    payload = {"label": label}
    url = f"{POI_ENDPOINT}"
    return patch_request(url, params=params, payload=payload)


@typechecked
def delete_poi(person_id: str) -> dict:
    """
    Deletes a Person of Interest from the organization.

    :param person_id: The unique identifier of the POI.
    :return: The deleted POI object.
    """
    params = {"person_id": person_id}
    url = f"{POI_ENDPOINT}"
    return delete_request(url, params=params)


@typechecked
def get_dashboard_occupancy_trend_data(dashboard_id: str,
                                       start_time: Optional[int] = None,
                                       end_time: Optional[int] = None,
                                       interval: Optional[str] = None):
    require_non_empty_str(dashboard_id, "dashboard_id")

    params = {
        "dashboard_id": dashboard_id,
        "start_time": start_time,
        "end_time": end_time,
        "interval": interval
    }

    params = remove_null_fields(params)

    return get_request(DASHBOARD_OCCUPANCY_TRENDS_ENDPOINT, params=params)

@typechecked
def get_occupancy_trend_enabled_cameras():
    return get_request(OCCUPANCY_TRENDS_ENABLED_CAMERAS_ENDPOINT)

@typechecked
def get_max_people_vehicle_counts(camera_id:str,
                                  start_time: Optional[int] = None,
                                  end_time: Optional[int] = None,
                                  search_zones: Optional[List[List[int]]] = None):
    require_non_empty_str(camera_id, "camera_id")

    params = {
        "camera_id": camera_id,
        "start_time": start_time,
        "end_time": end_time,
        "search_zones": str(search_zones)
    }

    params = remove_null_fields(params)

    return get_request(MAX_OBJECT_COUNT_ENDPOINT, params=params)

@typechecked
def get_camera_audio_status(camera_id: str) -> dict:
    """
    Returns the audio status of a specified camera.

    :param camera_id: The unique identifier of the camera.
    :return: A dictionary containing the audio status.
    """
    require_non_empty_str(camera_id, "camera_id")

    params = {"camera_id": camera_id}
    url = f"{CAMERA_AUDIO_ENDPOINT}"
    return get_request(url, params=params)

@typechecked
def set_camera_audio_status(camera_id: str,
                            enable_audio: bool) -> dict:
    """
    Sets the audio status of a specified camera.

    :param camera_id: The unique identifier of the camera.
    :param enable_audio: True to enable audio; otherwise, False.
    :return: A dictionary containing the updated audio status.
    """
    require_non_empty_str(camera_id, "camera_id")

    payload = {"camera_id": camera_id,
              "enable_audio": enable_audio}

    url = f"{CAMERA_AUDIO_ENDPOINT}"

    return post_request(url,payload=payload)