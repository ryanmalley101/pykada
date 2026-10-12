"""
Live smoke test for the access control functional API against the real
Verkada API. Creates a throwaway user, group, access level and exception
calendar, exercises them, and deletes them in a ``finally`` block.

Set DOOR_ID to use a specific API-enabled door; otherwise the first one found
is used.
"""
import os
import time
from datetime import datetime, timedelta, timezone

from termcolor import cprint

from pykada.access_control import (
    add_qr_code_to_user, delete_qr_code_from_user, disable_face_unlock,
    enable_face_unlock_with_uploaded_photo, update_qr_code_state,
    activate_access_card, activate_remote_unlock_for_user,
    add_access_schedule_event_to_access_level, add_card_to_user,
    add_exception_to_door_exception_calendar, add_license_plate_to_user,
    add_mfa_code_to_user, add_user_to_access_group, create_access_group,
    create_access_level, create_door_exception_calendar, deactivate_access_card,
    delete_access_group, delete_access_level,
    delete_access_schedule_event_on_access_level, delete_door_exception_calendar,
    delete_exception_on_door_exception_calendar, delete_license_plate_from_user,
    delete_mfa_code_from_user, find_access_user, get_access_group, get_access_level,
    get_access_user, get_access_schedule_event, get_all_access_groups,
    get_all_access_levels, get_all_access_scenarios, get_all_access_users,
    get_all_door_exception_calendars, get_all_doors,
    get_exception_on_door_exception_calendar, resolve_user_id,
    send_pass_app_invite_for_user, set_ble_unlock, set_entry_code_for_user,
    set_license_plate_active, update_access_level,
    update_access_schedule_event_on_access_level, update_access_user_dates,
    update_door_exception_calendar, update_exception_on_door_exception_calendar,
    upload_profile_photo,
)
from pykada.core_command import create_user, delete_user
from pykada.exceptions import VerkadaBadRequestError, VerkadaForbiddenError
from pykada.enums import VALID_CARD_TYPES_ENUM, WEEKDAY_FULL_ENUM
from pykada.helpers import (generate_random_alphanumeric_string,
                            generate_random_numeric_string)

now = datetime.now(timezone.utc)


