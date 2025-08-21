import os
import time

from termcolor import cprint

from pykada.workplace import get_guest_sites, create_guest_deny_list, \
    delete_guest_deny_list, get_all_guest_visits


def workplace_test():
    current_time = int(time.time())
    one_month_ago = current_time - (30 * 24 * 60 * 60)  # 30 days in seconds

    guest_site_id = os.getenv("GUEST_SITE_ID", None)

    all_guest_sites = get_guest_sites()['guest_sites']

    if not guest_site_id:
        guest_site_id = all_guest_sites[0]['site_id']

    print(all_guest_sites)

    cprint("All guest sites retrieved successfully", "green")

    create_deny_list_response = create_guest_deny_list(
        filename="../deny_list_example.csv",
        site_id=guest_site_id)

    print(create_deny_list_response)

    delete_guest_deny_list(site_id=guest_site_id)

    cprint("Guest deny lists tested successfully", "green")

    all_guest_visits = get_all_guest_visits(
        site_id=guest_site_id,
        start_time=one_month_ago,
        end_time=current_time
    )

    print(all_guest_visits)

    cprint("All guest sites and visits retrieved successfully", "green")



workplace_test()
