from pykada.endpoints import VIEWING_STATION_ENDPOINT
from pykada.verkada_requests import *


def get_viewing_stations():
    """
    Returns a list of viewing stations in an organization.

    :return: A list of viewing stations within the organization
    :rtype: dict
    """
    return get_request(f"{VIEWING_STATION_ENDPOINT}")

