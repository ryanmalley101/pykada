import time
from typing import Optional, Dict, Any, List

import numpy as np
from typeguard import typechecked

from pykada.api_tokens import get_default_api_token, VerkadaTokenManager
from pykada.endpoints import ACCESS_CARD_ENDPOINT, \
    ACCESS_CARD_ACTIVATE_ENDPOINT, ACCESS_CARD_DEACTIVATE_ENDPOINT, \
    ACCESS_LICENSE_PLATE_ENDPOINT, ACCESS_LICENSE_PLATE_ACTIVATE_ENDPOINT, \
    ACCESS_LICENSE_PLATE_DEACTIVATE_ENDPOINT, ACCESS_MFA_CODE_ENDPOINT, \
    ACCESS_DOOR_EXCEPTIONS_ENDPOINT, ACCESS_ADMIN_UNLOCK_ENDPOINT, \
    ACCESS_USER_UNLOCK_ENDPOINT, ACCESS_DOORS_ENDPOINT, ACCESS_EVENTS_ENDPOINT, \
    ACCESS_GROUPS_ENDPOINT, ACCESS_GROUP_ENDPOINT, ACCESS_GROUP_USER_ENDPOINT, \
    ACCESS_LEVEL_ENDPOINT, ACCESS_ALL_USERS_ENDPOINT, ACCESS_USER_ENDPOINT, \
    ACCESS_BLE_ACTIVATE_ENDPOINT, ACCESS_BLE_DEACTIVATE_ENDPOINT, \
    ACCESS_END_DATE_ENDPOINT, ACCESS_ENTRY_CODE_ENDPOINT, \
    ACCESS_PASS_INVITE_ENDPOINT, ACCESS_PROFILE_PHOTO_ENDPOINT, \
    ACCESS_REMOTE_UNLOCK_ACTIVATE_ENDPOINT, \
    ACCESS_REMOTE_UNLOCK_DEACTIVATE_ENDPOINT, ACCESS_START_DATE_ENDPOINT
from pykada.helpers import check_user_external_id, remove_null_fields, \
    require_non_empty_str, is_valid_date, is_valid_time
from pykada.enums import WEEKDAY_ENUM, FREQUENCY_ENUM, DOOR_STATUS_ENUM, \
    VALID_ACCESS_EVENT_TYPES_ENUM
from pykada.verkada_client import BaseClient
from pykada.verkada_requests import VerkadaRequestManager

