from typing import Optional, List

from typeguard import typechecked
from endpoints import *
from helpers import remove_null_fields
from verkada_requests import *

@typechecked
def get_alerts(start_time: Optional[int] = None,
               end_time: Optional[int] = None,
               include_image_url: Optional[bool] = None,
               page_token: Optional[str] = None,
               page_size: Optional[int] = None,
               notification_type: Optional[List[str]] = None) -> dict:
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
def delete_lpoi(license_plate: str) -> dict:
    """
    Deletes a license plate from License Plates of Interest using a specified license plate number.

    :param license_plate: The license plate number of the License Plate of Interest.
    :return: The deleted LPOI object.
    """
    params = {"license_plate": license_plate}
    return delete_request(LPOI_ENDPOINT, params=params)


@typechecked
def get_all_lpoi(page_size: Optional[int] = None, page_token: Optional[str] = None) -> dict:
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
    url = f"{LPR_ENDPOINT}"
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
    url = f"{LPR_ENDPOINT}"
    return patch_request(url, params=params, payload=payload)


@typechecked
def create_lpoi(license_plate: str, description: str) -> dict:
    """
    Creates a License Plate of Interest for an organization.

    :param license_plate: The license plate number for the new LPOI.
    :param description: The description for the new LPOI.
    :return: The created LPOI object.
    """
    payload = {"license_plate": license_plate, "description": description}
    url = f"{LPR_ENDPOINT}"
    return post_request(url, payload)


@typechecked
def get_lpr_timestamps(camera_id: str, license_plate: str,
                       start_time: Optional[int] = None, end_time: Optional[int] = None,
                       page_size: Optional[int] = None, page_token: Optional[str] = None) -> dict:
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
    params = {
        "camera_id": camera_id,
        "license_plate": license_plate,
        "start_time": start_time,
        "end_time": end_time,
        "page_size": page_size,
        "page_token": page_token
    }
    params = remove_null_fields(params)
    url = f"{LPR_ENDPOINT}"
    return get_request(url, params=params)


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
def get_occupancy_trends(camera_id: str, start_time: Optional[int] = None,
                         end_time: Optional[int] = None, interval: Optional[str] = None) -> dict:
    """
    Returns all occupancy trends data for a specified camera over a time range.

    :param camera_id: The unique identifier of the camera.
    :param start_time: Start time for the data (Unix timestamp in seconds).
    :param end_time: End time for the data (Unix timestamp in seconds).
    :param interval: Time interval (e.g., 15_minutes, 1_hour, etc.).
    :param type: Data type; for example, "person".
    :return: A JSON object with occupancy trends data.
    """
    params = {
        "camera_id": camera_id,
        "start_time": start_time,
        "end_time": end_time,
        "interval": interval,
        "type": type
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
def set_cloud_backup_settings(camera_id: str, days_to_preserve: str,
                              enabled: bool, time_to_preserve: str,
                              upload_timeslot: str, video_quality: str,
                              video_to_upload: str) -> dict:
    """
    Updates the cloud backup settings for a specified camera.

    :param camera_id: The unique identifier of the camera.
    :param days_to_preserve: Delimited list of booleans for each day.
    :param enabled: True if cloud backup is enabled; otherwise, False.
    :param time_to_preserve: Time slot for backup (start_time, end_time in seconds to midnight).
    :param upload_timeslot: Scheduled time slot for footage upload.
    :param video_quality: Video quality (STANDARD_QUALITY or HIGH_QUALITY).
    :param video_to_upload: Video type (MOTION or ALL). If MOTION, video_quality is set to HIGH_QUALITY.
    :return: The new cloud backup configuration.
    """
    if video_to_upload == "MOTION":
        video_quality = "HIGH_QUALITY"
    enabled_int = 1 if enabled else 0
    payload = {
        "camera_id": camera_id,
        "days_to_preserve": days_to_preserve,
        "enabled": enabled_int,
        "time_to_preserve": time_to_preserve,
        "upload_timeslot": upload_timeslot,
        "video_quality": video_quality,
        "video_to_upload": video_to_upload
    }
    url = f"{CLOUD_BACKUP_ENDPOINT}"
    return post_request(url, payload)


@typechecked
def get_camera_data(page_size: Optional[int] = None, page_token: Optional[str] = None) -> dict:
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


@typechecked
def get_footage_link(camera_id: str, timestamp: int = None) -> dict:
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
def get_latest_thumbnail(camera_id: str, resolution: str = None) -> bytes:
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
def get_thumbnail_link(camera_id: str, timestamp: int = None,
                       expiry: int = None) -> dict:
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


@typechecked
def get_all_poi() -> dict:
    """
    Returns details for all Persons of Interest in the organization.

    :return: A dictionary containing POI objects.
    """
    url = f"{POI_ENDPOINT}"
    return get_request(url)


@typechecked
def create_poi(base64_image: str, label: str) -> dict:
    """
    Creates a Person of Interest using a base64-encoded image and label.

    :param base64_image: A base64-encoded string representing the profile image.
    :param label: A descriptive label for the POI.
    :return: The newly created POI object.
    """
    payload = {"base64_image": base64_image, "label": label}
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
