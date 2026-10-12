from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from termcolor import cprint

from pykada.enums import EVENT_PRODUCT_TYPES_ENUM
from pykada.events import get_all_events

load_dotenv()  # the repo's .env; variables already in the shell win


def events_test():
    """
    Fetch the last two hours of events, one product at a time, then all at once.
    """
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=2)

    for product in EVENT_PRODUCT_TYPES_ENUM.values():
        events = list(get_all_events(start_time=start_time, end_time=end_time,
                                     product_types=[product]))
        assert all(e["device_type"] == product for e in events), product
        print(f"{product}: {len(events)} events")

    all_events = list(get_all_events(start_time=start_time, end_time=end_time))
    print(f"all products: {len(all_events)} events")

    motion = list(get_all_events(start_time=start_time, end_time=end_time,
                                 product_types=["camera"], event_types=["motion"]))
    assert all(e["event_type"] == "motion" for e in motion)
    print(f"camera motion: {len(motion)} events")

    cprint("Events test successful", "green")


events_test()
