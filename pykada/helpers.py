import copy
import csv
import os
import random
import string
import time
import typing
from typing import Optional

from typeguard import typechecked


WEEKDAY_ENUM = {
    "SUNDAY": "SU",
    "MONDAY": "MO",
    "TUESDAY": "TU",
    "WEDNESDAY": "WE",
    "THURSDAY": "TH",
    "FRIDAY": "FR",
    "SATURDAY": "SA",
}

FREQUENCY_ENUM = {
    "DAILY": "DAILY",
    "WEEKLY": "WEEKLY",
    "MONTHLY": "MONTHLY",
    "YEARLY": "YEARLY"
}

DOOR_STATUS_ENUM = {
    "LOCKED": "LOCKED",
    "CARD_AND_CODE": "CARD_AND_CODE",
    "ACCESS_CONTROLLED": "ACCESS_CONTROLLED",
    "UNLOCKED": "UNLOCKED"
}

SENSOR_FIELD_ENUM = {
    "HUMIDITY": "humidity",
    "MOTION": "motion",
    "NOISE_LEVEL": "noise_level",
    "PM_2_5": "pm_2_5",
    "PM_4_0": "pm_4_0",
    "PM_1_0_0": "pm_1_0_0",
    "TAMPER": "tamper",
    "TEMPERATURE": "temperature",
    "TVOC_SV11": "tvoc(SV11)",
    "USA_AIR_QUALITY_INDEX": "usa_air_quality_index",
    "VAPE_INDEX": "vape_index",
    "CARBON_DIOXIDE": "carbon_dioxide",
    "CARBON_MONOXIDE": "carbon_monoxide",
    "BAROMETRIC_PRESSURE": "barometric_pressure",
    "FORMALDEHYDE": "formaldehyde",
    "AMBIENT_LIGHT": "ambient_light",
    "TVOC_INDEX": "tvoc_index(SV23/SV25)",
    "HEAT_INDEX": "heat_index"
}


