import types
from unittest.mock import patch

import pytest

from pykada.access_control import (
    activate_access_scenario,
    get_access_scenarios,
    get_all_access_scenarios,
    release_access_scenario,
)
from pykada.endpoints import V2_ACCESS_SCENARIOS_ENDPOINT as SCENARIOS

RM = "pykada.verkada_requests.VerkadaRequestManager"


@pytest.mark.parametrize("func, kwargs, method, url, request_kwargs", [
    (get_access_scenarios, {}, "get", SCENARIOS, {"params": {}}),
    (get_access_scenarios, {"scenario_ids": ["sc1", "sc2"], "site_ids": ["s1"],
                            "scenario_types": ["LOCKDOWN"], "limit": 10},
     "get", SCENARIOS,
     {"params": {"scenario_ids": ["sc1", "sc2"], "site_ids": ["s1"],
                 "scenario_types": ["LOCKDOWN"], "limit": 10}}),
    (get_access_scenarios, {"scenario_ids": []}, "get", SCENARIOS, {"params": {}}),
    (activate_access_scenario, {"scenario_id": "sc1"}, "post",
     f"{SCENARIOS}/sc1/activate", {}),
    (release_access_scenario, {"scenario_id": "sc1"}, "post",
     f"{SCENARIOS}/sc1/release", {}),
])
def test_request_shape(func, kwargs, method, url, request_kwargs):
    with patch(f"{RM}.{method}", return_value={"ok": True}) as mock:
        assert func(**kwargs) == {"ok": True}
    mock.assert_called_once_with(url, **request_kwargs)


@patch(f"{RM}.get")
def test_get_all_access_scenarios_walks_pages(mock_get):
    mock_get.side_effect = [{"items": [{"scenario_id": "a"}], "cursor": "c1"},
                            {"items": [{"scenario_id": "b"}], "cursor": None}]
    result = get_all_access_scenarios(scenario_types=["EVACUATE"])
    assert isinstance(result, types.GeneratorType)
    assert [s["scenario_id"] for s in result] == ["a", "b"]
    assert mock_get.call_args_list[1].kwargs["params"]["scenario_types"] == ["EVACUATE"]


@pytest.mark.parametrize("call, match", [
    (lambda: activate_access_scenario(""), "scenario_id"),
    (lambda: release_access_scenario(" "), "scenario_id"),
    (lambda: get_access_scenarios(limit=0), "between 1 and 1000"),
])
def test_validation(call, match):
    with pytest.raises(ValueError, match=match):
        call()


def test_deprecated_types_param_removed():
    with pytest.raises(TypeError):
        get_access_scenarios(types=["LOCKDOWN"])
