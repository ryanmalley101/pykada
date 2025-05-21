import pytest
from unittest.mock import patch
from viewing_stations import *  # Replace with actual module name

@patch("viewing_stations.get_request")
def test_get_viewing_stations_returns_dict(mock_get):
    mock_get.return_value = {"viewing_stations": []}
    result = get_viewing_stations()
    assert isinstance(result, dict)
    mock_get.assert_called_once()