VALID_ACCESS_EVENT_TYPES_ENUM = {
    "DOOR_OPENED": "door_opened",
    "DOOR_REJECTED": "door_rejected",
    "DOOR_GRANTED": "door_granted",
    "DOOR_FORCED_OPEN": "door_forced_open",
    "DOOR_HELD_OPEN": "door_held_open",
    "DOOR_TAILGATING": "door_tailgating",
    "DOOR_CROWD_DETECTION": "door_crowd_detection",
    "DOOR_TAMPER": "door_tamper",
    "DOOR_POI_DETECTION": "door_poi_detection",
    "DOOR_INITIALIZED": "door_initialized",
    "DOOR_ARMED": "door_armed",
    "DOOR_ARMED_BUTTON_PRESSED": "door_armed_button_pressed",
    "DOOR_AUX_UNLOCK": "door_aux_unlock",
    "DOOR_LOCKED": "door_locked",
    "DOOR_UNLOCKED": "door_unlocked",
    "DOOR_UNARMED_EVENT": "door_unarmed_event",
    "DOOR_CODE_ENTERED_EVENT": "door_code_entered_event",
    "DOOR_BUTTON_PRESS_ENTERED_EVENT": "door_button_press_entered_event",
    "DOOR_ACU_STARTUP": "door_acu_startup",
    "DOOR_LOCK_STATE_CHANGED": "door_lock_state_changed",
    "DOOR_LOCKDOWN": "door_lockdown",
    "DOOR_AUXINPUT_CHANGE_STATE": "door_auxinput_change_state",
    "DOOR_AUXINPUT_HELD": "door_auxinput_held",
    "DOOR_LOW_BATTERY": "door_low_battery",
    "DOOR_CRITICAL_BATTERY": "door_critical_battery",
    "DOOR_MOBILE_NFC_SCAN_ACCEPTED": "door_mobile_nfc_scan_accepted",
    "DOOR_MOBILE_NFC_SCAN_REJECTED": "door_mobile_nfc_scan_rejected",
    "DOOR_USER_DATABASE_CORRUPT": "door_user_database_corrupt",
    "DOOR_KEYCARD_ENTERED_ACCEPTED": "door_keycard_entered_accepted",
    "DOOR_KEYCARD_ENTERED_REJECTED": "door_keycard_entered_rejected",
    "DOOR_CODE_ENTERED_ACCEPTED": "door_code_entered_accepted",
    "DOOR_CODE_ENTERED_REJECTED": "door_code_entered_rejected",
    "DOOR_REMOTE_UNLOCK_ACCEPTED": "door_remote_unlock_accepted",
    "DOOR_REMOTE_UNLOCK_REJECTED": "door_remote_unlock_rejected",
    "DOOR_PRESS_TO_EXIT_ACCEPTED": "door_press_to_exit_accepted",
    "DOOR_BLE_UNLOCK_ATTEMPT_ACCEPTED": "door_ble_unlock_attempt_accepted",
    "DOOR_BLE_UNLOCK_ATTEMPT_REJECTED": "door_ble_unlock_attempt_rejected",
    "DOOR_ACU_OFFLINE": "door_acu_offline",
    "DOOR_FIRE_ALARM_TRIGGERED": "door_fire_alarm_triggered",
    "DOOR_FIRE_ALARM_RELEASED": "door_fire_alarm_released",
    "DOOR_ACU_FIRE_ALARM_TRIGGERED": "door_acu_fire_alarm_triggered",
    "DOOR_ACU_FIRE_ALARM_RELEASED": "door_acu_fire_alarm_released",
    "DOOR_SCHEDULE_TOGGLE": "door_schedule_toggle",
    "DOOR_ACU_DPI_CUT": "door_acu_dpi_cut",
    "DOOR_ACU_DPI_SHORT": "door_acu_dpi_short",
    "DOOR_ACU_REX_CUT": "door_acu_rex_cut",
    "DOOR_ACU_REX_SHORT": "door_acu_rex_short",
    "DOOR_ACU_REX2_CUT": "door_acu_rex2_cut",
    "DOOR_ACU_REX2_SHORT": "door_acu_rex2_short",
    "DOOR_ACU_AUXINPUT_CUT": "door_acu_auxinput_cut",
    "DOOR_ACU_AUXINPUT_SHORT": "door_acu_auxinput_short",
    "DOOR_LOCKDOWN_DEBOUNCED": "door_lockdown_debounced",
    "DOOR_LP_PRESENTED_ACCEPTED": "door_lp_presented_accepted",
    "DOOR_LP_PRESENTED_REJECTED": "door_lp_presented_rejected",
    "DOOR_APB_DOUBLE_ENTRY": "door_apb_double_entry",
    "DOOR_APB_DOUBLE_EXIT": "door_apb_double_exit",
    "ALL_ACCESS_GRANTED": "all_access_granted",
    "ALL_ACCESS_REJECTED": "all_access_rejected",
    "DOOR_AUXOUTPUT_ACTIVATED": "door_auxoutput_activated",
    "DOOR_AUXOUTPUT_DEACTIVATED": "door_auxoutput_deactivated"
}

VALID_CARD_TYPES_ENUM = {
    "STANDARD_26_BIT_WIEGAND": "Standard 26-bit Wiegand",
    "HID_37_BIT": "HID 37-bit",
    "HID_37_BIT_NO_FACILITY_CODE": "HID 37-bit No Facility Code",
    "HID_34_BIT": "HID 34-bit",
    "CASI_RUSCO_40_BIT": "Casi Rusco 40-Bit",
    "HID_CORPORATE_1000_35": "HID Corporate 1000-35",
    "HID_CORPORATE_1000_48": "HID Corporate 1000-48",
    "HID_ICLASS": "HID iClass",
    "DESFIRE_CSN": "DESFire CSN",
    "VERKADA_DESFIRE": "Verkada DESFire",
    "DESFIRE_40X": "DESFire 40X",
    "APPLE_WALLET_PASS": "Apple Wallet Pass",
    "MIFARE_4_BYTE_CSN": "MiFare 4-Byte (32 bit) CSN",
    "MDC_CUSTOM_64_BIT": "MDC Custom 64-bit",
    "HID_36_BIT_KEYSCAN": "HID 36-bit Keyscan",
    "HID_33_BIT_DSX": "HID 33-bit DSX",
    "HID_33_BIT_RS2": "HID 33-bit RS2",
    "HID_36_BIT_SIMPLEX": "HID 36-bit Simplex",
    "CANSEC_37_BIT": "Cansec 37-bit",
    "CREDIT_CARD_BIN_NUMBER": "Credit Card BIN Number",
    "KANTECH_XSF": "Kantech XSF",
    "SCHLAGE_34_BIT": "Schlage 34-bit",
    "SCHLAGE_37_BIT": "Schlage 37-bit",
    "RBH_50_BIT": "RBH 50-bit",
    "GUARDALL_G_PROX_II_36_BIT": "Guardall G-Prox II 36-bit",
    "AMAG_32_BIT": "AMAG 32-bit",
    "SECURITAS_37_BIT": "Securitas 37-bit",
    "KASTLE_32_BIT": "Kastle 32-bit",
    "POINTGUARD_MDI_37_BIT": "PointGuard MDI 37-bit",
    "BLACKBOARD_64_BIT": "Blackboard 64-bit",
    "IDM_64_BIT": "IDm 64-bit",
    "CONTINENTAL_36_BIT": "Continental 36-bit",
    "AWID_34_BIT": "AWID 34-bit",
    "LICENSE_PLATE": "License Plate",
    "HID_INFINITY_37_BIT": "HID Infinity 37-bit",
    "HID_CERIDIAN_26_BIT": "HID Ceridian 26-bit",
    "ICLASS_35_BIT": "iClass 35-bit",
    "ANDOVER_CONTROLS_37_BIT": "Andover Controls 37-bit"
}

