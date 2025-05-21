import pytest
from typeguard import TypeCheckError
from unittest.mock import patch

import access_groups as ag
from access_groups import (
    get_access_groups,
    delete_access_group,
    get_access_group,
    create_access_group,
    add_user_to_access_group,
    remove_user_from_access_group
)


# --- get_access_groups --- #

@patch("access_groups.get_request", return_value={"groups": []})
def test_get_access_groups_returns_dict(mock_get):
    result = get_access_groups()
    mock_get.assert_called_once_with(ag.ACCESS_GROUPS_ENDPOINT)
    assert isinstance(result, dict)
    assert result == {"groups": []}


# --- delete_access_group --- #

def test_delete_access_group_empty_id_raises_value_error():
    with pytest.raises(ValueError):
        delete_access_group("")

def test_delete_access_group_none_id_raises_type_error():
    with pytest.raises(TypeCheckError):
        delete_access_group(None)

@patch("access_groups.delete_request", return_value={"deleted": True})
def test_delete_access_group_success(mock_delete):
    result = delete_access_group("group1")
    mock_delete.assert_called_once_with(
        ag.ACCESS_GROUP_ENDPOINT,
        params={"group_id": "group1"}
    )
    assert result == {"deleted": True}


# --- get_access_group --- #

def test_get_access_group_empty_id_raises_value_error():
    with pytest.raises(ValueError):
        get_access_group("")

def test_get_access_group_none_id_raises_type_error():
    with pytest.raises(TypeCheckError):
        get_access_group(None)

@patch("access_groups.get_request", return_value={"group": {"id": "group1"}})
def test_get_access_group_success(mock_get):
    result = get_access_group("group1")
    mock_get.assert_called_once_with(
        ag.ACCESS_GROUP_ENDPOINT,
        params={"group_id": "group1"}
    )
    assert result == {"group": {"id": "group1"}}


# --- create_access_group --- #

def test_create_access_group_empty_name_raises_value_error():
    with pytest.raises(ValueError):
        create_access_group("")

def test_create_access_group_none_name_raises_type_error():
    with pytest.raises(TypeCheckError):
        create_access_group(None)

@patch("access_groups.post_request", return_value={"created": {"id": "newgroup"}})
def test_create_access_group_success(mock_post):
    result = create_access_group("My Group")
    mock_post.assert_called_once_with(
        ag.ACCESS_GROUP_ENDPOINT,
        payload={"name": "My Group"}
    )
    assert result == {"created": {"id": "newgroup"}}


# --- add_user_to_access_group --- #

@pytest.mark.parametrize("group_id, user_id, external_id", [
    ("", "u1", None),
    ("g1", None, None),
    ("g1", "u1", "e1"),
])
def test_add_user_to_access_group_value_errors(group_id, user_id, external_id):
    with pytest.raises(ValueError):
        add_user_to_access_group(group_id, external_id=external_id, user_id=user_id)

def test_add_user_to_access_group_none_group_id_type_error():
    with pytest.raises(TypeCheckError):
        add_user_to_access_group(None, external_id="e1")

def test_add_user_to_access_group_invalid_user_id_type_error():
    with pytest.raises(TypeCheckError):
        add_user_to_access_group("g1", user_id=123)

@patch("access_groups.put_request", return_value={"updated": True})
def test_add_user_to_access_group_success_external_id(mock_put):
    result = add_user_to_access_group("g1", external_id="e1")
    mock_put.assert_called_once_with(
        ag.ACCESS_GROUP_USER_ENDPOINT,
        params={"group_id": "g1"},
        payload={"external_id": "e1"}
    )
    assert result == {"updated": True}

@patch("access_groups.put_request", return_value={"updated": True})
def test_add_user_to_access_group_success_user_id(mock_put):
    result = add_user_to_access_group("g1", user_id="u1")
    mock_put.assert_called_once_with(
        ag.ACCESS_GROUP_USER_ENDPOINT,
        params={"group_id": "g1"},
        payload={"user_id": "u1"}
    )
    assert result == {"updated": True}


# --- remove_user_from_access_group --- #

@pytest.mark.parametrize("group_id, user_id, external_id", [
    ("", None, "e1"),
    ("", "u1", None),
    ("g1", None, None),
    ("g1", "u1", "e1"),
])
def test_remove_user_from_access_group_value_errors(group_id, user_id, external_id):
    with pytest.raises(ValueError):
        remove_user_from_access_group(group_id, external_id=external_id, user_id=user_id)

def test_remove_user_from_access_group_none_group_id_type_error():
    with pytest.raises(TypeCheckError):
        remove_user_from_access_group(None, external_id="e1")

def test_remove_user_from_access_group_invalid_external_id_type_error():
    with pytest.raises(TypeCheckError):
        remove_user_from_access_group("g1", external_id=123)

@patch("access_groups.put_request", return_value={"removed": True})
def test_remove_user_from_access_group_success_external_id(mock_put):
    result = remove_user_from_access_group("g1", external_id="e1")
    mock_put.assert_called_once_with(
        ag.ACCESS_GROUP_USER_ENDPOINT,
        params={"group_id": "g1", "external_id": "e1"}
    )
    assert result == {"removed": True}

@patch("access_groups.put_request", return_value={"removed": True})
def test_remove_user_from_access_group_success_user_id(mock_put):
    result = remove_user_from_access_group("g1", user_id="u1")
    mock_put.assert_called_once_with(
        ag.ACCESS_GROUP_USER_ENDPOINT,
        params={"group_id": "g1", "user_id": "u1"}
    )
    assert result == {"removed": True}

