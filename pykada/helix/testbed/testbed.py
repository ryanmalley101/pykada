import os
import time
from pykada.helix.helix import (
    create_helix_event_type,
    get_helix_event_types,
    update_helix_event_type,
    delete_helix_event_type,
    create_helix_event,
    get_helix_event,
    update_helix_event,
    delete_helix_event
)
from pykada.helpers import generate_random_alphanumeric_string


def helix_testbed():
    """
    Testbed for performing full CRUD operations on Helix event types and events.
    """
    event_type_uid = None
    event = None
    camera_id = os.getenv("CAMERA_ID")
    time_ms = int(time.time() * 1000)

    try:
        # Create a Helix Event Type
        event_type = create_helix_event_type(
            event_schema={"item": "string", "price": "float"},
            name=f"Event {generate_random_alphanumeric_string(8)}"
        )
        print("Created Event Type:", event_type)
        event_type_uid = event_type["event_type_uid"]

        # Retrieve the created Event Type
        retrieved_event_type = get_helix_event_types(event_type_uid=event_type_uid)
        print("Retrieved Event Type:", retrieved_event_type)

        # Update the Event Type
        updated_event_type = update_helix_event_type(
            event_type_uid=event_type_uid,
            event_schema={"item": "string", "price": "float", "quantity": "integer"},
            name=f"New Event {generate_random_alphanumeric_string(8)}"
        )
        print("Updated Event Type:", updated_event_type)

        # Create a Helix Event
        event = create_helix_event(
            camera_id=camera_id,
            event_type_uid=event_type_uid,
            time_ms=time_ms,
            flagged=True,
            attributes={"item": "Test Item", "price": 19.99}
        )
        print("Created Event:", event)
        # event_uid = event["event_uid"]

        # Retrieve the created Event
        retrieved_event = get_helix_event(
            camera_id=camera_id,
            time_ms=time_ms,
            event_type_uid=event_type_uid
        )
        print("Retrieved Event:", retrieved_event)

        # Update the Event
        updated_event = update_helix_event(
            camera_id=camera_id,
            time_ms=time_ms,
            event_type_uid=event_type_uid,
            flagged=False,
            extra_attributes={"quantity": 5}
        )
        print("Updated Event:", updated_event)

    finally:
        # Clean up: Delete the Helix Event
        if event:
            try:
                deleted_event = delete_helix_event(
                    camera_id=camera_id,
                    time_ms=time_ms,
                    event_type_uid=event_type_uid
                )
                print("Deleted Event:", deleted_event)
            except Exception as e:
                print(f"Failed to delete event: {e}")

        # Clean up: Delete the Helix Event Type
        if event_type_uid:
            try:
                deleted_event_type = delete_helix_event_type(event_type_uid=event_type_uid)
                print("Deleted Event Type:", deleted_event_type)
            except Exception as e:
                print(f"Failed to delete event type: {e}")

    print("Helix Testbed completed successfully.")

helix_testbed()