import os
import time
import uuid

from termcolor import cprint

from pykada.access_control import add_card_to_user, \
    activate_access_card, deactivate_access_card, \
    delete_license_plate_from_user, add_license_plate_to_user, \
    activate_license_plate, deactivate_license_plate, \
    delete_mfa_code_from_user, add_mfa_code_to_user, \
    get_all_door_exception_calendars, create_door_exception_calendar, \
    update_door_exception_calendar, delete_door_exception_calendar, \
    get_exception_on_door_exception_calendar, \
    add_exception_to_door_exception_calendar, \
    update_exception_on_door_exception_calendar, \
    delete_exception_on_door_exception_calendar, get_doors, get_access_groups, \
    delete_access_group, get_access_group, create_access_group, \
    add_user_to_access_group, get_all_access_levels, get_access_level, \
    create_access_level, update_access_level, delete_access_level, \
    add_access_schedule_event_to_access_level, \
    update_access_schedule_event_on_access_level, \
    delete_access_schedule_event_on_access_level, get_all_access_users, \
    activate_ble_for_access_user, set_end_date_for_user, \
    set_entry_code_for_user, send_pass_app_invite_for_user, \
    upload_profile_photo, activate_remote_unlock_for_user, \
    set_start_date_for_user
from pykada.core_command import create_user, delete_user
from pykada.helpers import generate_random_alphanumeric_string, \
    generate_random_numeric_string
from pykada.enums import WEEKDAY_ENUM, VALID_CARD_TYPES_ENUM

current_time = int(time.time())
one_hour_from_now = current_time + 3600
#
# def generate_random_recurrence_rule() -> dict:
#     """
#     Generate a random recurrence rule using the provided enums.
#     """
#     frequency = random.choice(list(FREQUENCY_ENUM.values()))
#     recurrence_rule = {
#         "frequency": frequency,
#         "interval": random.randint(1, 10),
#         "start_time": f"{random.randint(0, 23):02}:{random.randint(0, 59):02}"
#     }
#
#     if frequency in (FREQUENCY_ENUM["WEEKLY"], FREQUENCY_ENUM["MONTHLY"], FREQUENCY_ENUM["YEARLY"]):
#         recurrence_rule["by_day"] = random.sample(list(WEEKDAY_ENUM.values()), random.randint(1, 3))
#
#     if frequency == FREQUENCY_ENUM["YEARLY"]:
#         recurrence_rule["by_month"] = random.randint(1, 12)
#
#     if frequency in (FREQUENCY_ENUM["MONTHLY"], FREQUENCY_ENUM["YEARLY"]):
#         if random.choice([True, False]):
#             recurrence_rule["by_month_day"] = random.randint(1, 31)
#         else:
#             recurrence_rule["by_set_pos"] = random.randint(1, 5)
#
#     if random.choice([True, False]):
#         recurrence_rule["excluded_dates"] = [
#             (datetime.datetime.now() + datetime.timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d")
#             for _ in range(random.randint(1, 3))
#         ]
#
#     if random.choice([True, False]):
#         recurrence_rule["until"] = (datetime.datetime.now() + datetime.timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d")
#     else:
#         recurrence_rule["count"] = random.randint(1, 100)
#
#     return recurrence_rule
#
#
# def generate_random_door_exception(group_id:str) -> dict:
#     """
#     Generate a random door exception using the provided enums.
#     """
#     door_status = random.choice(list(DOOR_STATUS_ENUM.values()))
#     exception = {
#         "date": (datetime.datetime.now() + datetime.timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d"),
#         "door_status": door_status,
#         "all_day_default": random.choice([True, False])
#     }
#
#     if not exception["all_day_default"]:
#         exception["start_time"] = f"{random.randint(0, 23):02}:{random.randint(0, 59):02}"
#         exception["end_time"] = f"{random.randint(0, 23):02}:{random.randint(0, 59):02}"
#
#     if random.choice([True, False]):
#         exception["double_badge"] = True
#         exception["double_badge_group_ids"] = [group_id]
#
#     if random.choice([True, False]):
#         exception["first_person_in"] = True
#         exception["first_person_in_group_ids"] = [group_id]
#
#     # if random.choice([True, False]):
#     #     exception["recurrence_rule"] = generate_random_recurrence_rule()
#
#     return exception