class AccessControlClient(BaseClient):
    """
    Client for interacting with Verkada's Access Control API.
    """
    @typechecked
    def __init__(self,
                 api_key: Optional[str] = None,
                 token_manager: Optional[VerkadaTokenManager] = None,
                 request_manager: Optional[VerkadaRequestManager] = None):
        """
        Initializes the AccessControlClient.

        :param api_key: Optional API key for authentication. If not provided, it will be fetched from environment variables.
        :param token_manager: Optional custom VerkadaTokenManager instance.
        :param request_manager: Optional custom VerkadaRequestManager instance.
        """
        super().__init__(api_key, token_manager, request_manager)


    @typechecked
    def delete_access_card(self, card_id: str, user_id: Optional[str] = None, external_id: Optional[str] = None) -> Dict[str, Any]:
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

        return self.request_manager.delete(ACCESS_CARD_ENDPOINT, params=params)


    @typechecked
    def add_card_to_user(self, user_id: Optional[str] = None,
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

        return self.request_manager.post(ACCESS_CARD_ENDPOINT, params=params, payload=payload)


    @typechecked
    def activate_access_card(self, card_id: str, user_id: Optional[str] = None, external_id: Optional[str] = None) -> Dict[str, Any]:
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

        return self.request_manager.put(ACCESS_CARD_ACTIVATE_ENDPOINT, params=params)


    @typechecked
    def deactivate_access_card(self, card_id: str, user_id: Optional[str] = None, external_id: Optional[str] = None) -> Dict[str, Any]:
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

        return self.request_manager.put(ACCESS_CARD_DEACTIVATE_ENDPOINT, params=params)


    @typechecked
    def delete_license_plate_from_user(self, license_plate_number: str, user_id: Optional[str] = None, external_id: Optional[str] = None) -> Dict[str, Any]:
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

        return self.request_manager.delete(ACCESS_LICENSE_PLATE_ENDPOINT, params=params)


    @typechecked
    def add_license_plate_to_user(self,
                                  license_plate_number: str,
                                  active: Optional[bool] = False,
                                  name: Optional[str] = None,
                                  user_id: Optional[str] = None,
                                  external_id: Optional[str] = None) \
            -> Dict[str, Any]:
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

        return self.request_manager.post(ACCESS_LICENSE_PLATE_ENDPOINT, params=params, payload=payload)


    @typechecked
    def activate_license_plate(self,
                               license_plate_number: str,
                               user_id: Optional[str] = None,
                               external_id: Optional[str] = None) \
            -> Dict[str, Any]:
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

        return self.request_manager.put(ACCESS_LICENSE_PLATE_ACTIVATE_ENDPOINT,
                                        params=params)


    @typechecked
    def deactivate_license_plate(self,
                                 license_plate_number: str,
                                 user_id: Optional[str] = None,
                                 external_id: Optional[str] = None) ->\
            Dict[str, Any]:
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

        return self.request_manager.put(
            ACCESS_LICENSE_PLATE_DEACTIVATE_ENDPOINT,
            params=params)


    @typechecked
    def delete_mfa_code_from_user(self,
                                  code: str,
                                  user_id: Optional[str] = None,
                                  external_id: Optional[str] = None) ->\
            Dict[str, Any]:
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

        return self.request_manager.delete(ACCESS_MFA_CODE_ENDPOINT, params=params)


    @typechecked
    def add_mfa_code_to_user(self,
                             code: str,
                             user_id: Optional[str] = None,
                             external_id: Optional[str] = None)\
            -> Dict[str, Any]:
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

        return self.request_manager.post(ACCESS_MFA_CODE_ENDPOINT,
                                         params=params,
                                         payload=payload)

    @typechecked
    def get_all_door_exception_calendars(self,
                                         last_updated_at: Optional[int] = None)\
            -> Dict[str, Any]:
        """
        Retrieve all available door exception calendars.

        :param last_updated_at: Optional timestamp (Unix seconds) to filter calendars updated after this time.
        :return: JSON response containing all available door exception calendars.
        """
        params = {"last_updated_at": last_updated_at} \
            if last_updated_at is not None else {}
        return self.request_manager.get(ACCESS_DOOR_EXCEPTIONS_ENDPOINT,
                                        params=params)


    @typechecked
    def get_door_exception_calendar(self, calendar_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific door exception calendar.

        :param calendar_id: The unique identifier for the door exception calendar.
        :return: JSON response containing the door exception calendar details.
        :raises ValueError: If calendar_id is an empty string.
        """
        require_non_empty_str(calendar_id, "calendar_id")
        params = {'calendar_id': calendar_id}
        return self.request_manager.get(
            ACCESS_DOOR_EXCEPTIONS_ENDPOINT,
            params=params)


    @typechecked
    def create_door_exception_calendar(self,
                                       doors: List[str],
                                       exceptions: List[Dict[str, Any]],
                                       name: str) -> Dict[str, Any]:
        """
        Create a new door exception calendar.

        :param doors: A non-empty list of door IDs.
        :param exceptions: A non-empty list of door exception objects.
        :param name: Name of the door exception calendar.
        :return: JSON response containing the created door exception calendar information.
        :raises ValueError: If any required field is missing or invalid.
        """
        require_non_empty_str(name, "name")
        if not doors or not all(isinstance(door, str) and door.strip() for door in doors):
            raise ValueError("doors must be a non-empty list of non-empty strings")
        for idx, door in enumerate(doors):
            require_non_empty_str(door, "door", idx)

        for exc in exceptions:
            validate_door_exception(exc)

        payload = {
            "doors": doors,
            "exceptions": exceptions,
            "name": name
        }
        return self.request_manager.post(ACCESS_DOOR_EXCEPTIONS_ENDPOINT, payload=payload)


    @typechecked
    def update_door_exception_calendar(self,
                                       doors: List[str],
                                       exceptions: List[Dict[str, Any]],
                                       name: str,
                                       calendar_id: str) -> Dict[str, Any]:
        """
        Update an existing door exception calendar.

        :param doors: A non-empty list of door IDs.
        :param exceptions: A non-empty list of door exception objects.
        :param name: Updated name of the door exception calendar.
        :param calendar_id: The unique identifier of the calendar to update.
        :return: JSON response containing the updated door exception calendar information.
        :raises ValueError: If any required field is missing or invalid.
        """
        require_non_empty_str(name, "name")
        if not doors or not all(isinstance(door, str) and door.strip() for door in doors):
            raise ValueError("doors must be a non-empty list of non-empty strings")
        for idx, door in enumerate(doors):
            require_non_empty_str(door, "door", idx)

        for exc in exceptions:
            validate_door_exception(exc)

        payload = {
            "doors": doors,
            "exceptions": exceptions,
            "name": name
        }
        url = f"{ACCESS_DOOR_EXCEPTIONS_ENDPOINT}/{calendar_id}"

        return self.request_manager.put(url, payload=payload)


    @typechecked
    def delete_door_exception_calendar(self, calendar_id: str) -> Dict[str, Any]:
        """
        Delete a door exception calendar.

        :param calendar_id: The unique identifier for the door exception calendar to delete.
        :return: JSON response confirming deletion.
        :raises ValueError: If calendar_id is an empty string.
        """
        require_non_empty_str(calendar_id, "calendar_id")
        url = f"{ACCESS_DOOR_EXCEPTIONS_ENDPOINT}/{calendar_id}"
        return self.request_manager.delete(url)


    @typechecked
    def get_exception_on_door_exception_calendar(self, calendar_id: str,
                                                 exception_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific exception from a door exception calendar.

        :param calendar_id: The unique identifier for the door exception calendar.
        :param exception_id: The unique identifier for the exception.
        :return: JSON response containing the exception details.
        :raises ValueError: If calendar_id or exception_id is an empty string.
        """
        require_non_empty_str(calendar_id, "calendar_id")
        require_non_empty_str(exception_id, "exception_id")
        url = f"{ACCESS_DOOR_EXCEPTIONS_ENDPOINT}/{calendar_id}/exception/{exception_id}"
        return self.request_manager.get(url)


    @typechecked
    def add_exception_to_door_exception_calendar(
        self,
        calendar_id: str,
        exception: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add an Exception to a Door Exception Calendar.

        Adds a new Exception to the Door Exception Calendar identified by `calendar_id` using the details provided in the exception object.
        The exception object must follow the expected schema and will be validated using the `validate_door_exception` function.

        :param calendar_id: The unique identifier for the door exception calendar.
        :param exception: A dictionary representing the new exception details.
        :return: JSON response containing the created exception information.
        :raises ValueError: If calendar_id is an empty string or if the exception object fails validation.
        """
        require_non_empty_str(calendar_id, "calendar_id")
        validate_door_exception(exception)

        url = f"{ACCESS_DOOR_EXCEPTIONS_ENDPOINT}/{calendar_id}/exception"
        return self.request_manager.post(url, payload=exception)


    @typechecked
    def update_exception_on_door_exception_calendar(
            self,
            calendar_id: str,
            exception_id: str,
            exception: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an Exception on a Door Exception Calendar.

        Updates the Exception identified by `exception_id` on the Door Exception Calendar
        identified by `calendar_id` using the new exception details provided as a single object.

        The provided exception object must follow the expected schema, which is validated using
        the `validate_door_exception` function. For example, the object must include:
          - date (in YYYY-MM-DD format)
          - door_status (one of the allowed values)
          - For non-all-day exceptions, valid start_time and end_time (in HH:MM format)
          - If all_day_default is True, door_status must be "access_controlled", and start_time/end_time
            should be omitted or defaulted to "00:00" and "23:59", respectively.
          - Optional fields such as first_person_in, double_badge, and their corresponding group IDs,
            as well as an optional recurrence_rule object.

        :param calendar_id: The unique identifier for the door exception calendar.
        :param exception_id: The unique identifier for the exception to update.
        :param exception: A dictionary representing the new exception details.
        :return: JSON response containing the updated exception information.
        :raises ValueError: If any required parameter is missing or if the exception object fails validation.
        """
        require_non_empty_str(calendar_id, "calendar_id")
        require_non_empty_str(exception_id, "exception_id")
        validate_door_exception(exception)

        url = f"{ACCESS_DOOR_EXCEPTIONS_ENDPOINT}/{calendar_id}/exception/{exception_id}"
        return self.request_manager.put(url, payload=exception)


    @typechecked
    def delete_exception_on_door_exception_calendar(self, calendar_id: str, exception_id: str) -> Dict[str, Any]:
        """
        Delete an exception from a door exception calendar.

        :param calendar_id: The unique identifier for the door exception calendar.
        :param exception_id: The unique identifier for the exception to delete.
        :return: JSON response confirming deletion of the exception.
        :raises ValueError: If calendar_id or exception_id is an empty string.
        """
        require_non_empty_str(calendar_id, "calendar_id")
        require_non_empty_str(exception_id, "exception_id")
        url = f"{ACCESS_DOOR_EXCEPTIONS_ENDPOINT}/{calendar_id}/exception/{exception_id}"
        return self.request_manager.delete(url)


    @typechecked
    def unlock_door_as_admin(self, door_id: str) -> Dict[str, Any]:
        """
        Unlock a door as an administrator.

        This function sends a request to unlock the specified door without requiring user identification.

        :param door_id: The unique identifier for the door.
        :return: JSON response containing the result of the unlock operation.
        :raises ValueError: If door_id is an empty string.
        """
        if not door_id:
            raise ValueError("door_id must be a non-empty string")

        payload = {"door_id": door_id}
        return self.request_manager.post(ACCESS_ADMIN_UNLOCK_ENDPOINT, payload=payload)


    @typechecked
    def unlock_door_as_user(self, door_id: str, user_id: Optional[str] = None,
                            external_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Unlock a door as a user.

        This function sends a request to unlock the specified door, using either the internal user_id or the external_id.

        :param door_id: The unique identifier for the door.
        :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
        :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
        :return: JSON response containing the result of the unlock operation.
        :raises ValueError: If door_id is an empty string.
        """
        if not door_id:
            raise ValueError("door_id must be a non-empty string")

        payload = check_user_external_id(user_id, external_id)
        payload["door_id"] = door_id

        return self.request_manager.post(ACCESS_USER_UNLOCK_ENDPOINT, payload=payload)


    @typechecked
    def get_doors(self,
                  door_id_list: Optional[List[Any]] = None,
                  site_id_list: Optional[List[Any]] = None) -> Dict[str, Any]:
        """
        Retrieve door information.

        This function sends a GET request to retrieve details for doors based on provided door IDs and/or site IDs.

        :param door_id_list: A list of door IDs. If provided, these will be joined into a comma-separated string.
        :param site_id_list: A list of site IDs. If provided, these will be joined into a comma-separated string.
        :return: JSON response containing door information.
        """
        door_ids = ",".join(map(str, door_id_list)) if door_id_list else None
        site_ids = ",".join(map(str, site_id_list)) if site_id_list else None

        params = {"door_ids": door_ids, "site_ids": site_ids}
        return self.request_manager.get(ACCESS_DOORS_ENDPOINT, params=params)


    @typechecked
    def get_access_events(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        page_token: Optional[str] = None,
        page_size: Optional[int] = 100,
        event_type: Optional[List[str]] = None,
        site_id: Optional[str] = None,
        device_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve access events based on various filters.

        :param start_time: The start of the time range for requested events, as a Unix timestamp in seconds.
                           Defaults to one hour ago from the current time if not provided.
        :param end_time: The end of the time range for requested events, as a Unix timestamp in seconds.
                         Defaults to the current time if not provided.
        :param page_token: The pagination token used to fetch the next page of results.
        :param page_size: The number of items returned in a single response (0 to 200). Defaults to 100.
        :param event_type: One or multiple comma-separated event type values.
        :param site_id: One or multiple comma-separated site identifiers.
        :param device_id: One or multiple comma-separated device identifiers.
        :param user_id: One or multiple comma-separated user identifiers.
        :return: JSON response containing access events matching the provided filters.
        :raises ValueError: If page_size is not between 0 and 200.
        """
        current_time = int(time.time())
        if start_time is None:
            start_time = current_time - 3600  # default to one hour ago
        if end_time is None:
            end_time = current_time

        if event_type:
            invalid_events = np.setdiff1d(event_type, list(VALID_ACCESS_EVENT_TYPES_ENUM.values()))
            if len(invalid_events) > 0:
                raise ValueError(f"Event types {invalid_events} are not in the "
                                 f"list of valid event types: "
                                 f"{list(VALID_ACCESS_EVENT_TYPES_ENUM.values())}")

        if page_size is not None and (page_size < 0 or page_size > 200):
            raise ValueError("page_size must be between 0 and 200")

        params = {
            "start_time": start_time,
            "end_time": end_time,
            "page_token": page_token,
            "page_size": page_size,
            "event_type": ",".join(map(str, event_type)) if event_type else None,
            "site_id": site_id,
            "device_id": device_id,
            "user_id": user_id,
        }
        # Remove keys with None values.
        params = {k: v for k, v in params.items() if v is not None}

        return self.request_manager.get(ACCESS_EVENTS_ENDPOINT, params=params)


    @typechecked
    def get_access_groups(self) -> dict:
        """
        Retrieve all access groups.

        :return: JSON response containing a list of access groups.
        :rtype: dict
        """
        return self.request_manager.get(ACCESS_GROUPS_ENDPOINT)


    @typechecked
    def delete_access_group(self, group_id: str) -> dict:
        """
        Delete an access group.

        :param group_id: The unique identifier for the access group.
        :type group_id: str
        :return: JSON response after deleting the access group.
        :rtype: dict
        :raises ValueError: If group_id is an empty string.
        """
        if not group_id:
            raise ValueError("group_id must be a non-empty string")
        params = {"group_id": group_id}
        return self.request_manager.delete(ACCESS_GROUP_ENDPOINT, params=params)


    @typechecked
    def get_access_group(self, group_id: str) -> dict:
        """
        Retrieve a specific access group by its ID.

        :param group_id: The unique identifier for the access group.
        :type group_id: str
        :return: JSON response containing the access group details.
        :rtype: dict
        :raises ValueError: If group_id is an empty string.
        """
        if not group_id:
            raise ValueError("group_id must be a non-empty string")
        params = {"group_id": group_id}
        return self.request_manager.get(ACCESS_GROUP_ENDPOINT, params=params)


    @typechecked
    def create_access_group(self, name: str) -> dict:
        """
        Create a new access group with the specified name.

        :param name: The name for the new access group.
        :type name: str
        :return: JSON response containing details of the created access group.
        :rtype: dict
        :raises ValueError: If name is an empty string.
        """

        require_non_empty_str(name, 'name')

        payload = {"name": name}

        return self.request_manager.post(ACCESS_GROUP_ENDPOINT, payload=payload)


    @typechecked
    def add_user_to_access_group(self, group_id: str, external_id: Optional[str] = None,
                                 user_id: Optional[str] = None) -> dict:
        """
        Add a user to an access group. Exactly one of user_id or external_id must be provided.

        :param group_id: The unique identifier for the access group.
        :type group_id: str
        :param external_id: The external identifier for the user.
        :type external_id: str, optional
        :param user_id: The internal user identifier.
        :type user_id: str, optional
        :return: JSON response after adding the user to the access group.
        :rtype: dict
        :raises ValueError: If group_id is empty, or if not exactly one of user_id or external_id is provided.
        """
        if not group_id:
            raise ValueError("group_id must be a non-empty string")
        if (user_id is None and external_id is None) or (
                user_id is not None and external_id is not None):
            raise ValueError(
                "Exactly one of user_id or external_id must be provided, not both or neither.")

        params = {"group_id": group_id}
        payload = {"external_id": external_id, "user_id": user_id}
        # Remove keys with None values from payload.
        payload = remove_null_fields(payload)
        return self.request_manager.put(ACCESS_GROUP_USER_ENDPOINT, params=params,
                           payload=payload)


    @typechecked
    def remove_user_from_access_group(self,
                                      group_id: str,
                                      external_id: Optional[str] = None,
                                      user_id: Optional[str] = None) -> dict:
        """
        Remove a user from an access group. Exactly one of user_id or external_id must be provided.

        :param group_id: The unique identifier for the access group.
        :param external_id: The external identifier for the user.
        :param user_id: The internal user identifier.
        :return: JSON response after removing the user from the access group.
        :raises ValueError: If group_id is empty, or if not exactly one of user_id or external_id is provided.
        """
        if not group_id:
            raise ValueError("group_id must be a non-empty string")
        if (user_id is None and external_id is None) or (
                user_id is not None and external_id is not None):
            raise ValueError(
                "Exactly one of user_id or external_id must be provided, not both or neither.")

        params = {"group_id": group_id, "external_id": external_id,
                  "user_id": user_id}
        # Remove keys with None values.
        params = remove_null_fields(params)
        return self.request_manager.put(ACCESS_GROUP_USER_ENDPOINT, params=params)


    @typechecked
    def get_all_access_levels(self) -> Dict[str, Any]:
        """
        Retrieve all available access levels.

        :return: JSON response containing all available access levels.
        """
        return self.request_manager.get(ACCESS_LEVEL_ENDPOINT)


    @typechecked
    def get_access_level(self, access_level_id: str) -> Dict[str, Any]:
        """
        Retrieve details for a specific access level.

        :param access_level_id: The unique identifier for the access level.
        :return: JSON response containing the access level details.
        :raises ValueError: If access_level_id is an empty string.
        """
        if not access_level_id:
            raise ValueError("access_level_id must be a non-empty string")

        url = f"{ACCESS_LEVEL_ENDPOINT}/{access_level_id}"
        return self.request_manager.get(url)


    @typechecked
    def create_access_level(
            self,
            name: str,
            access_groups: Optional[List[str]] = None,
            access_schedule_events: Optional[List[Dict[str, Any]]] = None,
            doors: Optional[List[str]] = None,
            sites: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new Access Level.

        To use this API, you need an API Key having permission "Door Access Management"
        for all sites listed in 'sites' for the Access Level, and "Manage via API" must
        also be enabled for all doors listed in 'doors'.

        Body Parameters:
          - access_groups (List[str], required): IDs of Access Groups granted door access via this Access Level.
          - access_schedule_events (List[Dict[str, Any]], required): List of Access Schedule Events associated with this Access Level.
                Each event object should include:
                  - access_schedule_event_id (str): Unique identifier for the Access Schedule Event.
                  - door_status (str): Door status for Access Schedule Events (defaults to "access_granted").
                  - start_time (str): Start time of the event in HH:MM format (00:00 to 23:59, with leading zeros).
                  - end_time (str): End time of the event in HH:MM format (00:00 to 23:59, with leading zeros).
                  - weekday (str): Enum for days of the week (e.g., "SU").
          - doors (List[str], required): IDs of Doors accessible under this Access Level.
          - name (str, required): Name of the Access Level.
          - sites (List[str], required): IDs of Sites containing the Doors this Access Level applies to.

        :param access_groups: List of Access Group IDs.
        :param access_schedule_events: List of Access Schedule Event objects.
        :param doors: List of Door IDs.
        :param name: Name for the Access Level.
        :param sites: List of Site IDs.
        :return: JSON response containing the created Access Level information.
        :raises ValueError: If name is an empty string.
        """
        require_non_empty_str(name, "name")

        payload = {
            "access_groups": access_groups if access_groups else [],
            "access_schedule_events": access_schedule_events if access_schedule_events else [],
            "doors": doors if doors else [],
            "name": name,
            "sites": sites if sites else [],
        }

        print(payload)
        return self.request_manager.post(ACCESS_LEVEL_ENDPOINT, payload=payload)


    @typechecked
    def update_access_level(
            self,
            access_level_id: str,
            access_groups: List[str],
            access_schedule_events: List[Dict[str, Any]],
            doors: List[str],
            name: str,
            sites: List[str]
    ) -> Dict[str, Any]:
        """
        Update an existing Access Level.

        To use this API, you need an API Key having permission "Door Access Management"
        for all sites listed in 'sites' for the Access Level, and "Manage via API" must
        also be enabled for all doors listed in 'doors'.

        :param access_level_id: The ID of the Access Level to be updated.
        :param access_groups: List of Access Group IDs.
        :param access_schedule_events: List of Access Schedule Event objects.
        :param doors: List of Door IDs.
        :param name: Name for the Access Level.
        :param sites: List of Site IDs.
        :return: JSON response containing the updated Access Level information.
        :raises ValueError: If access_level_id or name is an empty string.
        """
        if not access_level_id:
            raise ValueError("access_level_id must be a non-empty string")
        if not name:
            raise ValueError("name must be a non-empty string")

        payload = {
            "access_groups": access_groups if access_groups else [],
            "access_schedule_events": access_schedule_events if access_schedule_events else [],
            "doors": doors if doors else [],
            "name": name,
            "sites": sites if sites else [],
        }

        url = f"{ACCESS_LEVEL_ENDPOINT}/{access_level_id}"
        return self.request_manager.put(url, payload=payload)

    @typechecked
    def delete_access_level(self, access_level_id: str) -> bytes:
        """
        Delete an access level.

        :param access_level_id: The unique identifier for the access level to delete.
        :return: The raw response content confirming deletion.
        :raises ValueError: If access_level_id is an empty string.
        """
        if not access_level_id:
            raise ValueError("access_level_id must be a non-empty string")

        url = f"{ACCESS_LEVEL_ENDPOINT}/{access_level_id}"
        return self.request_manager.delete(url, return_json=False)


    @typechecked
    def add_access_schedule_event_to_access_level(
            self,
            access_level_id: str,
            start_time: str,
            end_time: str,
            weekday: str,
    ) -> Dict[str, Any]:
        """
        Add an access schedule event to a specific access level.

        The event details are provided in the payload. The door_status is fixed to "access_granted".

        :param access_level_id: The unique identifier for the access level.
        :param start_time: Start time of the event in HH:MM format (00:00 to 23:59, with leading zeros).
        :param end_time: End time of the event in HH:MM format (00:00 to 23:59, with leading zeros).
        :param weekday: Enum for days of the week (e.g., "SU").
        :return: JSON response containing the created event information.
        :raises ValueError: If access_level_id is empty, if start_time or end_time are not valid, or if weekday is invalid.
        """
        if not access_level_id:
            raise ValueError("access_level_id must be a non-empty string")
        if not is_valid_time(start_time) or not is_valid_time(end_time):
            raise ValueError(
                "start_time and end_time must be in HH:MM format (00:00 to 23:59) with required leading zeros")
        if weekday not in WEEKDAY_ENUM.values():
            raise ValueError(
                f"weekday must be one of the values in WEEKDAY_ENUM: {list(WEEKDAY_ENUM.values())}")

        payload = {
            "door_status": "access_granted",
            "start_time": start_time,
            "end_time": end_time,
            "weekday": weekday,
        }
        url = f"{ACCESS_LEVEL_ENDPOINT}/{access_level_id}/access_schedule_event"
        return self.request_manager.post(url, payload=payload)


    @typechecked
    def update_access_schedule_event_on_access_level(
            self,
            access_level_id: str,
            event_id: str,
            start_time: str,
            end_time: str,
            weekday: str,
    ) -> Dict[str, Any]:
        """
        Update an access schedule event on a specific access level.

        :param access_level_id: The unique identifier for the access level.
        :param event_id: The unique identifier for the schedule event.
        :param start_time: Updated start time in HH:MM format.
        :param end_time: Updated end time in HH:MM format.
        :param weekday: Updated weekday enum (e.g., "SU").
        :return: JSON response containing the updated event information.
        :raises ValueError: If any of the required identifiers or times are invalid.
        """
        if not access_level_id:
            raise ValueError("access_level_id must be a non-empty string")
        if not event_id:
            raise ValueError("event_id must be a non-empty string")
        if not is_valid_time(start_time) or not is_valid_time(end_time):
            raise ValueError(
                "start_time and end_time must be in HH:MM format (00:00 to 23:59) with required leading zeros")
        if weekday not in WEEKDAY_ENUM.values():
            raise ValueError(
                f"weekday must be one of the values in WEEKDAY_ENUM: {list(WEEKDAY_ENUM.values())}")

        payload = {
            "door_status": "access_granted",
            "start_time": start_time,
            "end_time": end_time,
            "weekday": weekday,
        }
        url = f"{ACCESS_LEVEL_ENDPOINT}/{access_level_id}/access_schedule_event/{event_id}"
        return self.request_manager.put(url, payload=payload)


    @typechecked
    def delete_access_schedule_event_on_access_level(
            self,
            access_level_id: str,
            event_id: str
    ) -> bytes:
        """
        Delete an access schedule event from a specific access level.

        :param access_level_id: The unique identifier for the access level.
        :param event_id: The unique identifier for the schedule event.
        :return: The raw response content confirming deletion.
        :raises ValueError: If access_level_id or event_id is an empty string.
        """
        if not access_level_id:
            raise ValueError("access_level_id must be a non-empty string")
        if not event_id:
            raise ValueError("event_id must be a non-empty string")

        url = f"{ACCESS_LEVEL_ENDPOINT}/{access_level_id}/access_schedule_event/{event_id}"
        return self.request_manager.delete(url, return_json=False)


    @typechecked
    def get_all_access_users(self) -> dict:
        """
        Retrieve all access user information.

        :return: JSON response containing access user information.
        :rtype: dict
        """
        return self.request_manager.get(ACCESS_ALL_USERS_ENDPOINT)


    @typechecked
    def get_access_user(self, user_id: Optional[str] = None,
                        external_id: Optional[str] = None) -> dict:
        """
        Retrieve access user by either user_id or external_id.
        Exactly one of user_id or external_id must be provided.

        :param user_id: The internal user identifier.
        :param external_id: The external user identifier.
        :return: JSON response containing access user details.
        :rtype: dict
        :raises ValueError: If not exactly one of user_id or external_id is provided.
        """
        params = check_user_external_id(user_id, external_id)
        return self.request_manager.get(ACCESS_USER_ENDPOINT, params=params)


    @typechecked
    def activate_ble_for_access_user(self,
                                     user_id: Optional[str] = None,
                                     external_id: Optional[str] = None) -> dict:
        """
        Activate BLE for an access user. Exactly one of user_id or external_id must be provided.

        :param user_id: The internal user identifier.
        :param external_id: The external user identifier.
        :return: JSON response after activating BLE for the access user.
        :rtype: dict
        :raises ValueError: If not exactly one of user_id or external_id is provided.
        """
        params = check_user_external_id(user_id, external_id)
        return self.request_manager.put(ACCESS_BLE_ACTIVATE_ENDPOINT, params=params)


    @typechecked
    def deactivate_ble_for_access_user(self, user_id: Optional[str] = None,
                                       external_id: Optional[str] = None) -> dict:
        """
        Deactivate BLE for an access user. Exactly one of user_id or external_id must be provided.

        :param user_id: The internal user identifier.
        :param external_id: The external user identifier.
        :return: JSON response after deactivating BLE for the access user.
        :rtype: dict
        :raises ValueError: If not exactly one of user_id or external_id is provided.
        """
        params = check_user_external_id(user_id, external_id)
        return self.request_manager.put(ACCESS_BLE_DEACTIVATE_ENDPOINT, params=params)


    @typechecked
    def set_end_date_for_user(self,
                              end_date: str,
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
        return self.request_manager.put(ACCESS_END_DATE_ENDPOINT, params=params, payload=payload)


    @typechecked
    def remove_entry_code_for_user(self, user_id: Optional[str] = None,
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
        return self.request_manager.delete(ACCESS_ENTRY_CODE_ENDPOINT, params=params)


    @typechecked
    def set_entry_code_for_user(self,
                                entry_code: str,
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
        return self.request_manager.put(ACCESS_ENTRY_CODE_ENDPOINT, params=params, payload=payload)


    @typechecked
    def send_pass_app_invite_for_user(self, user_id: Optional[str] = None,
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
        return self.request_manager.post(ACCESS_PASS_INVITE_ENDPOINT, params=params)


    @typechecked
    def delete_profile_photo(self, user_id: Optional[str] = None,
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
        return self.request_manager.delete(ACCESS_PROFILE_PHOTO_ENDPOINT, params=params)


    @typechecked
    def get_profile_photo(self, user_id: Optional[str] = None,
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
        return self.request_manager.get_image(ACCESS_PROFILE_PHOTO_ENDPOINT, params=params)


    @typechecked
    def upload_profile_photo(self,
                             photo_path: str,
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
            "x-verkada-auth": get_default_api_token()
        }

        files = {
            'file': open(photo_path, 'rb'),
        }
        #
        # with open(photo_path, "rb") as image_file:
        #     encoded_image = base64.b64encode(image_file.read()).decode('utf_8')
        # payload = {"file": encoded_image}
        return self.request_manager.put(ACCESS_PROFILE_PHOTO_ENDPOINT, headers=headers, params=params, files=files)


    @typechecked
    def activate_remote_unlock_for_user(self, user_id: Optional[str] = None,
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
        return self.request_manager.put(ACCESS_REMOTE_UNLOCK_ACTIVATE_ENDPOINT, params=params)


    @typechecked
    def deactivate_remote_unlock_for_user(self, user_id: Optional[str] = None,
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
        return self.request_manager.put(ACCESS_REMOTE_UNLOCK_DEACTIVATE_ENDPOINT, params=params)


    @typechecked
    def set_start_date_for_user(self,
                                start_date: str,
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
        return self.request_manager.put(ACCESS_START_DATE_ENDPOINT, params=params, payload=payload)


@typechecked
def activate_access_card(card_id: str, user_id: Optional[str] = None, external_id: Optional[str] = None):
    """
    Activate an access card for a user.

    :param card_id: The unique identifier for the access card.
    :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
    :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
    :return: JSON response containing the result of the activation.
    :raises ValueError: If card_id is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().activate_access_card(card_id, user_id, external_id)

@typechecked
def activate_ble_for_access_user(user_id: Optional[str] = None, external_id: Optional[str] = None):
    """
    Activate BLE for an access user. Exactly one of user_id or external_id must be provided.

    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :return: JSON response after activating BLE for the access user.
    :rtype: dict
    :raises ValueError: If not exactly one of user_id or external_id is provided.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().activate_ble_for_access_user(user_id, external_id)

@typechecked
def activate_license_plate(license_plate_number: str, user_id: Optional[str] = None, external_id: Optional[str] = None):
    """
    Activate a license plate for a user.

    :param license_plate_number: The license plate number to be activated.
    :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
    :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
    :return: JSON response containing the result of the activation.
    :raises ValueError: If license_plate_number is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().activate_license_plate(license_plate_number, user_id, external_id)

@typechecked
def activate_remote_unlock_for_user(user_id: Optional[str] = None, external_id: Optional[str] = None):
    """
    Activate remote unlock for an access user.

    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :return: JSON response after activating remote unlock.
    :rtype: dict

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().activate_remote_unlock_for_user(user_id, external_id)

@typechecked
def add_access_schedule_event_to_access_level(access_level_id: str, start_time: str, end_time: str, weekday: str):
    """
    Add an access schedule event to a specific access level.

    The event details are provided in the payload. The door_status is fixed to "access_granted".

    :param access_level_id: The unique identifier for the access level.
    :param start_time: Start time of the event in HH:MM format (00:00 to 23:59, with leading zeros).
    :param end_time: End time of the event in HH:MM format (00:00 to 23:59, with leading zeros).
    :param weekday: Enum for days of the week (e.g., "SU").
    :return: JSON response containing the created event information.
    :raises ValueError: If access_level_id is empty, if start_time or end_time are not valid, or if weekday is invalid.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().add_access_schedule_event_to_access_level(access_level_id, start_time, end_time, weekday)

@typechecked
def add_card_to_user(user_id: Optional[str] = None, external_id: Optional[str] = None, active: Optional[bool] = False, card_number: Optional[str] = None, card_number_hex: Optional[str] = None, card_number_base36: Optional[str] = None, facility_code: str = '', card_type: str = ''):
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

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().add_card_to_user(user_id, external_id, active, card_number, card_number_hex, card_number_base36, facility_code, card_type)

@typechecked
def add_exception_to_door_exception_calendar(calendar_id: str, exception: Dict[str, Any]):
    """
    Add an Exception to a Door Exception Calendar.

    Adds a new Exception to the Door Exception Calendar identified by `calendar_id` using the details provided in the exception object.
    The exception object must follow the expected schema and will be validated using the `validate_door_exception` function.

    :param calendar_id: The unique identifier for the door exception calendar.
    :param exception: A dictionary representing the new exception details.
    :return: JSON response containing the created exception information.
    :raises ValueError: If calendar_id is an empty string or if the exception object fails validation.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().add_exception_to_door_exception_calendar(calendar_id, exception)

@typechecked
def add_license_plate_to_user(license_plate_number: str, active: Optional[bool] = False, name: Optional[str] = None, user_id: Optional[str] = None, external_id: Optional[str] = None):
    """
    Add a license plate to a user.

    :param license_plate_number: The license plate number to be added.
    :param active: Boolean flag indicating if the license plate should be active. Defaults to False.
    :param name: Optional name associated with the license plate.
    :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
    :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
    :return: JSON response containing the added license plate details.
    :raises ValueError: If license_plate_number is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().add_license_plate_to_user(license_plate_number, active, name, user_id, external_id)

@typechecked
def add_mfa_code_to_user(code: str, user_id: Optional[str] = None, external_id: Optional[str] = None):
    """
    Add an MFA code to a user.

    :param code: The MFA code to be added.
    :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
    :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
    :return: JSON response containing the added MFA code details.
    :raises ValueError: If code is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().add_mfa_code_to_user(code, user_id, external_id)

@typechecked
def add_user_to_access_group(group_id: str, external_id: Optional[str] = None, user_id: Optional[str] = None):
    """
    Add a user to an access group. Exactly one of user_id or external_id must be provided.

    :param group_id: The unique identifier for the access group.
    :type group_id: str
    :param external_id: The external identifier for the user.
    :type external_id: str, optional
    :param user_id: The internal user identifier.
    :type user_id: str, optional
    :return: JSON response after adding the user to the access group.
    :rtype: dict
    :raises ValueError: If group_id is empty, or if not exactly one of user_id or external_id is provided.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().add_user_to_access_group(group_id, external_id, user_id)

@typechecked
def create_access_group(name: str):
    """
    Create a new access group with the specified name.

    :param name: The name for the new access group.
    :type name: str
    :return: JSON response containing details of the created access group.
    :rtype: dict
    :raises ValueError: If name is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().create_access_group(name)

@typechecked
def create_access_level(name: str, access_groups: Optional[List[str]] = None, access_schedule_events: Optional[List[Dict[str, Any]]] = None, doors: Optional[List[str]] = None, sites: Optional[List[str]] = None):
    """
    Create a new Access Level.

    To use this API, you need an API Key having permission "Door Access Management"
    for all sites listed in 'sites' for the Access Level, and "Manage via API" must
    also be enabled for all doors listed in 'doors'.

    Body Parameters:
      - access_groups (List[str], required): IDs of Access Groups granted door access via this Access Level.
      - access_schedule_events (List[Dict[str, Any]], required): List of Access Schedule Events associated with this Access Level.
            Each event object should include:
              - access_schedule_event_id (str): Unique identifier for the Access Schedule Event.
              - door_status (str): Door status for Access Schedule Events (defaults to "access_granted").
              - start_time (str): Start time of the event in HH:MM format (00:00 to 23:59, with leading zeros).
              - end_time (str): End time of the event in HH:MM format (00:00 to 23:59, with leading zeros).
              - weekday (str): Enum for days of the week (e.g., "SU").
      - doors (List[str], required): IDs of Doors accessible under this Access Level.
      - name (str, required): Name of the Access Level.
      - sites (List[str], required): IDs of Sites containing the Doors this Access Level applies to.

    :param access_groups: List of Access Group IDs.
    :param access_schedule_events: List of Access Schedule Event objects.
    :param doors: List of Door IDs.
    :param name: Name for the Access Level.
    :param sites: List of Site IDs.
    :return: JSON response containing the created Access Level information.
    :raises ValueError: If name is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().create_access_level(name, access_groups, access_schedule_events, doors, sites)

@typechecked
def create_door_exception_calendar(doors: List[str], exceptions: List[Dict[str, Any]], name: str):
    """
    Create a new door exception calendar.

    :param doors: A non-empty list of door IDs.
    :param exceptions: A non-empty list of door exception objects.
    :param name: Name of the door exception calendar.
    :return: JSON response containing the created door exception calendar information.
    :raises ValueError: If any required field is missing or invalid.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().create_door_exception_calendar(doors, exceptions, name)

@typechecked
def deactivate_access_card(card_id: str, user_id: Optional[str] = None, external_id: Optional[str] = None):
    """
    Deactivate an access card for a user.

    :param card_id: The unique identifier for the access card.
    :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
    :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
    :return: JSON response containing the result of the deactivation.
    :raises ValueError: If card_id is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().deactivate_access_card(card_id, user_id, external_id)

@typechecked
def deactivate_ble_for_access_user(user_id: Optional[str] = None, external_id: Optional[str] = None):
    """
    Deactivate BLE for an access user. Exactly one of user_id or external_id must be provided.

    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :return: JSON response after deactivating BLE for the access user.
    :rtype: dict
    :raises ValueError: If not exactly one of user_id or external_id is provided.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().deactivate_ble_for_access_user(user_id, external_id)

@typechecked
def deactivate_license_plate(license_plate_number: str, user_id: Optional[str] = None, external_id: Optional[str] = None):
    """
    Deactivate a license plate for a user.

    :param license_plate_number: The license plate number to be deactivated.
    :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
    :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
    :return: JSON response containing the result of the deactivation.
    :raises ValueError: If license_plate_number is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().deactivate_license_plate(license_plate_number, user_id, external_id)

@typechecked
def deactivate_remote_unlock_for_user(user_id: Optional[str] = None, external_id: Optional[str] = None):
    """
    Deactivate remote unlock for an access user.

    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :return: JSON response after deactivating remote unlock.
    :rtype: dict

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().deactivate_remote_unlock_for_user(user_id, external_id)

@typechecked
def delete_access_card(card_id: str, user_id: Optional[str] = None, external_id: Optional[str] = None):
    """
    Delete an access card for a user.

    :param card_id: The unique identifier for the access card.
    :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
    :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
    :return: JSON response containing the result of the deletion.
    :raises ValueError: If card_id is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().delete_access_card(card_id, user_id, external_id)

@typechecked
def delete_access_group(group_id: str):
    """
    Delete an access group.

    :param group_id: The unique identifier for the access group.
    :type group_id: str
    :return: JSON response after deleting the access group.
    :rtype: dict
    :raises ValueError: If group_id is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().delete_access_group(group_id)

@typechecked
def delete_access_level(access_level_id: str):
    """
    Delete an access level.

    :param access_level_id: The unique identifier for the access level to delete.
    :return: The raw response content confirming deletion.
    :raises ValueError: If access_level_id is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().delete_access_level(access_level_id)

@typechecked
def delete_access_schedule_event_on_access_level(access_level_id: str, event_id: str):
    """
    Delete an access schedule event from a specific access level.

    :param access_level_id: The unique identifier for the access level.
    :param event_id: The unique identifier for the schedule event.
    :return: The raw response content confirming deletion.
    :raises ValueError: If access_level_id or event_id is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().delete_access_schedule_event_on_access_level(access_level_id, event_id)

@typechecked
def delete_door_exception_calendar(calendar_id: str):
    """
    Delete a door exception calendar.

    :param calendar_id: The unique identifier for the door exception calendar to delete.
    :return: JSON response confirming deletion.
    :raises ValueError: If calendar_id is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().delete_door_exception_calendar(calendar_id)

@typechecked
def delete_exception_on_door_exception_calendar(calendar_id: str, exception_id: str):
    """
    Delete an exception from a door exception calendar.

    :param calendar_id: The unique identifier for the door exception calendar.
    :param exception_id: The unique identifier for the exception to delete.
    :return: JSON response confirming deletion of the exception.
    :raises ValueError: If calendar_id or exception_id is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().delete_exception_on_door_exception_calendar(calendar_id, exception_id)

@typechecked
def delete_license_plate_from_user(license_plate_number: str, user_id: Optional[str] = None, external_id: Optional[str] = None):
    """
    Delete a license plate from a user.

    :param license_plate_number: The license plate number to be deleted.
    :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
    :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
    :return: JSON response containing the result of the deletion.
    :raises ValueError: If license_plate_number is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().delete_license_plate_from_user(license_plate_number, user_id, external_id)

@typechecked
def delete_mfa_code_from_user(code: str, user_id: Optional[str] = None, external_id: Optional[str] = None):
    """
    Delete an MFA code from a user.

    :param code: The MFA code to be deleted.
    :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
    :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
    :return: JSON response containing the result of the deletion.
    :raises ValueError: If code is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().delete_mfa_code_from_user(code, user_id, external_id)

@typechecked
def delete_profile_photo(user_id: Optional[str] = None, external_id: Optional[str] = None):
    """
    Delete the profile photo for an access user.

    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :return: JSON response after deleting the profile photo.
    :rtype: dict

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().delete_profile_photo(user_id, external_id)

@typechecked
def get_access_events(start_time: Optional[int] = None, end_time: Optional[int] = None, page_token: Optional[str] = None, page_size: Optional[int] = 100, event_type: Optional[List[str]] = None, site_id: Optional[str] = None, device_id: Optional[str] = None, user_id: Optional[str] = None):
    """
    Retrieve access events based on various filters.

    :param start_time: The start of the time range for requested events, as a Unix timestamp in seconds.
                       Defaults to one hour ago from the current time if not provided.
    :param end_time: The end of the time range for requested events, as a Unix timestamp in seconds.
                     Defaults to the current time if not provided.
    :param page_token: The pagination token used to fetch the next page of results.
    :param page_size: The number of items returned in a single response (0 to 200). Defaults to 100.
    :param event_type: One or multiple comma-separated event type values.
    :param site_id: One or multiple comma-separated site identifiers.
    :param device_id: One or multiple comma-separated device identifiers.
    :param user_id: One or multiple comma-separated user identifiers.
    :return: JSON response containing access events matching the provided filters.
    :raises ValueError: If page_size is not between 0 and 200.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().get_access_events(start_time, end_time, page_token, page_size, event_type, site_id, device_id, user_id)

@typechecked
def get_access_group(group_id: str):
    """
    Retrieve a specific access group by its ID.

    :param group_id: The unique identifier for the access group.
    :type group_id: str
    :return: JSON response containing the access group details.
    :rtype: dict
    :raises ValueError: If group_id is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().get_access_group(group_id)

@typechecked
def get_access_groups():
    """
    Retrieve all access groups.

    :return: JSON response containing a list of access groups.
    :rtype: dict

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().get_access_groups()

@typechecked
def get_access_level(access_level_id: str):
    """
    Retrieve details for a specific access level.

    :param access_level_id: The unique identifier for the access level.
    :return: JSON response containing the access level details.
    :raises ValueError: If access_level_id is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().get_access_level(access_level_id)

@typechecked
def get_access_user(user_id: Optional[str] = None, external_id: Optional[str] = None):
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

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().get_access_user(user_id, external_id)

@typechecked
def get_all_access_levels():
    """
    Retrieve all available access levels.

    :return: JSON response containing all available access levels.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().get_all_access_levels()

@typechecked
def get_all_access_users():
    """
    Retrieve all access user information.

    :return: JSON response containing access user information.
    :rtype: dict

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().get_all_access_users()

@typechecked
def get_all_door_exception_calendars(last_updated_at: Optional[int] = None):
    """
    Retrieve all available door exception calendars.

    :param last_updated_at: Optional timestamp (Unix seconds) to filter calendars updated after this time.
    :return: JSON response containing all available door exception calendars.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().get_all_door_exception_calendars(last_updated_at)

@typechecked
def get_door_exception_calendar(calendar_id: str):
    """
    Retrieve a specific door exception calendar.

    :param calendar_id: The unique identifier for the door exception calendar.
    :return: JSON response containing the door exception calendar details.
    :raises ValueError: If calendar_id is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().get_door_exception_calendar(calendar_id)

@typechecked
def get_doors(door_id_list: Optional[List[Any]] = None, site_id_list: Optional[List[Any]] = None):
    """
    Retrieve door information.

    This function sends a GET request to retrieve details for doors based on provided door IDs and/or site IDs.

    :param door_id_list: A list of door IDs. If provided, these will be joined into a comma-separated string.
    :param site_id_list: A list of site IDs. If provided, these will be joined into a comma-separated string.
    :return: JSON response containing door information.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().get_doors(door_id_list, site_id_list)

@typechecked
def get_exception_on_door_exception_calendar(calendar_id: str, exception_id: str):
    """
    Retrieve a specific exception from a door exception calendar.

    :param calendar_id: The unique identifier for the door exception calendar.
    :param exception_id: The unique identifier for the exception.
    :return: JSON response containing the exception details.
    :raises ValueError: If calendar_id or exception_id is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().get_exception_on_door_exception_calendar(calendar_id, exception_id)

@typechecked
def get_profile_photo(user_id: Optional[str] = None, external_id: Optional[str] = None, original: Optional[bool] = False):
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

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().get_profile_photo(user_id, external_id, original)

@typechecked
def remove_entry_code_for_user(user_id: Optional[str] = None, external_id: Optional[str] = None):
    """
    Remove the entry code for an access user.

    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :return: JSON response after removing the entry code for the access user.
    :rtype: dict
    :raises ValueError: If not exactly one of user_id or external_id is provided.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().remove_entry_code_for_user(user_id, external_id)

@typechecked
def remove_user_from_access_group(group_id: str, external_id: Optional[str] = None, user_id: Optional[str] = None):
    """
    Remove a user from an access group. Exactly one of user_id or external_id must be provided.

    :param group_id: The unique identifier for the access group.
    :type group_id: str
    :param external_id: The external identifier for the user.
    :type external_id: str, optional
    :param user_id: The internal user identifier.
    :type user_id: str, optional
    :return: JSON response after removing the user from the access group.
    :rtype: dict
    :raises ValueError: If group_id is empty, or if not exactly one of user_id or external_id is provided.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().remove_user_from_access_group(group_id, external_id, user_id)

@typechecked
def send_pass_app_invite_for_user(user_id: Optional[str] = None, external_id: Optional[str] = None):
    """
    Send a Pass App invite for an access user.

    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :return: JSON response after sending the invite.
    :rtype: dict

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().send_pass_app_invite_for_user(user_id, external_id)

@typechecked
def set_end_date_for_user(end_date: str, user_id: Optional[str] = None, external_id: Optional[str] = None):
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

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().set_end_date_for_user(end_date, user_id, external_id)

@typechecked
def set_entry_code_for_user(entry_code: str, user_id: Optional[str] = None, external_id: Optional[str] = None, override: Optional[bool] = False):
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

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().set_entry_code_for_user(entry_code, user_id, external_id, override)

@typechecked
def set_start_date_for_user(start_date: str, user_id: Optional[str] = None, external_id: Optional[str] = None):
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

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().set_start_date_for_user(start_date, user_id, external_id)

@typechecked
def unlock_door_as_admin(door_id: str):
    """
    Unlock a door as an administrator.

    This function sends a request to unlock the specified door without requiring user identification.

    :param door_id: The unique identifier for the door.
    :return: JSON response containing the result of the unlock operation.
    :raises ValueError: If door_id is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().unlock_door_as_admin(door_id)

@typechecked
def unlock_door_as_user(door_id: str, user_id: Optional[str] = None, external_id: Optional[str] = None):
    """
    Unlock a door as a user.

    This function sends a request to unlock the specified door, using either the internal user_id or the external_id.

    :param door_id: The unique identifier for the door.
    :param user_id: The internal user identifier (exactly one of user_id or external_id must be provided).
    :param external_id: The external user identifier (exactly one of user_id or external_id must be provided).
    :return: JSON response containing the result of the unlock operation.
    :raises ValueError: If door_id is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().unlock_door_as_user(door_id, user_id, external_id)

@typechecked
def update_access_level(access_level_id: str, access_groups: List[str], access_schedule_events: List[Dict[str, Any]], doors: List[str], name: str, sites: List[str]):
    """
    Update an existing Access Level.

    To use this API, you need an API Key having permission "Door Access Management"
    for all sites listed in 'sites' for the Access Level, and "Manage via API" must
    also be enabled for all doors listed in 'doors'.

    :param access_level_id: The ID of the Access Level to be updated.
    :param access_groups: List of Access Group IDs.
    :param access_schedule_events: List of Access Schedule Event objects.
    :param doors: List of Door IDs.
    :param name: Name for the Access Level.
    :param sites: List of Site IDs.
    :return: JSON response containing the updated Access Level information.
    :raises ValueError: If access_level_id or name is an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().update_access_level(access_level_id, access_groups, access_schedule_events, doors, name, sites)

@typechecked
def update_access_schedule_event_on_access_level(access_level_id: str, event_id: str, start_time: str, end_time: str, weekday: str):
    """
    Update an access schedule event on a specific access level.

    :param access_level_id: The unique identifier for the access level.
    :param event_id: The unique identifier for the schedule event.
    :param start_time: Updated start time in HH:MM format.
    :param end_time: Updated end time in HH:MM format.
    :param weekday: Updated weekday enum (e.g., "SU").
    :return: JSON response containing the updated event information.
    :raises ValueError: If any of the required identifiers or times are invalid.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().update_access_schedule_event_on_access_level(access_level_id, event_id, start_time, end_time, weekday)

@typechecked
def update_door_exception_calendar(doors: List[str], exceptions: List[Dict[str, Any]], name: str, calendar_id: str):
    """
    Update an existing door exception calendar.

    :param doors: A non-empty list of door IDs.
    :param exceptions: A non-empty list of door exception objects.
    :param name: Updated name of the door exception calendar.
    :param calendar_id: The unique identifier of the calendar to update.
    :return: JSON response containing the updated door exception calendar information.
    :raises ValueError: If any required field is missing or invalid.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().update_door_exception_calendar(doors, exceptions, name, calendar_id)

@typechecked
def update_exception_on_door_exception_calendar(calendar_id: str, exception_id: str, exception: Dict[str, Any]):
    """
    Update an Exception on a Door Exception Calendar.

    Updates the Exception identified by `exception_id` on the Door Exception Calendar
    identified by `calendar_id` using the new exception details provided as a single object.

    The provided exception object must follow the expected schema, which is validated using
    the `validate_door_exception` function. For example, the object must include:
      - date (in YYYY-MM-DD format)
      - door_status (one of the allowed values)
      - For non-all-day exceptions, valid start_time and end_time (in HH:MM format)
      - If all_day_default is True, door_status must be "access_controlled", and start_time/end_time
        should be omitted or defaulted to "00:00" and "23:59", respectively.
      - Optional fields such as first_person_in, double_badge, and their corresponding group IDs,
        as well as an optional recurrence_rule object.

    :param calendar_id: The unique identifier for the door exception calendar.
    :param exception_id: The unique identifier for the exception to update.
    :param exception: A dictionary representing the new exception details.
    :return: JSON response containing the updated exception information.
    :raises ValueError: If any required parameter is missing or if the exception object fails validation.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().update_exception_on_door_exception_calendar(calendar_id, exception_id, exception)

@typechecked
def upload_profile_photo(photo_path: str, user_id: Optional[str] = None, external_id: Optional[str] = None, overwrite: Optional[bool] = False):
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

    ---

    **Note:** This is a functional wrapper for its equivalent method in the AccessControlClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use an AccessControlClient object directly for better performance.
    """
    return AccessControlClient().upload_profile_photo(photo_path, user_id, external_id, overwrite)
@typechecked
def validate_recurrence_rule(rr: Dict[str, Any],
                             idx: Optional[int] = None) -> None:
    """
    Validates a recurrence rule object based on the expected schema.

    :param rr: The recurrence rule object.
    :param idx: Optional index for context.
    :raises ValueError: If any required field is missing or invalid.
    """
    require_non_empty_str(rr.get("frequency", ""), "frequency", idx)
    frequency = rr["frequency"]

    if "interval" not in rr or not isinstance(rr["interval"], int):
        raise ValueError(
            f"Exception at index {idx}: 'interval' must be an integer in recurrence_rule")

    require_non_empty_str(rr.get("start_time", ""),
                          "recurrence_rule start_time", idx)
    if not is_valid_time(rr["start_time"]):
        raise ValueError(
            f"Exception at index {idx}: 'recurrence_rule start_time' must be in HH:MM format")

    if "by_day" in rr:
        # Validate that by_day is a list of non-empty strings.
        if not isinstance(rr["by_day"], list) or not all(
                isinstance(day, str) and day.strip() for day in rr["by_day"]):
            raise ValueError(
                f"Exception at index {idx}: 'by_day' must be a list of non-empty strings")
        # Validate allowed usage based on frequency.
        if frequency == FREQUENCY_ENUM["DAILY"]:
            raise ValueError(
                f"Exception at index {idx}: 'by_day' is not supported for DAILY frequency")
        elif frequency == FREQUENCY_ENUM["WEEKLY"]:
            if len(rr["by_day"]) < 1:
                raise ValueError(
                    f"Exception at index {idx}: 'by_day' must contain at least one value for WEEKLY frequency")
        elif frequency in (FREQUENCY_ENUM["MONTHLY"],
                           FREQUENCY_ENUM["YEARLY"]):
            if "by_set_pos" not in rr or rr["by_set_pos"] is None:
                raise ValueError(
                    f"Exception at index {idx}: For MONTHLY or YEARLY frequency, 'by_set_pos' is required when 'by_day' is provided")
            if len(rr["by_day"]) != 1:
                raise ValueError(
                    f"Exception at index {idx}: For MONTHLY or YEARLY frequency, 'by_day' must contain exactly one value")
        # Validate that each day is one of the allowed weekdays.
        if not set(rr["by_day"]).issubset(set(WEEKDAY_ENUM.values())):
            raise ValueError(
                f"Exception at index {idx}: 'by_day' values must be one of {list(WEEKDAY_ENUM.values())}")

    if "by_month" in rr:
        if not isinstance(rr["by_month"], int) or not (
                1 <= rr["by_month"] <= 12) or frequency != FREQUENCY_ENUM[
            "YEARLY"]:
            raise ValueError(
                f"Exception at index {idx}: 'by_month' must be an integer between 1 and 12 and is only supported for YEARLY frequency.")

    if "by_month_day" in rr:
        if frequency not in (FREQUENCY_ENUM["MONTHLY"],
                             FREQUENCY_ENUM["YEARLY"]):
            raise ValueError(
                f"Exception at index {idx}: 'by_month_day' is only supported for MONTHLY or YEARLY frequency.")
        if "by_set_pos" in rr:
            raise ValueError(
                f"Exception at index {idx}: Only one of 'by_month_day' or 'by_set_pos' is allowed.")
        if not isinstance(rr["by_month_day"], int) or not (
                1 <= rr["by_month_day"] <= 31):
            raise ValueError(
                f"Exception at index {idx}: 'by_month_day' must be an integer between 1 and 31.")

    if "by_set_pos" in rr:
        if not isinstance(rr["by_set_pos"], int) or not (
                1 <= rr["by_set_pos"] <= 5):
            raise ValueError(
                f"Exception at index {idx}: 'by_set_pos' must be an integer between 1 and 5.")
        if frequency not in (FREQUENCY_ENUM["MONTHLY"],
                             FREQUENCY_ENUM["YEARLY"]):
            raise ValueError(
                f"Exception at index {idx}: 'by_set_pos' is only supported for MONTHLY or YEARLY frequency.")

    if "excluded_dates" in rr:
        if not isinstance(rr["excluded_dates"], list) or not all(
                isinstance(d, str) and is_valid_date(d) for d in
                rr["excluded_dates"]):
            raise ValueError(
                f"Exception at index {idx}: 'excluded_dates' must be a list of valid dates in YYYY-MM-DD format")

    if "until" in rr:
        if not isinstance(rr["until"], str) or not is_valid_date(rr["until"]):
            raise ValueError(
                f"Exception at index {idx}: 'until' must be a valid date in YYYY-MM-DD format")

    if "count" in rr:
        if not isinstance(rr["count"], int):
            raise ValueError(
                f"Exception at index {idx}: 'count' must be an integer")
    if "count" in rr and "until" in rr:
        raise ValueError(
            f"Exception at index {idx}: Only one of 'count' or 'until' may be provided in recurrence_rule")


@typechecked
def validate_door_exception(exc: Dict[str, Any],
                            idx: Optional[int] = None) -> None:
    """
    Validates a door exception object based on the expected schema.

    :param exc: The door exception object.
    :param idx: Optional index for context.
    :raises ValueError: If any required field is missing or invalid.
    """
    if not isinstance(exc, dict):
        raise ValueError(f"Exception at index {idx}: must be a dictionary")

    if "date" not in exc:
        raise ValueError(f"Exception at index {idx}: 'date' is required")
    require_non_empty_str(exc["date"], "date", idx)
    if not is_valid_date(exc["date"]):
        raise ValueError(
            f"Exception at index {idx}: 'date' must be in YYYY-MM-DD format")

    if "door_status" not in exc:
        raise ValueError(
            f"Exception at index {idx}: 'door_status' is required")
    require_non_empty_str(exc["door_status"], "door_status", idx)
    if exc["door_status"] not in list(DOOR_STATUS_ENUM.values()):
        raise ValueError(
            f"Exception at index {idx}: 'door_status' must be one of {list(DOOR_STATUS_ENUM.values())}")

    if exc.get("double_badge", False):
        if not isinstance(exc["double_badge"], bool):
            raise ValueError(
                f"Exception at index {idx}: 'double_badge' must be a boolean")
        if "double_badge_group_ids" not in exc or not isinstance(
                exc["double_badge_group_ids"], list):
            raise ValueError(
                f"Exception at index {idx}: 'double_badge_group_ids' must be provided as a list when double_badge is True")

    if "double_badge_group_ids" in exc:
        if "double_badge" not in exc or exc.get("double_badge") is False:
            raise ValueError(
                f"Exception at index {idx}: 'double_badge must also be set to TRUE if double_badge_group_ids are provided.")

    all_day = exc.get("all_day_default", False)
    if all_day:
        if exc["door_status"] != "access_controlled":
            raise ValueError(
                f"Exception at index {idx}: when all_day_default is True, door_status must be 'access_controlled'")
        if "start_time" in exc and exc["start_time"] not in (None, "",
                                                             "00:00"):
            raise ValueError(
                f"Exception at index {idx}: when all_day_default is True, start_time must be '00:00' or not provided")
        if "end_time" in exc and exc["end_time"] not in (None, "", "23:59"):
            raise ValueError(
                f"Exception at index {idx}: when all_day_default is True, end_time must be '23:59' or not provided")
    else:
        if "start_time" not in exc:
            raise ValueError(
                f"Exception at index {idx}: 'start_time' is required for non all-day exceptions")
        require_non_empty_str(exc["start_time"], "start_time", idx)
        if not is_valid_time(exc["start_time"]):
            raise ValueError(
                f"Exception at index {idx}: 'start_time' must be in HH:MM format")
        if "end_time" not in exc:
            raise ValueError(
                f"Exception at index {idx}: 'end_time' is required for non all-day exceptions")
        require_non_empty_str(exc["end_time"], "end_time", idx)
        if not is_valid_time(exc["end_time"]):
            raise ValueError(
                f"Exception at index {idx}: 'end_time' must be in HH:MM format")

    if exc.get("first_person_in", False):
        if "first_person_in_group_ids" not in exc or not isinstance(
                exc["first_person_in_group_ids"], list):
            raise ValueError(
                f"Exception at index {idx}: 'first_person_in_group_ids' must be provided as a list when first_person_in is True")

    if "recurrence_rule" in exc:
        validate_recurrence_rule(exc["recurrence_rule"], idx)