VALID_OCCUPANCY_TRENDS_INTERVALS_ENUM = {
    "15_MINUTES": "15_minutes",
    "1_HOUR": "1_hour",
    "6_HOURS": "6_hours",
    "12_HOURS": "12_hours",
    "1_DAY": "1_day",
    "30_DAYS": "30_days"
}

VALID_OCCUPANCY_TRENDS_TYPES_ENUM = {
    "PERSON": "person",
    "VEHICLE": "vehicle"
}

VALID_CLOUD_BACKUP_VIDEO_QUALITY_ENUM = {
    "STANDARD_QUALITY": "STANDARD_QUALITY",
    "HIGH_QUALITY": "HIGH_QUALITY",
}

VALID_CLOUD_BACKUP_VIDEO_TO_UPLOAD_ENUM = {
    "ALL": "ALL",
    "MOTION": "MOTION",
}

VALID_IMAGE_RESOLUTION_ENUM = {
    "LOW_RES": "low-res",
    "HI_RES": "hi-res",
}


def remove_null_fields(obj: dict):
    """
    Removes fields with a value of None from a dictionary.
    :param obj:
    :return: A dictionary with no values of None
    """
    return {k: v for k, v in obj.items() if v is not None}


@typechecked
def require_non_empty_str(value: str, field_name: str, idx: Optional[int] = None) -> None:
    """
    Ensures that a value is a non-empty string.

    :param value: The string value to check.
    :param field_name: The name of the field for error messaging.
    :param idx: Optional index for context.
    :raises ValueError: If value is not a non-empty string.
    """
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        if idx is not None:
            msg += f" (at index {idx})"
        raise ValueError(msg)


def check_user_external_id(user_id, external_id):
    """
    Check if only one of user_id or external_id are provided.
    Throw an error if neither or both are provided.
    The AC API requires exactly one of these identifiers.

    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :return: A dictionary containing the provided identifier.
    """
    if (user_id is None and external_id is None) or (user_id is not None and external_id is not None):
        raise ValueError("Exactly one of user_id or external_id must be provided, not both or neither.")

    params = {"user_id": user_id, "external_id": external_id}
    params = remove_null_fields(params)
    return params