def access_control_test():
    """
    Test various access control functionalities.
    """
    door_id = os.getenv("DOOR_ID", None)

    new_user_external_id = generate_random_alphanumeric_string()  # Replace with a valid external ID

    group_id = None

    new_user_id = None

    new_access_level_id = None

    new_door_exception_calendar_id = None

    # Example usage of the create_user function
    new_user = create_user(external_id=new_user_external_id,
                           company_name="ACME Corp",
                           department="Engineering",
                           department_id="12345",
                           email=f"{new_user_external_id}@example.com",
                           employee_id="E12345",
                           employee_type="full-time",
                           employee_title="Software Engineer",
                           first_name="John",
                           middle_name="A",
                           last_name="Doe",
                           )
    print("New User:", new_user)

    new_user_id = new_user["user_id"]

    time.sleep(5)  # Wait for the user to be created

    all_access_user_info = get_all_access_users()["access_members"]


    try:
        external_ids = [user['external_id'] for user in all_access_user_info]
        print(list(external_ids))

        if new_user_external_id not in external_ids:
            raise ValueError(f"User with external ID {new_user_external_id} "
                             f"not found in access users information. "
                             f"Creation of the user likely failed")

        activate_ble_for_access_user(external_id=new_user_external_id,)

        set_entry_code_for_user(external_id=new_user_external_id,
                                entry_code=generate_random_numeric_string(),
                                override=True)

        set_start_date_for_user(external_id=new_user_external_id,
                                start_date=str(current_time))

        set_end_date_for_user(external_id=new_user_external_id,
                              end_date=str(one_hour_from_now))

        activate_remote_unlock_for_user(external_id=new_user_external_id)

        upload_profile_photo(external_id=new_user_external_id,
                             photo_path="Cary-Grant.png",
                             overwrite=True)

        send_pass_app_invite_for_user(external_id=new_user_external_id)

        # Test Credentials

        card_info = add_card_to_user(external_id=new_user_external_id,
                                     card_number=generate_random_numeric_string(length=4),
                                     facility_code=generate_random_numeric_string(length=2),
                                     card_type=VALID_CARD_TYPES_ENUM["STANDARD_26_BIT_WIEGAND"],
                                     active=True)

        card_id = card_info["card_id"]

        deactivate_access_card(external_id=new_user_external_id,
                               card_id=card_id)

        activate_access_card(external_id=new_user_external_id,
                             card_id=card_id)

        license_plate_number = generate_random_alphanumeric_string(length=6).upper()

        add_license_plate_to_user(external_id=new_user_external_id,
                                  license_plate_number=license_plate_number,
                                  name="John's License Plate",
                                  active=True)

        deactivate_license_plate(external_id=new_user_external_id,
                                 license_plate_number=license_plate_number)

        activate_license_plate(external_id=new_user_external_id,
                               license_plate_number=license_plate_number)
        time.sleep(3)
        delete_license_plate_from_user(external_id=new_user_external_id,
                                       license_plate_number=license_plate_number)

        mfa_code = generate_random_numeric_string(length=6)

        add_mfa_code_to_user(external_id=new_user_external_id,
                             code=mfa_code)

        delete_mfa_code_from_user(external_id=new_user_external_id,
                                  code=mfa_code)

        group_info = create_access_group(f"Test Group {generate_random_alphanumeric_string()}")

        group_id = group_info["group_id"]

        access_groups = get_access_groups()['access_groups']

        group_ids = [group['group_id'] for group in access_groups]

        if group_id not in group_ids:
            raise ValueError(f"Group with ID {group_id} not found in access groups information. "
                             f"Creation of the group likely failed")

        add_user_to_access_group(external_id=new_user_external_id,
                                 group_id=group_id)

        time.sleep(2)  # Wait for the user to be added to the group

        access_group_info = get_access_group(group_id=group_id)

        print(access_group_info)

        if new_user_id not in access_group_info['user_ids']:
            raise ValueError(f"User with ID {new_user_id} "
                             f"not found in access group information: {access_group_info} "
                             f"Addition of the user to the group likely failed")

        doors_in_org = get_doors()['doors']

        print(doors_in_org)

        if not door_id:
            api_enabled_doors = [door for door in doors_in_org if door['api_control_enabled']]
            if len(api_enabled_doors) == 0:
                raise ValueError("No API-enabled doors found in the organization.")
            door_info = api_enabled_doors[0]
            door_id = api_enabled_doors[0]['door_id']
        else:
            matching_doors = [door for door in doors_in_org if door['door_id'] == door_id]
            if len(matching_doors) == 0:
                raise ValueError(f"Door with ID {door_id} not found in the organization.")
            door_info = matching_doors[0]

            if door_info['api_control_enabled'] is False:
                raise ValueError(f"Door with ID {door_id} is not API-enabled.")

        print("DOOR INFO")
        print(door_info)
        door_name = door_info['site']['name']
        door_site_id = door_info['site']['site_id']

        print(door_info)

        new_uuid = uuid.uuid4()

        def generate_access_schedule_event(weekday, start_time="00:00", end_time="23:59"):
            return {
                # "access_schedule_event_id": str(new_uuid),
                "door_status": "access_granted",
                "start_time": start_time,
                "end_time": end_time,
                "weekday": weekday
            }

        # new_access_level = create_access_level(
        #     name=f"Test Access Level {generate_random_alphanumeric_string()}",
        #     doors=[door_id],
        #     sites=[door_site_id],
        #     access_groups=[group_id],
        #     access_schedule_events=[generate_access_schedule_event(w) for w in WEEKDAY_ENUM.values()],
        # )

        new_access_level = create_access_level(
            name=f"Test Access Level {generate_random_alphanumeric_string(length=4)}",
            doors=[],
            sites=[door_site_id],
            access_groups=[group_id],
            access_schedule_events=[],
        )

        new_access_level_id = new_access_level["access_level_id"]

        all_access_levels = get_all_access_levels()["access_levels"]

        if new_access_level_id not in [level['access_level_id'] for level in all_access_levels]:
            raise ValueError(f"Access Level with ID {new_access_level_id} "
                             f"not found in access levels information. "
                             f"Creation of the access level likely failed")

        new_access_level_info = get_access_level(access_level_id=new_access_level_id)

        print(new_access_level_info)

        update_access_level(access_level_id=new_access_level_id,
                            name=f"Updated Test Access Level {generate_random_alphanumeric_string(length=4)}",
                            doors=[],
                            sites=[door_site_id],
                            access_groups=[],
                            access_schedule_events=[],
                            )

        updated_access_level_info = get_access_level(access_level_id=new_access_level_id)

        print(updated_access_level_info)

        added_schedule_event = add_access_schedule_event_to_access_level(
            access_level_id=new_access_level_id,
            start_time="00:00",
            end_time="23:59",
            weekday=WEEKDAY_ENUM["WEDNESDAY"],
        )

        added_schedule_event_id = added_schedule_event["access_schedule_event_id"]

        updated_access_schedule_event = update_access_schedule_event_on_access_level(
            access_level_id=new_access_level_id,
            event_id=added_schedule_event_id,
            start_time="12:00",
            end_time="22:00",
            weekday=WEEKDAY_ENUM["THURSDAY"],
        )

        deleted_schedule_event = delete_access_schedule_event_on_access_level(
            access_level_id=new_access_level_id,
            event_id=added_schedule_event_id,
        )

        # Create a door exception
        door_exception = {
            "date": "2026-07-02",
            "door_status": "access_controlled",
            "start_time": "13:22",
            "end_time": "14:52"
        }

        # Test door exception calendars
        new_door_exception_calendar = create_door_exception_calendar(
            doors=[door_id],
            name=f"Test Door Exception Calendar {generate_random_alphanumeric_string()}",
            exceptions=[door_exception],
        )

        new_door_exception_calendar_id = new_door_exception_calendar[
            "door_exception_calendar_id"]

        updated_door_exception_calendar = update_door_exception_calendar(
            calendar_id=new_door_exception_calendar_id,
            name=f"Updated Test Door Exception Calendar {generate_random_alphanumeric_string()}",
            doors=[door_id],
            exceptions=[door_exception],
        )

        add_exception_to_door_exception_calendar(
            calendar_id=new_door_exception_calendar_id,
            exception=door_exception,
        )

        new_door_exception_calendar_id = updated_door_exception_calendar[
            "door_exception_calendar_id"]
        exception_id = updated_door_exception_calendar["exceptions"][0][
            "door_exception_id"]

        time.sleep(1)

        print(get_exception_on_door_exception_calendar(
            calendar_id=new_door_exception_calendar_id,
            exception_id=exception_id))

        updated_door_exception = update_exception_on_door_exception_calendar(
            calendar_id=new_door_exception_calendar_id,
            exception_id=exception_id,
            exception=door_exception,
        )

        get_exception_on_door_exception_calendar(
            calendar_id=new_door_exception_calendar_id,
            exception_id=exception_id,
        )

        get_all_door_exception_calendars()

        delete_exception_on_door_exception_calendar(
            calendar_id=new_door_exception_calendar_id,
            exception_id=exception_id,
        )

        delete_door_exception_calendar(
            calendar_id=new_door_exception_calendar_id,
        )

        new_door_exception_calendar_id = None

    finally:
        # Clean up: delete the user
        if new_user_external_id:
            try:
                deleted_user = delete_user(external_id=new_user_external_id)
                print("Deleted User:", deleted_user)
            except Exception as e:
                print(f"Failed to delete user: {e}")

        # Clean up: delete the access group
        if group_id:
            try:
                deleted_group = delete_access_group(group_id=group_id)
                print("Deleted Group:", deleted_group)
            except Exception as e:
                print(f"Failed to delete group: {e}")

        # Clean up: delete the access level
        if new_access_level_id:
            try:
                deleted_access_level = delete_access_level(
                    access_level_id=new_access_level_id)
                print("Deleted Access Level:", deleted_access_level)
            except Exception as e:
                print(f"Failed to delete access level: {e}")

        # Clean up: delete the door exception calendar
        if new_door_exception_calendar_id:
            try:
                deleted_calendar = delete_door_exception_calendar(
                    calendar_id=new_door_exception_calendar_id)
                print("Deleted Door Exception Calendar:", deleted_calendar)
            except Exception as e:
                print(f"Failed to delete door exception calendar: {e}")

    cprint("Access Control Test Completed", "green")

# access_control_test()
