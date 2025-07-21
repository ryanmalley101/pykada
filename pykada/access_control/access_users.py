from typeguard import typechecked
from typing import Optional
from pykada.endpoints import *
from pykada.helpers import check_user_external_id, remove_null_fields
from pykada.verkada_requests import *


@typechecked
def get_all_access_users() -> dict:
    """
    Retrieve all access user information.

    :return: JSON response containing access user information.
    :rtype: dict
    """
    return get_request(ACCESS_ALL_USERS_ENDPOINT)

@typechecked
def get_access_user(user_id: Optional[str] = None,
                    external_id: Optional[str] = None) -> dict:
    """
    Retrieve access user by either user_id or external_id.
    Exactly one of user_id or external_id must be provided.

    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :return: JSON response containing access user details.
    :rtype: dict
    :raises ValueError: If not exactly one of user_id or external_id is provided.
    """
    params = check_user_external_id(user_id, external_id)
    return get_request(ACCESS_USER_ENDPOINT, params=params)

@typechecked
def activate_ble_for_access_user(user_id: Optional[str] = None,
                                 external_id: Optional[str] = None) -> dict:
    """
    Activate BLE for an access user. Exactly one of user_id or external_id must be provided.

    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :return: JSON response after activating BLE for the access user.
    :rtype: dict
    :raises ValueError: If not exactly one of user_id or external_id is provided.
    """
    params = check_user_external_id(user_id, external_id)
    return put_request(ACCESS_BLE_ACTIVATE_ENDPOINT, params=params)

@typechecked
def deactivate_ble_for_access_user(user_id: Optional[str] = None,
                                   external_id: Optional[str] = None) -> dict:
    """
    Deactivate BLE for an access user. Exactly one of user_id or external_id must be provided.

    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :return: JSON response after deactivating BLE for the access user.
    :rtype: dict
    :raises ValueError: If not exactly one of user_id or external_id is provided.
    """
    params = check_user_external_id(user_id, external_id)
    return put_request(ACCESS_BLE_DEACTIVATE_ENDPOINT, params=params)

@typechecked
def set_end_date_for_user(end_date: str,
                          user_id: Optional[str] = None,
                          external_id: Optional[str] = None) -> dict:
    """
    Set the end date for an access user. Exactly one of user_id or external_id must be provided.

    :param end_date: The end date in string format.
    :type end_date: str
    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :return: JSON response after setting the end date for the access user.
    :rtype: dict
    :raises ValueError: If end_date is an empty string or if not exactly one of user_id or external_id is provided.
    """
    if not end_date:
        raise ValueError("end_date must be a non-empty string")
    params = check_user_external_id(user_id, external_id)
    payload = {"end_date": end_date}
    params = remove_null_fields(params)
    return put_request(ACCESS_END_DATE_ENDPOINT, params=params, payload=payload)

@typechecked
def remove_entry_code_for_user(user_id: Optional[str] = None,
                               external_id: Optional[str] = None) -> dict:
    """
    Remove the entry code for an access user.

    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :return: JSON response after removing the entry code for the access user.
    :rtype: dict
    :raises ValueError: If not exactly one of user_id or external_id is provided.
    """
    params = check_user_external_id(user_id, external_id)
    return delete_request(ACCESS_ENTRY_CODE_ENDPOINT, params=params)

@typechecked
def set_entry_code_for_user(entry_code: str,
                            user_id: Optional[str] = None,
                            external_id: Optional[str] = None,
                            override: Optional[bool] = False) -> dict:
    """
    Set the entry code for an access user.

    :param entry_code: The entry code to set.
    :type entry_code: str
    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :param override: Whether to override an existing entry code.
    :type override: Optional[bool]
    :return: JSON response after setting the entry code.
    :rtype: dict
    """
    params = check_user_external_id(user_id, external_id)
    params["override"] = override
    params = remove_null_fields(params)
    payload = {"entry_code": entry_code}
    return put_request(ACCESS_ENTRY_CODE_ENDPOINT, params=params, payload=payload)

