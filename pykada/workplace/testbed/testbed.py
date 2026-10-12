import os
from datetime import datetime, timedelta, timezone

from termcolor import cprint

from pykada.workplace import (create_guest_deny_list, delete_guest_deny_list,
                              get_all_approved_lists, get_all_guest_events,
                              get_all_guest_hosts, get_all_guest_types,
                              get_all_guest_visits, get_guest_sites)


def workplace_test():
    now = datetime.now(timezone.utc)
    one_month_ago = now - timedelta(days=30)

    guest_site_id = os.getenv("GUEST_SITE_ID", None)

    all_guest_sites = get_guest_sites()['guest_sites']
    if not guest_site_id:
        guest_site_id = all_guest_sites[0]['site_id']
    print(all_guest_sites)
    cprint("All guest sites retrieved successfully", "green")

    print(create_guest_deny_list(filename="../deny_list_example.csv", site_id=guest_site_id))
    delete_guest_deny_list(site_id=guest_site_id)
    cprint("Guest deny lists tested successfully", "green")

    # Spans 30 days; fetched internally as 24-hour windows
    visits = list(get_all_guest_visits(site_id=guest_site_id, start_time=one_month_ago,
                                       end_time=now))
    print(f"{len(visits)} visits in the last 30 days")

    print("Hosts:", [h["full_name"] for h in get_all_guest_hosts(guest_site_id)])
    print("Guest types:", [t["name"] for t in get_all_guest_types(guest_site_id)])
    print("Approved lists:", [lst["name"] for lst in get_all_approved_lists(guest_site_id)])
    print("Guest events:", list(get_all_guest_events(guest_site_id, start_time=now,
                                                     end_time=now + timedelta(days=30))))

    cprint("Workplace test successful", "green")


workplace_test()
