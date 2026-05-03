import pytest
from typeguard import TypeCheckError
from unittest.mock import patch

from pykada.endpoints import ACCESS_ADMIN_UNLOCK_ENDPOINT, ACCESS_USER_UNLOCK_ENDPOINT, ACCESS_DOORS_ENDPOINT
from pykada.access_control import unlock_door_as_admin, \
    unlock_door_as_user, get_doors


# --- unlock_door_as_admin --- #

def test_unlock_door_as_admin_empty_id_raises_value():
    with pytest.raises(ValueError):
        unlock_door_as_admin("")

def test_unlock_door_as_admin_none_id_raises_type_error():
    with pytest.raises(TypeCheckError):
        unlock_door_as_admin(None)  # door_id must be str

@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"result": "unlocked"})
def test_unlock_door_as_admin_success(mock_post):
    res = unlock_door_as_admin("door123")
    mock_post.assert_called_once_with(
        ACCESS_ADMIN_UNLOCK_ENDPOINT,
        payload={"door_id": "door123"}
    )
    assert res == {"result": "unlocked"}


# --- unlock_door_as_user --- #

def test_unlock_door_as_user_empty_id_raises_value():
    with pytest.raises(ValueError):
        unlock_door_as_user("", user_id="u1")

def test_unlock_door_as_user_none_id_raises_type_error():
    with pytest.raises(TypeCheckError):
        unlock_door_as_user(None, user_id="u1")

def test_unlock_door_as_user_missing_ids_raises_value():
    with pytest.raises(ValueError):
        unlock_door_as_user("door123")

def test_unlock_door_as_user_both_ids_raises_value():
    with pytest.raises(ValueError):
        unlock_door_as_user("door123", user_id="u1", external_id="e1")

@patch("pykada.access_control.check_user_external_id", return_value={"user_id": "u1"})
@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"result": "unlocked"})
def test_unlock_door_as_user_success_user_id(mock_post, mock_check):
    res = unlock_door_as_user("door123", user_id="u1")
    mock_check.assert_called_once_with("u1", None)
    mock_post.assert_called_once_with(
        ACCESS_USER_UNLOCK_ENDPOINT,
        payload={"user_id": "u1", "door_id": "door123"}
    )
    assert res == {"result": "unlocked"}

@patch("pykada.access_control.check_user_external_id", return_value={"external_id": "e1"})
@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"result": "unlocked"})
def test_unlock_door_as_user_success_external_id(mock_post, mock_check):
    res = unlock_door_as_user("door123", external_id="e1")
    mock_check.assert_called_once_with(None, "e1")
    mock_post.assert_called_once_with(
        ACCESS_USER_UNLOCK_ENDPOINT,
        payload={"external_id": "e1", "door_id": "door123"}
    )
    assert res == {"result": "unlocked"}


# --- get_doors --- #

@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"doors": []})
def test_get_doors_default(mock_get):
    res = get_doors()
    mock_get.assert_called_once_with(
        ACCESS_DOORS_ENDPOINT,
        params={"door_ids": None, "site_ids": None}
    )
    assert isinstance(res, dict)

@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"doors": ["d1", "d2"]})
def test_get_doors_with_lists(mock_get):
    res = get_doors(door_id_list=["d1", "d2"], site_id_list=[10, 20])
    mock_get.assert_called_once_with(
        ACCESS_DOORS_ENDPOINT,
        params={"door_ids": "d1,d2", "site_ids": "10,20"}
    )
    assert res == {"doors": ["d1", "d2"]}

def test_get_doors_bad_door_list_type():
    with pytest.raises(TypeCheckError):
        get_doors(door_id_list="not-a-list")

def test_get_doors_bad_site_list_type():
    with pytest.raises(TypeCheckError):
        get_doors(site_id_list="not-a-list")
