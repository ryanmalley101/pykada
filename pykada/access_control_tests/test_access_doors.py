import types
from unittest.mock import patch

import pytest

from pykada.access_control import (
    get_all_doors,
    get_doors,
    unlock_door_as_admin,
    unlock_door_as_user,
)
from pykada.endpoints import (
    ACCESS_ADMIN_UNLOCK_ENDPOINT,
    ACCESS_USER_UNLOCK_ENDPOINT,
    V2_ACCESS_DOORS_ENDPOINT as DOORS,
)

RM = "pykada.verkada_requests.VerkadaRequestManager"


@pytest.mark.parametrize("func, kwargs, method, url, request_kwargs", [
    (get_doors, {}, "get", DOORS, {"params": {}}),
    (get_doors, {"door_ids": ["d1", "d2"], "limit": 1000}, "get", DOORS,
     {"params": {"door_ids": "d1,d2", "limit": 1000}}),
    (get_doors, {"site_ids": ["s1"], "cursor": "c"}, "get", DOORS,
     {"params": {"site_ids": "s1", "cursor": "c"}}),
    (unlock_door_as_admin, {"door_id": "d1"}, "post", ACCESS_ADMIN_UNLOCK_ENDPOINT,
     {"payload": {"door_id": "d1"}}),
    (unlock_door_as_user, {"door_id": "d1", "user_id": "u1"}, "post",
     ACCESS_USER_UNLOCK_ENDPOINT, {"payload": {"user_id": "u1", "door_id": "d1"}}),
    (unlock_door_as_user, {"door_id": "d1", "external_id": "e1"}, "post",
     ACCESS_USER_UNLOCK_ENDPOINT, {"payload": {"external_id": "e1", "door_id": "d1"}}),
])
def test_request_shape(func, kwargs, method, url, request_kwargs):
    with patch(f"{RM}.{method}", return_value={"ok": True}) as mock:
        assert func(**kwargs) == {"ok": True}
    mock.assert_called_once_with(url, **request_kwargs)


@patch(f"{RM}.get")
def test_get_all_doors_walks_pages(mock_get):
    mock_get.side_effect = [{"items": [{"door_id": "a"}], "cursor": "c1"},
                            {"items": [{"door_id": "b"}], "cursor": None}]
    result = get_all_doors(site_ids=["s1"])
    assert isinstance(result, types.GeneratorType)
    assert [d["door_id"] for d in result] == ["a", "b"]
    assert mock_get.call_args_list[1].kwargs["params"] == {
        "site_ids": "s1", "limit": 100, "cursor": "c1"}


@pytest.mark.parametrize("call, match", [
    (lambda: get_doors(door_ids=["d1"], site_ids=["s1"]), "Only one"),
    (lambda: get_all_doors(door_ids=["d1"], site_ids=["s1"]), "Only one"),
    (lambda: get_doors(limit=1001), "between 1 and 1000"),
    (lambda: unlock_door_as_admin(""), "door_id"),
    (lambda: unlock_door_as_user("d1"), "Exactly one"),
    (lambda: unlock_door_as_user("", user_id="u1"), "door_id"),
])
def test_validation(call, match):
    with pytest.raises(ValueError, match=match):
        call()
