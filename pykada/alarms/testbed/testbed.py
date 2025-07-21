import os

from pykada.alarms.classic_alarms import get_alarm_devices, get_alarm_site_information

alarms_site_id = os.getenv("CLASSIC_ALARMS_SITE_ID")

def classic_alarms_test():

    alarm_sites_info = get_alarm_site_information()["sites"]

    if len(alarm_sites_info) > 0:
        get_alarm_devices(site_id=alarm_sites_info[0]["site_id"])


    print("Classic Alarms test completed successfully.")

classic_alarms_test()