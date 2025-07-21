from typeguard import typechecked
from typing import Optional, Dict, Any

from pykada.endpoints import *
from pykada.helpers import remove_null_fields, check_user_external_id, \
    require_non_empty_str
from pykada.verkada_requests import *

@typechecked
def delete_access_card(card_id: str, user_id: Optional[str] = None, external_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Delete an access card for a user.

    :param card_id: The unique identifier for the access card.
    :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
    :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
    :return: JSON response containing the result of the deletion.
    :raises ValueError: If card_id is an empty string.
    """
    if not card_id:
        raise ValueError("card_id must be a non-empty string")

    params = check_user_external_id(user_id, external_id)
    params["card_id"] = card_id

    return delete_request(ACCESS_CARD_ENDPOINT, params=params)


@typechecked
def add_card_to_user(user_id: Optional[str] = None,
                     external_id: Optional[str] = None,
                     active: Optional[bool] = False,
                     card_number: Optional[str] = None,
                     card_number_hex: Optional[str] = None,
                     card_number_base36: Optional[str] = None,
                     facility_code: str = "",
                     card_type: str = "") -> Dict[str, Any]:
    """
    Add a card to a user.

    Creates and adds an access card for a specified user (by user_id or external_id)
    and organization. The card object is passed in the request body as JSON. This
    request requires a facility code and exactly one of the following: card_number,
    card_number_hex, or card_number_base36. The 'active' field defaults to False.

    :param user_id: The internal user identifier.
    :param external_id: The external user identifier.
    :param active: Boolean flag indicating if the credential should be active. Defaults to False.
    :param card_number: The card number used to grant or deny access.
    :param card_number_hex: The card number in hexadecimal format.
    :param card_number_base36: The card number in base36 format.
    :param facility_code: The facility code used to grant or deny access.
    :param card_type: The type of card (e.g., Standard 26-bit Wiegand, HID 37-bit, etc.).
    :return: JSON response containing the created credential information.
    :raises ValueError: If not exactly one of card_number, card_number_hex, or card_number_base36 is provided.
    """
    params = check_user_external_id(user_id, external_id)

    # Ensure exactly one card number format is provided.
    card_number_options = [card_number, card_number_hex, card_number_base36]
    if sum(x is not None for x in card_number_options) != 1:
        raise ValueError("Exactly one of card_number, card_number_hex, or card_number_base36 must be provided.")

    payload = {
        "active": active,
        "facility_code": facility_code,
        "type": card_type,
    }

    if card_number is not None:
        payload["card_number"] = card_number
    elif card_number_hex is not None:
        payload["card_number_hex"] = card_number_hex
    elif card_number_base36 is not None:
        payload["card_number_base36"] = card_number_base36

    return post_request(ACCESS_CARD_ENDPOINT, params=params, payload=payload)


@typechecked
def activate_access_card(card_id: str, user_id: Optional[str] = None, external_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Activate an access card for a user.

    :param card_id: The unique identifier for the access card.
    :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
    :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
    :return: JSON response containing the result of the activation.
    :raises ValueError: If card_id is an empty string.
    """
    if not card_id:
        raise ValueError("card_id must be a non-empty string")

    params = check_user_external_id(user_id, external_id)
    params["card_id"] = card_id

    return put_request(ACCESS_CARD_ACTIVATE_ENDPOINT, params=params)


@typechecked
def deactivate_access_card(card_id: str, user_id: Optional[str] = None, external_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Deactivate an access card for a user.

    :param card_id: The unique identifier for the access card.
    :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
    :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
    :return: JSON response containing the result of the deactivation.
    :raises ValueError: If card_id is an empty string.
    """
    if not card_id:
        raise ValueError("card_id must be a non-empty string")

    params = check_user_external_id(user_id, external_id)
    params["card_id"] = card_id

    return put_request(ACCESS_CARD_DEACTIVATE_ENDPOINT, params=params)


@typechecked
def delete_license_plate_from_user(license_plate_number: str, user_id: Optional[str] = None, external_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Delete a license plate from a user.

    :param license_plate_number: The license plate number to be deleted.
    :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
    :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
    :return: JSON response containing the result of the deletion.
    :raises ValueError: If license_plate_number is an empty string.
    """
    if not license_plate_number:
        raise ValueError("license_plate_number must be a non-empty string")

    params = check_user_external_id(user_id, external_id)
    params["license_plate_number"] = license_plate_number

    return delete_request(ACCESS_LICENSE_PLATE_ENDPOINT, params=params)


@typechecked
def add_license_plate_to_user(license_plate_number: str, active: Optional[bool] = False, name: Optional[str] = None,
                              user_id: Optional[str] = None, external_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Add a license plate to a user.

    :param license_plate_number: The license plate number to be added.
    :param active: Boolean flag indicating if the license plate should be active. Defaults to False.
    :param name: Optional name associated with the license plate.
    :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
    :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
    :return: JSON response containing the added license plate details.
    :raises ValueError: If license_plate_number is an empty string.
    """
    if not license_plate_number:
        raise ValueError("license_plate_number must be a non-empty string")

    params = check_user_external_id(user_id, external_id)

    payload = {
        "license_plate_number": license_plate_number,
        "active": active,
        "name": name
    }

    payload = remove_null_fields(payload)

    return post_request(ACCESS_LICENSE_PLATE_ENDPOINT, params=params, payload=payload)


@typechecked
def activate_license_plate(license_plate_number: str, user_id: Optional[str] = None, external_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Activate a license plate for a user.

    :param license_plate_number: The license plate number to be activated.
    :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
    :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
    :return: JSON response containing the result of the activation.
    :raises ValueError: If license_plate_number is an empty string.
    """
    if not license_plate_number:
        raise ValueError("license_plate_number must be a non-empty string")

    params = check_user_external_id(user_id, external_id)
    params["license_plate_number"] = license_plate_number

    return put_request(ACCESS_LICENSE_PLATE_ACTIVATE_ENDPOINT, params=params)


@typechecked
def deactivate_license_plate(license_plate_number: str, user_id: Optional[str] = None, external_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Deactivate a license plate for a user.

    :param license_plate_number: The license plate number to be deactivated.
    :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
    :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
    :return: JSON response containing the result of the deactivation.
    :raises ValueError: If license_plate_number is an empty string.
    """
    if not license_plate_number:
        raise ValueError("license_plate_number must be a non-empty string")

    params = check_user_external_id(user_id, external_id)
    params["license_plate_number"] = license_plate_number

    return put_request(ACCESS_LICENSE_PLATE_DEACTIVATE_ENDPOINT, params=params)


@typechecked
def delete_mfa_code_from_user(code: str, user_id: Optional[str] = None, external_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Delete an MFA code from a user.

    :param code: The MFA code to be deleted.
    :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
    :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
    :return: JSON response containing the result of the deletion.
    :raises ValueError: If code is an empty string.
    """
    if not code:
        raise ValueError("code must be a non-empty string")

    params = check_user_external_id(user_id, external_id)
    params["code"] = code

    return delete_request(ACCESS_MFA_CODE_ENDPOINT, params=params)


@typechecked
def add_mfa_code_to_user(code: str, user_id: Optional[str] = None, external_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Add an MFA code to a user.

    :param code: The MFA code to be added.
    :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
    :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
    :return: JSON response containing the added MFA code details.
    :raises ValueError: If code is an empty string.
    """

    require_non_empty_str(code, "code")

    if not code:
        raise ValueError("code must be a non-empty string")

    params = check_user_external_id(user_id, external_id)

    payload = {
        "code": code
    }

    return post_request(ACCESS_MFA_CODE_ENDPOINT, params=params, payload=payload)