@typechecked
def send_pass_app_invite_for_user(user_id: Optional[str] = None,
                                  external_id: Optional[str] = None) -> dict:
    """
    Send a Pass App invite for an access user.

    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :return: JSON response after sending the invite.
    :rtype: dict
    """
    params = check_user_external_id(user_id, external_id)
    return post_request(ACCESS_PASS_INVITE_ENDPOINT, params=params)

@typechecked
def delete_profile_photo(user_id: Optional[str] = None,
                         external_id: Optional[str] = None) -> dict:
    """
    Delete the profile photo for an access user.

    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :return: JSON response after deleting the profile photo.
    :rtype: dict
    """
    params = check_user_external_id(user_id, external_id)
    return delete_request(ACCESS_PROFILE_PHOTO_ENDPOINT, params=params)

@typechecked
def get_profile_photo(user_id: Optional[str] = None,
                      external_id: Optional[str] = None,
                      original: Optional[bool] = False) -> bytes:
    """
    Retrieve the profile photo for an access user.

    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :param original: Whether to retrieve the original image.
    :type original: Optional[bool]
    :return: JSON response containing the profile photo information.
    :rtype: bytes
    """
    params = check_user_external_id(user_id, external_id)
    params["original"] = original
    return get_request_image(ACCESS_PROFILE_PHOTO_ENDPOINT, params=params)

@typechecked
def upload_profile_photo(photo_path: str,
                         user_id: Optional[str] = None,
                         external_id: Optional[str] = None,
                         overwrite: Optional[bool] = False) -> dict:
    """
    Upload a profile photo for an access user.

    :param photo_path: Path to the image file.
    :type photo_path: str
    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :param overwrite: Whether to overwrite an existing profile photo.
    :type overwrite: Optional[bool]
    :return: JSON response after uploading the profile photo.
    :rtype: dict
    """
    params = check_user_external_id(user_id, external_id)
    params["overwrite"] = overwrite

    headers = {
        # do not include content-type as requests won't add a boundary if it is set
        "accept": "application/json",
        # "content-type": "multipart/form-data",
        "x-verkada-auth": get_api_token()
    }

    files = {
        'file': open(photo_path, 'rb'),
    }
    #
    # with open(photo_path, "rb") as image_file:
    #     encoded_image = base64.b64encode(image_file.read()).decode('utf_8')
    # payload = {"file": encoded_image}
    return put_request(ACCESS_PROFILE_PHOTO_ENDPOINT, headers=headers, params=params, files=files)

@typechecked
def activate_remote_unlock_for_user(user_id: Optional[str] = None,
                                    external_id: Optional[str] = None) -> dict:
    """
    Activate remote unlock for an access user.

    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :return: JSON response after activating remote unlock.
    :rtype: dict
    """
    params = check_user_external_id(user_id, external_id)
    return put_request(ACCESS_REMOTE_UNLOCK_ACTIVATE_ENDPOINT, params=params)

@typechecked
def deactivate_remote_unlock_for_user(user_id: Optional[str] = None,
                                      external_id: Optional[str] = None) -> dict:
    """
    Deactivate remote unlock for an access user.

    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :return: JSON response after deactivating remote unlock.
    :rtype: dict
    """
    params = check_user_external_id(user_id, external_id)
    return put_request(ACCESS_REMOTE_UNLOCK_DEACTIVATE_ENDPOINT, params=params)

@typechecked
def set_start_date_for_user(start_date: str,
                            user_id: Optional[str] = None,
                            external_id: Optional[str] = None) -> dict:
    """
    Set the start date for an access user.

    :param start_date: The start date in string format.
    :type start_date: str
    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :return: JSON response after setting the start date.
    :rtype: dict
    :raises ValueError: If start_date is an empty string.
    """
    params = check_user_external_id(user_id, external_id)
    if not start_date:
        raise ValueError("start_date must be a non-empty string")
    payload = {"start_date": start_date}
    return put_request(ACCESS_START_DATE_ENDPOINT, params=params, payload=payload)
