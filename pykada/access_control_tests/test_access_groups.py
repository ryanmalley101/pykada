import types
from unittest.mock import patch

import pytest
from typeguard import TypeCheckError

from pykada.access_control import (
    add_user_to_access_group,
    create_access_group,
    delete_access_group,
    get_access_group,
    get_access_groups,
    get_all_access_groups,
    remove_user_from_access_group,
)
from pykada.endpoints import V2_ACCESS_GROUPS_ENDPOINT as GROUPS

RM = "pykada.verkada_requests.VerkadaRequestManager"


@pytest.mark.parametrize("func, kwargs, method, url, request_kwargs", [
    (get_access_groups, {}, "get", GROUPS, {"params": {}}),
    (get_access_groups, {"limit": 1000, "cursor": "c"}, "get", GROUPS,
     {"params": {"limit": 1000, "cursor": "c"}}),
    (get_access_group, {"group_id": "g1"}, "get", f"{GROUPS}/g1", {}),
    (create_access_group, {"name": "Night Shift"}, "post", GROUPS,
     {"payload": {"name": "Night Shift"}}),
    (delete_access_group, {"group_id": "g1"}, "delete", f"{GROUPS}/g1", {}),
    (add_user_to_access_group, {"group_id": "g1", "user_id": "u1"}, "put",
     f"{GROUPS}/g1/users/u1", {}),
    (remove_user_from_access_group, {"group_id": "g1", "user_id": "u1"}, "delete",
     f"{GROUPS}/g1/users/u1", {}),
])
def test_request_shape(func, kwargs, method, url, request_kwargs):
    with patch(f"{RM}.{method}", return_value={"ok": True}) as mock:
        assert func(**kwargs) == {"ok": True}
    mock.assert_called_once_with(url, **request_kwargs)


@patch(f"{RM}.get")
def test_get_all_access_groups_walks_pages(mock_get):
    mock_get.side_effect = [{"items": [{"group_id": "a"}], "cursor": "c1"},
                            {"items": [{"group_id": "b"}], "cursor": None}]
    result = get_all_access_groups()
    assert isinstance(result, types.GeneratorType)
    assert [g["group_id"] for g in result] == ["a", "b"]


@pytest.mark.parametrize("call, match", [
    (lambda: get_access_group(""), "group_id"),
    (lambda: delete_access_group(" "), "group_id"),
    (lambda: create_access_group(""), "name"),
    (lambda: create_access_group("x" * 256), "255"),
    (lambda: add_user_to_access_group("g1", ""), "user_id"),
    (lambda: remove_user_from_access_group("", "u1"), "group_id"),
    (lambda: get_access_groups(limit=0), "between 1 and 1000"),
])
def test_validation(call, match):
    with pytest.raises(ValueError, match=match):
        call()


def test_add_user_requires_user_id_not_external_id():
    with pytest.raises(TypeError):
        add_user_to_access_group("g1", external_id="e1")


def test_type_errors():
    with pytest.raises(TypeCheckError):
        create_access_group(123)
