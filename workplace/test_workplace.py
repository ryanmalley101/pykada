import unittest
from workplace import *

class TestWorkplaceRequests(unittest.TestCase):
    def test_get_guest_sites(self):
        self.assertIsInstance(get_guest_sites()['devices'], list)
    #
    # def test_create_destroy_deny_list(self):
    #
