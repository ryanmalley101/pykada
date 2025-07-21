from termcolor import cprint

from pykada.viewing_stations.viewing_stations import get_viewing_stations


def get_viewing_stations_test():

    get_viewing_stations()

    cprint("get_viewing_stations test completed successfully", "green")

get_viewing_stations_test()