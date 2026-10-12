import os
import time

from pykada.helix import (
    create_helix_event,
    create_helix_event_type,
    create_helix_events_batch,
    delete_helix_event,
    delete_helix_event_type,
    get_batch_job_status,
    get_helix_event,
    get_helix_event_types,
    update_helix_event,
    update_helix_event_type,
)
from pykada.helpers import generate_random_alphanumeric_string


def helix_testbed():
    """
    Testbed for full CRUD on Helix event types and events, plus a batch create.

    Field names are suffixed with a random string: Helix requires a field name
    to have the same type across every schema in the org, so a fixed name like
    "price" can collide with an existing event type.
    """
    event_type_uid = None
    created_times = []
    camera_id = os.getenv("CAMERA_ID")
    time_ms = int(time.time() * 1000)
    suffix = generate_random_alphanumeric_string(6).lower()
    item, price, quantity = f"item_{suffix}", f"price_{suffix}", f"quantity_{suffix}"

    try:
        event_type = create_helix_event_type(
            event_schema={item: "string", price: "float"},
            name=f"Event {generate_random_alphanumeric_string(8)}"
        )
        print("Created Event Type:", event_type)
        event_type_uid = event_type["event_type_uid"]

        print("Retrieved Event Type:", get_helix_event_types(event_type_uid=event_type_uid))

        print("Updated Event Type:", update_helix_event_type(
            event_type_uid=event_type_uid,
            event_schema={item: "string", price: "float", quantity: "integer"},
            name=f"New Event {generate_random_alphanumeric_string(8)}"
        ))

        print("Created Event:", create_helix_event(
            camera_id=camera_id, event_type_uid=event_type_uid, time_ms=time_ms,
            flagged=True, attributes={item: "Test Item", price: 19.99}))
        created_times.append(time_ms)

        print("Retrieved Event:", get_helix_event(
            camera_id=camera_id, time_ms=time_ms, event_type_uid=event_type_uid))

        print("Updated Event:", update_helix_event(
            camera_id=camera_id, time_ms=time_ms, event_type_uid=event_type_uid,
            flagged=False, extra_attributes={quantity: 5}))

        # Batch create (v1) and poll the job (v2 /batch/jobs)
        batch_times = [time_ms - 1000 * (i + 1) for i in range(3)]
        job = create_helix_events_batch([
            {"camera_id": camera_id, "event_type_uid": event_type_uid, "time_ms": t,
             "attributes": {item: f"Batch {i}", price: 1.5 * i}}
            for i, t in enumerate(batch_times)
        ])
        created_times.extend(batch_times)
        print("Batch Job:", job)
        status = {}
        for _ in range(15):
            status = get_batch_job_status(job["job_id"])
            if status["status"] in ("completed", "failed"):
                break
            time.sleep(2)
        print("Batch Job Status:", status)

    finally:
        for t in created_times:
            try:
                delete_helix_event(camera_id=camera_id, time_ms=t, event_type_uid=event_type_uid)
                print(f"Deleted Event at {t}")
            except Exception as e:
                print(f"Failed to delete event at {t}: {e}")

        if event_type_uid:
            try:
                print("Deleted Event Type:", delete_helix_event_type(event_type_uid=event_type_uid))
            except Exception as e:
                print(f"Failed to delete event type: {e}")

    print("Helix Testbed completed successfully.")


helix_testbed()
