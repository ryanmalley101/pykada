import os
import time

from termcolor import cprint

from pykada.helpers import SENSOR_FIELD_ENUM
from pykada.sensors.sensors import get_all_sensor_data, get_all_sensor_alerts


def sensor_alert_data_test():
    """
    Test function to retrieve and print all sensor data.
    """
    # Define the time range for the query
    one_hour_ago = int(time.time()) - 3600
    one_month_ago = one_hour_ago - (30 * 24 * 60 * 60)  # 30 days in seconds

    sensor_id = os.getenv("SENSOR_ID", None)

    if not sensor_id:
        raise ValueError("SENSOR_ID environment variable is not set.")

    all_sensor_alerts = get_all_sensor_alerts(
        device_ids=[sensor_id],
        start_time=one_month_ago,
        end_time=one_hour_ago,
        fields=[SENSOR_FIELD_ENUM["TEMPERATURE"], SENSOR_FIELD_ENUM["HUMIDITY"]]
    )

    print([a for a in all_sensor_alerts])

    # Retrieve all sensor data
    all_sensor_data = get_all_sensor_data(
        device_id=sensor_id,
        start_time=one_month_ago,
        end_time=one_hour_ago,
        fields=[SENSOR_FIELD_ENUM["TEMPERATURE"],
                SENSOR_FIELD_ENUM["HUMIDITY"]],
        interval="5m"
    )

    # Print the retrieved sensor data
    print([a for a in all_sensor_data])

    cprint("All sensor data retrieved successfully", "green")


sensor_alert_data_test()