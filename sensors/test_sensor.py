import time
import os
from sensors import *
import unittest


class TestSensorRequests(unittest.TestCase):

    def test_get_sensor_data(self):
        sensor_id = os.getenv("SENSOR_ID", None)

        self.assertTrue(sensor_id)

        timestamp = int(time.time())

        sensor_data = get_sensor_data(device_id=sensor_id,
                        start_time=timestamp-3600,
                        end_time=timestamp,
                        page_size=5,
                        page_token='0',
                        fields=[SENSOR_FIELD_ENUM['TEMPERATURE'],
                                SENSOR_FIELD_ENUM['HUMIDITY']],
                        interval='1m'
                        )

        self.assertTrue(sensor_data['data'])

    def test_get_sensor_alerts(self):
        sensor_id = os.getenv("SENSOR_ID", None)

        self.assertTrue(sensor_id)

        timestamp = int(time.time())

        sensor_alerts = get_sensor_alerts(device_ids=[sensor_id],
                                      start_time=timestamp - 3600,
                                      end_time=timestamp,
                                      page_size=5,
                                      page_token='0',
                                      fields=[SENSOR_FIELD_ENUM['TEMPERATURE'],
                                              SENSOR_FIELD_ENUM['HUMIDITY']])

        # You might not have alerts, so the best thing we can test for is
        # whether the request succeeds in the first place and has an attribute
        # `alert_events`
        self.assertIsInstance(sensor_alerts['alert_events'], list)

if __name__ == '__main__':
    unittest.main()