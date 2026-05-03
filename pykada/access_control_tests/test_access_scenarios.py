import pytest
from unittest.mock import patch

from pykada.endpoints import ACCESS_SCENARIOS_ENDPOINT
from pykada.access_control import (
    get_access_scenarios,
    activate_access_scenario,
    release_access_scenario,
)


# ——— get_access_scenarios ——— #

@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"scenarios": []})
def test_get_access_scenarios_no_filters(mock_get):
    result = get_access_scenarios()
    assert isinstance(result, dict)
    mock_get.assert_called_once_with(ACCESS_SCENARIOS_ENDPOINT, params={})


@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"scenarios": []})
def test_get_access_scenarios_with_scenario_ids(mock_get):
    result = get_access_scenarios(scenario_ids=["s1", "s2"])
    assert isinstance(result, dict)
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["scenario_ids"] == "s1,s2"


@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"scenarios": []})
def test_get_access_scenarios_with_site_ids(mock_get):
    result = get_access_scenarios(site_ids=["site1"])
    assert isinstance(result, dict)
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["site_ids"] == "site1"


@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"scenarios": []})
def test_get_access_scenarios_with_types(mock_get):
    result = get_access_scenarios(types=["lockdown", "unlock"])
    assert isinstance(result, dict)
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["types"] == "lockdown,unlock"


# ——— activate_access_scenario ——— #

@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"activated": True})
def test_activate_access_scenario_success(mock_post):
    result = activate_access_scenario("scen1")
    assert isinstance(result, dict)
    expected_url = f"{ACCESS_SCENARIOS_ENDPOINT}/scen1/activate"
    mock_post.assert_called_once_with(expected_url)


def test_activate_access_scenario_empty_id_raises():
    with pytest.raises(ValueError, match="scenario_id"):
        activate_access_scenario("")


# ——— release_access_scenario ——— #

@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"released": True})
def test_release_access_scenario_success(mock_post):
    result = release_access_scenario("scen1")
    assert isinstance(result, dict)
    expected_url = f"{ACCESS_SCENARIOS_ENDPOINT}/scen1/release"
    mock_post.assert_called_once_with(expected_url)


def test_release_access_scenario_empty_id_raises():
    with pytest.raises(ValueError, match="scenario_id"):
        release_access_scenario("")
