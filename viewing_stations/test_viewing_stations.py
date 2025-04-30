
import unittest

from viewing_stations import get_viewing_stations


class TestViewingStationRequests(unittest.TestCase):

    def test_get_viewing_stations(self):
        self.assertIsInstance(get_viewing_stations()['devices'], list)

if __name__ == '__main__':
    unittest.main()