def iterate_paginated_results(
    paginated_func: typing.Callable[..., dict],
    items_key: Optional[str] = None,
    initial_params: Optional[dict]=None,
    next_token_key: Optional[str] = None,
    default_page_size: Optional[int] = 100,
    # Optional: Add delay between requests to avoid hitting rate limits
    request_delay_seconds: Optional[float] = 0
) -> typing.Generator[typing.Any, None, None]:
    """
    Iterates through all pages of results from a paginated function.

    Args:
        paginated_func: The function that fetches a single page of results.
                        It must accept 'page_size' and 'page_token' in its
                        parameters and return a dict containing a list of items
                        under 'items_key' and the next page token under
                        'next_token_key'.
        initial_params: A dictionary of parameters for the *first* API call,
                        excluding 'page_size' and 'page_token'. This dict
                        will be deep copied before use.
        items_key: The key in the response dictionary that contains the list
                   of items for the current page (e.g., 'alerts', 'items', 'data').
        next_token_key: The key in the response dictionary that contains the
                        token for the next page (e.g., 'next_page_token',
                        'page_token'). Should be None when there are no more pages.
        default_page_size: The page size to use if not specified in initial_params.
        request_delay_seconds: Optional delay in seconds between fetching pages.

    Yields:
        Each individual item from the paginated results across all pages.
    """
    if initial_params is None:
        initial_params = {}
    current_page_token: typing.Optional[str] = None
    # Start with a deep copy of initial_params to avoid modifying the original
    params = copy.deepcopy(initial_params)

    # Set default page size if not provided in initial_params or is None
    if 'page_size' not in params or params['page_size'] is None:
         params['page_size'] = default_page_size

    # Ensure page_token is initially absent or None, it will be added/updated below
    params.pop('page_token', None)

    while True:
        # Add or update page_token for the current iteration's request
        # On the first loop, current_page_token is None, which is correct for the first page
        params['page_token'] = current_page_token

        # Call the wrapped function to get the current page
        try:
            response = paginated_func(**params)
        except Exception as e:
            # Handle potential exceptions from the wrapped function (e.g., network errors, API errors)
            # You might want more specific error handling or retry logic here
            print(f"Error fetching page with token {current_page_token}: {e}")
            raise # Re-raise the exception

        # Validate the response structure
        if not isinstance(response, dict):
             print(f"Warning: Paginated function did not return a dictionary. Response: {response}")
             break # Stop iteration if response is unexpected

        response_keys = list(response.keys())
        if not next_token_key and len(response_keys):
            potential_next_token_keys = [string for string in response_keys if "token" in string]
            if len(potential_next_token_keys) == 1:
                next_token_key = potential_next_token_keys[0]

        if not next_token_key:
            raise ValueError("next_token_key was not provided and could "
                             "not be inferred from response")

        if not items_key and len(response_keys) == 2:
            potential_items_key = [string for string in response_keys if "token" not in string]
            if len(potential_items_key) == 1:
                items_key = potential_items_key[0]

        if not items_key:
            raise ValueError("next_token_key was not provided and could "
                             "not be inferred from response")

        # Extract items and the next page token using the provided keys
        items = response.get(items_key, [])

        next_page_token_from_response = response.get(next_token_key)

        # Yield items from the current page
        for item in items:
            yield item

        # Update the page token for the next iteration
        current_page_token = next_page_token_from_response

        # Check if there are more pages. If the next token is None, we are done.
        if current_page_token is None:
            break

        # Optional: Wait before making the next request
        if request_delay_seconds > 0:
            time.sleep(request_delay_seconds)

def verify_csv_columns(file_path: str, expected_headers_list: typing.List[str]) -> bool:
    """
    Verifies if a CSV file exists and contains exactly the columns
    specified in the expected_headers_list. The order of columns
    in the file does not matter.

    Args:
        file_path: The path to the CSV file.
        expected_headers_list: A list of strings representing the exact
                                names and number of columns expected in the CSV header.

    Returns:
        True if the file exists and has the specified columns,
        False otherwise.
    """
    # Convert the expected headers list to a set for efficient comparison (order doesn't matter)
    expected_headers_set: typing.Set[str] = set(expected_headers_list)
    expected_column_count = len(expected_headers_list)

    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        return False

    if expected_column_count == 0:
        print("Error: expected_headers_list cannot be empty.")
        return False

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)

            # Read the header row
            try:
                headers = next(reader)
            except StopIteration:
                print(f"Error: File '{file_path}' is empty or has no header row.")
                return False
            except Exception as e:
                 print(f"Error reading header from '{file_path}': {e}")
                 return False

            # Check if the number of columns matches the expected count
            if len(headers) != expected_column_count:
                print(f"Error: File '{file_path}' does not have the expected number of columns.")
                print(f"Expected {expected_column_count}, Found {len(headers)}.")
                print(f"Columns found: {headers}")
                return False

            # Check if the column names are the expected ones (order doesn't matter)
            actual_headers_set = set(headers)

            if actual_headers_set != expected_headers_set:
                print(f"Error: File '{file_path}' has incorrect column names.")
                print(f"Expected names: {expected_headers_set}, Found names: {actual_headers_set}")
                return False

            # If all checks pass
            print(f"File '{file_path}' successfully verified: has the expected {expected_column_count} columns.")
            return True

    except Exception as e:
        # Catch other potential CSV reading errors
        print(f"An unexpected error occurred while processing '{file_path}': {e}")
        return False


def generate_random_alphanumeric_string(length=16):
    """
    Generate a random alphanumeric string of the specified length.
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def generate_random_numeric_string(length=16):
    """
    Generate a random numeric string of the specified length.
    """
    characters = string.digits
    return ''.join(random.choice(characters) for _ in range(length))