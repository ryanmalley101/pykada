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


VALID_EVENT_TYPES = {
    "DOOR_OPENED": "door_opened",
    "DOOR_REJECTED": "door_rejected",
    "DOOR_GRANTED": "door_granted",
    "DOOR_FORCED_OPEN": "door_forced_open",
    "DOOR_HELD_OPEN": "door_held_open",
    "DOOR_TAILGATING": "door_tailgating",
    "DOOR_CROWD_DETECTION": "door_crowd_detection",
    "DOOR_TAMPER": "door_tampam",  # Note: Check spelling if required ("door_tamper" might be intended)
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