def access_control_test():
    """
    Test various access control functionalities.
    """
    door_id = os.getenv("DOOR_ID", None)
    new_user_external_id = generate_random_alphanumeric_string()
    group_id = None
    new_access_level_id = None
    new_calendar_id = None

    new_user = create_user(external_id=new_user_external_id,
                           company_name="ACME Corp",
                           email=f"{new_user_external_id}@example.com",
                           employee_id="E12345",
                           first_name="John",
                           last_name="Doe")
    print("New User:", new_user)
    new_user_id = new_user["user_id"]

    time.sleep(5)  # Wait for the user to propagate to Access

    try:
        if new_user_id not in [u["user_id"] for u in get_all_access_users()]:
            raise ValueError(f"User {new_user_id} not found in access users; "
                             f"creation likely failed")
        assert resolve_user_id(new_user_external_id) == new_user_id
        print("Access user:", get_access_user(new_user_id))
        print("Full v1 record:", find_access_user(email=f"{new_user_external_id}@example.com"))

        # User settings
        set_ble_unlock(new_user_id, active=True)
        set_entry_code_for_user(new_user_id, entry_code=generate_random_numeric_string(8),
                                override=True)
        update_access_user_dates(new_user_id, start_date=now,
                                 end_date=now + timedelta(hours=1))
        activate_remote_unlock_for_user(external_id=new_user_external_id)
        upload_profile_photo(new_user_id, photo_path="Face-Upload-Test.jpeg", overwrite=True)
        send_pass_app_invite_for_user(new_user_id)

        # Credentials
        card_info = add_card_to_user(card_type=VALID_CARD_TYPES_ENUM["STANDARD_26_BIT_WIEGAND"],
                                     external_id=new_user_external_id,
                                     card_number=generate_random_numeric_string(length=4),
                                     facility_code=generate_random_numeric_string(length=2),
                                     active=True)
        card_id = card_info["card_id"]
        deactivate_access_card(card_id, external_id=new_user_external_id)
        activate_access_card(card_id, external_id=new_user_external_id)

        plate = generate_random_alphanumeric_string(length=6).upper()
        add_license_plate_to_user(plate, external_id=new_user_external_id,
                                  name="John's License Plate", active=True)
        set_license_plate_active(plate, active=False, external_id=new_user_external_id)
        set_license_plate_active(plate, active=True, external_id=new_user_external_id)
        time.sleep(3)
        delete_license_plate_from_user(plate, external_id=new_user_external_id)

        mfa_code = generate_random_numeric_string(length=6)
        add_mfa_code_to_user(mfa_code, user_id=new_user_id)
        delete_mfa_code_from_user(mfa_code, user_id=new_user_id)

        qr_code = generate_random_numeric_string(length=12)
        print("QR code:", add_qr_code_to_user("NONE", external_id=new_user_external_id,
                                              qr_code=qr_code))
        print("QR code state:", update_qr_code_state("NONE", user_id=new_user_id,
                                                     qr_code=qr_code, active=False))
        delete_qr_code_from_user("NONE", user_id=new_user_id, qr_code=qr_code)

        # Multipart upload. A face-quality 400 still proves the server received
        # and parsed the image; anything else is a real failure.
        try:
            print("Face unlock:", enable_face_unlock_with_uploaded_photo(
                "Face-Upload-Test.jpeg", user_id=new_user_id, overwrite=True))
        except VerkadaBadRequestError as e:
            if "face" not in str(e).lower():
                raise
            print(f"Face unlock upload received; image rejected: {e}")
        disable_face_unlock(external_id=new_user_external_id)

        # Groups
        group_id = create_access_group(
            f"Test Group {generate_random_alphanumeric_string()}")["group_id"]
        if group_id not in [g["group_id"] for g in get_all_access_groups()]:
            raise ValueError(f"Group {group_id} not found; creation likely failed")
        added = add_user_to_access_group(group_id, new_user_id)
        print("Group after add:", added)
        # Membership is eventually consistent on reads; poll briefly
        for _ in range(10):
            if new_user_id in (get_access_group(group_id).get("user_ids") or []):
                break
            time.sleep(2)
        else:
            raise ValueError(f"User {new_user_id} not in group {group_id} after 20s")

        # Doors
        doors = list(get_all_doors())
        if door_id:
            door_info = next((d for d in doors if d["door_id"] == door_id), None)
            if door_info is None:
                raise ValueError(f"Door {door_id} not found in the organization.")
            if not door_info["api_control_enabled"]:
                raise ValueError(f"Door {door_id} is not API-enabled.")
        else:
            door_info = next((d for d in doors if d["api_control_enabled"]), None)
            if door_info is None:
                raise ValueError("No API-enabled doors found in the organization.")
            door_id = door_info["door_id"]
        door_site_id = door_info["site"]["site_id"]
        print("Door:", door_info)

        # Access levels
        new_access_level_id = create_access_level(
            name=f"Test Access Level {generate_random_alphanumeric_string(length=4)}",
            sites=[door_site_id], access_groups=[group_id], doors=[],
            access_schedule_events=[{"weekday": WEEKDAY_FULL_ENUM["MONDAY"],
                                     "start_time": "08:00", "end_time": "18:00"}],
        )["access_level_id"]
        if new_access_level_id not in [lvl["access_level_id"] for lvl in get_all_access_levels()]:
            raise ValueError(f"Access Level {new_access_level_id} not found")
        update_access_level(new_access_level_id,
                            name=f"Updated Test Access Level "
                                 f"{generate_random_alphanumeric_string(length=4)}",
                            access_groups=[])
        print(get_access_level(new_access_level_id))

        event_id = add_access_schedule_event_to_access_level(
            new_access_level_id, weekday=WEEKDAY_FULL_ENUM["WEDNESDAY"],
            start_time="00:00", end_time="23:59")["access_schedule_event_id"]
        update_access_schedule_event_on_access_level(
            new_access_level_id, event_id, weekday=WEEKDAY_FULL_ENUM["THURSDAY"],
            start_time="12:00", end_time="22:00")
        print(get_access_schedule_event(new_access_level_id, event_id))
        delete_access_schedule_event_on_access_level(new_access_level_id, event_id)

        # Door exception calendars
        # A Friday at least 30 days out, so it matches the Friday-only recurrence
        exception_date = now + timedelta(days=30)
        exception_date += timedelta(days=(4 - exception_date.weekday()) % 7)
        door_exception = {
            "date": exception_date.strftime("%Y-%m-%d"),
            "door_status": "access_controlled",
            "start_time": "13:22",
            "end_time": "14:52",
            "recurrence_rule": {"frequency": "WEEKLY", "interval": 1,
                                "by_day": [WEEKDAY_FULL_ENUM["FRIDAY"]], "count": 4},
        }
        new_calendar_id = create_door_exception_calendar(
            name=f"Test Door Exception Calendar {generate_random_alphanumeric_string()}",
            doors=[door_id], exceptions=[door_exception])["calendar_id"]
        updated = update_door_exception_calendar(
            new_calendar_id,
            name=f"Updated Test Door Exception Calendar {generate_random_alphanumeric_string()}",
            doors=[door_id], exceptions=[door_exception])
        add_exception_to_door_exception_calendar(new_calendar_id, door_exception)

        exception_id = updated["exceptions"][0]["exception_id"]
        time.sleep(1)
        print(get_exception_on_door_exception_calendar(new_calendar_id, exception_id))
        update_exception_on_door_exception_calendar(new_calendar_id, exception_id,
                                                    {**door_exception, "end_time": "15:00"})
        print([c["name"] for c in get_all_door_exception_calendars(
            last_updated_after=now - timedelta(minutes=5))])
        delete_exception_on_door_exception_calendar(new_calendar_id, exception_id)
        delete_door_exception_calendar(new_calendar_id)
        new_calendar_id = None

        # Scenarios (read-only; activating would lock real doors)
        try:
            print("Scenarios:", [s["name"] for s in get_all_access_scenarios()])
        except VerkadaForbiddenError as e:
            print(f"Skipped scenarios: API key lacks access-site scope ({e.error_code})")

    finally:
        for label, cleanup, target in [
            ("user", lambda: delete_user(external_id=new_user_external_id), new_user_external_id),
            ("access group", lambda: delete_access_group(group_id), group_id),
            ("access level", lambda: delete_access_level(new_access_level_id), new_access_level_id),
            ("exception calendar", lambda: delete_door_exception_calendar(new_calendar_id),
             new_calendar_id),
        ]:
            if target:
                try:
                    cleanup()
                    print(f"Deleted {label} {target}")
                except Exception as e:
                    print(f"Failed to delete {label} {target}: {e}")

    cprint("Access Control Test Completed", "green")

# access_control_test()
