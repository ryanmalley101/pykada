import pytest
from typeguard import TypeCheckError
from unittest.mock import patch
import base64

# Replace 'access_user' with the actual module name
import access_users as au
from pykada.access_control import get_all_access_users, \
    get_access_user, activate_ble_for_access_user, \
    deactivate_ble_for_access_user, set_end_date_for_user, \
    remove_entry_code_for_user, set_entry_code_for_user, \
    send_pass_app_invite_for_user, delete_profile_photo, get_profile_photo, \
    upload_profile_photo, activate_remote_unlock_for_user, \
    deactivate_remote_unlock_for_user, set_start_date_for_user


@patch("access_users.get_request", return_value={"users": []})
def test_get_access_user_information(mock_get):
    result = get_all_access_users()
    mock_get.assert_called_once_with(au.ACCESS_ALL_USERS_ENDPOINT)
    assert result == {"users": []}


def test_get_all_access_users_missing_ids_raises_value():
    with pytest.raises(ValueError):
        get_access_user()

def test_get_all_access_users_both_ids_raises_value():
    with pytest.raises(ValueError):
        get_access_user(user_id="u1", external_id="e1")

def test_get_all_access_users_none_type_error():
    with pytest.raises(TypeCheckError):
        get_access_user(user_id=123)

@patch("access_users.check_user_external_id", return_value={"user_id": "u1"})
@patch("access_users.get_request", return_value={"data": 1})
def test_get_all_access_users_success(mock_get, mock_check):
    res = get_access_user(user_id="u1")
    mock_check.assert_called_once_with("u1", None)
    mock_get.assert_called_once_with(au.ACCESS_ALL_USERS_ENDPOINT, params={"user_id": "u1"})
    assert res == {"data": 1}


@pytest.mark.parametrize("func, endpoint", [
    (activate_ble_for_access_user, au.ACCESS_BLE_ACTIVATE_ENDPOINT),
    (deactivate_ble_for_access_user, au.ACCESS_BLE_DEACTIVATE_ENDPOINT)
])
def test_ble_funcs_missing_ids_raises_value(func, endpoint):
    with pytest.raises(ValueError):
        func()

@pytest.mark.parametrize("func", [
    activate_ble_for_access_user,
    deactivate_ble_for_access_user
])
def test_ble_funcs_type_error(func):
    with pytest.raises(TypeCheckError):
        func(user_id=123)

@patch("access_users.check_user_external_id", return_value={"external_id": "e1"})
@patch("access_users.put_request", return_value={"ok": True})
def test_ble_funcs_success(mock_put, mock_check):
    for func, endpoint in [
        (activate_ble_for_access_user, au.ACCESS_BLE_ACTIVATE_ENDPOINT),
        (deactivate_ble_for_access_user, au.ACCESS_BLE_DEACTIVATE_ENDPOINT)
    ]:
        mock_put.reset_mock()
        mock_check.reset_mock()
        res = func(external_id="e1")
        mock_check.assert_called_once_with(None, "e1")
        mock_put.assert_called_once_with(endpoint, params={"external_id": "e1"})
        assert res == {"ok": True}


def test_set_end_date_empty_date_raises_value():
    with pytest.raises(ValueError):
        set_end_date_for_user("", user_id="u1")

def test_set_end_date_missing_ids_raises_value():
    with pytest.raises(ValueError):
        set_end_date_for_user("2022-01-01")

def test_set_end_date_type_error():
    with pytest.raises(TypeCheckError):
        set_end_date_for_user(20220101, user_id="u1")

@patch("access_users.check_user_external_id", return_value={"external_id": "e1"})
@patch("access_users.put_request", return_value={"ok": True})
def test_set_end_date_success(mock_put, mock_check):
    res = set_end_date_for_user("2022-01-01", external_id="e1")
    mock_check.assert_called_once_with(None, "e1")
    mock_put.assert_called_once_with(
        au.ACCESS_END_DATE_ENDPOINT,
        params={"external_id": "e1", "end_date": "2022-01-01"}
    )
    assert res == {"ok": True}


def test_remove_entry_code_missing_ids_raises_value():
    with pytest.raises(ValueError):
        remove_entry_code_for_user()

def test_remove_entry_code_type_error():
    with pytest.raises(TypeCheckError):
        remove_entry_code_for_user(user_id=[])

@patch("access_users.check_user_external_id", return_value={"user_id": "u1"})
@patch("access_users.delete_request", return_value={"deleted": True})
def test_remove_entry_code_success(mock_del, mock_check):
    res = remove_entry_code_for_user(user_id="u1")
    mock_check.assert_called_once_with("u1", None)
    mock_del.assert_called_once_with(au.ACCESS_ENTRY_CODE_ENDPOINT, params={"user_id": "u1"})
    assert res == {"deleted": True}


def test_set_entry_code_type_error_user():
    with pytest.raises(TypeCheckError):
        set_entry_code_for_user(entry_code="1234", user_id=123)

@patch("access_users.check_user_external_id", return_value={"user_id": "u1"})
@patch("access_users.put_request", return_value={"set": True})
def test_set_entry_code_success(mock_put, mock_check):
    res = set_entry_code_for_user("abcd", user_id="u1", override=True)
    mock_check.assert_called_once_with("u1", None)
    mock_put.assert_called_once_with(
        au.ACCESS_ENTRY_CODE_ENDPOINT,
        params={"user_id": "u1", "override": True},
        payload={"entry_code": "abcd"}
    )
    assert res == {"set": True}


def test_send_pass_app_invite_missing_ids_raises_value():
    with pytest.raises(ValueError):
        send_pass_app_invite_for_user()

@patch("access_users.check_user_external_id", return_value={"external_id": "e1"})
@patch("access_users.post_request", return_value={"sent": True})
def test_send_pass_app_invite_success(mock_post, mock_check):
    res = send_pass_app_invite_for_user(external_id="e1")
    mock_check.assert_called_once_with(None, "e1")
    mock_post.assert_called_once_with(au.ACCESS_PASS_INVITE_ENDPOINT, params={"external_id": "e1"})
    assert res == {"sent": True}


def test_delete_profile_photo_missing_ids_raises_value():
    with pytest.raises(ValueError):
        delete_profile_photo()

@patch("access_users.check_user_external_id", return_value={"user_id": "u1"})
@patch("access_users.delete_request", return_value={"deleted": True})
def test_delete_profile_photo_success(mock_del, mock_check):
    res = delete_profile_photo(user_id="u1")
    mock_check.assert_called_once_with("u1", None)
    mock_del.assert_called_once_with(au.ACCESS_PROFILE_PHOTO_ENDPOINT, params={"user_id": "u1"})
    assert res == {"deleted": True}


@patch("access_users.check_user_external_id", return_value={"external_id": "e1"})
@patch("access_users.get_request", return_value={"photo": True})
def test_get_profile_photo_default_original(mock_get, mock_check):
    res = get_profile_photo(external_id="e1")
    mock_check.assert_called_once_with(None, "e1")
    mock_get.assert_called_once_with(
        au.ACCESS_PROFILE_PHOTO_ENDPOINT,
        params={"external_id": "e1", "original": False}
    )
    assert res == {"photo": True}


@patch("access_users.check_user_external_id", return_value={"external_id": "e1"})
@patch("access_users.get_request", return_value={"photo": True})
def test_get_profile_photo_with_original_true(mock_get, mock_check):
    res = get_profile_photo(external_id="e1", original=True)
    mock_get.assert_called_once_with(
        au.ACCESS_PROFILE_PHOTO_ENDPOINT,
        params={"external_id": "e1", "original": True}
    )
    assert res == {"photo": True}


def test_upload_profile_photo_type_error_path():
    with pytest.raises(TypeCheckError):
        upload_profile_photo(photo_path=123, user_id="u1")

@patch("access_users.check_user_external_id", return_value={"user_id": "u1"})
@patch("access_users.get_default_api_token", return_value="token123")
@patch("access_users.put_request", return_value={"uploaded": True})
def test_upload_profile_photo_success(mock_put, mock_token, mock_check, tmp_path):
    file_path = tmp_path / "img.jpg"
    content = b"hello"
    file_path.write_bytes(content)
    res = upload_profile_photo(str(file_path), user_id="u1", overwrite=False)
    mock_check.assert_called_once_with("u1", None)
    expected_payload = {"file": base64.b64encode(content).decode("utf_8")}
    mock_put.assert_called_once_with(
        au.ACCESS_PROFILE_PHOTO_ENDPOINT,
        params={"user_id": "u1", "overwrite": False},
        payload=expected_payload
    )
    assert res == {"uploaded": True}


@pytest.mark.parametrize("func, endpoint", [
    (activate_remote_unlock_for_user, au.ACCESS_REMOTE_UNLOCK_ACTIVATE_ENDPOINT),
    (deactivate_remote_unlock_for_user, au.ACCESS_REMOTE_UNLOCK_DEACTIVATE_ENDPOINT)
])
def test_remote_unlock_missing_ids_raises_value(func, endpoint):
    with pytest.raises(ValueError):
        func()

@pytest.mark.parametrize("func", [
    activate_remote_unlock_for_user,
    deactivate_remote_unlock_for_user
])
def test_remote_unlock_type_error(func):
    with pytest.raises(TypeCheckError):
        func(user_id=123)

@patch("access_users.check_user_external_id", return_value={"external_id": "e1"})
@patch("access_users.put_request", return_value={"ok": True})
def test_remote_unlock_success(mock_put, mock_check):
    for func, endpoint in [
        (activate_remote_unlock_for_user, au.ACCESS_REMOTE_UNLOCK_ACTIVATE_ENDPOINT),
        (deactivate_remote_unlock_for_user, au.ACCESS_REMOTE_UNLOCK_DEACTIVATE_ENDPOINT)
    ]:
        mock_put.reset_mock()
        mock_check.reset_mock()
        res = func(external_id="e1")
        mock_check.assert_called_once_with(None, "e1")
        mock_put.assert_called_once_with(endpoint, params={"external_id": "e1"})
        assert res == {"ok": True}


def test_set_start_date_empty_raises_value():
    with pytest.raises(ValueError):
        set_start_date_for_user("", user_id="u1")

def test_set_start_date_missing_ids_raises_value():
    with pytest.raises(ValueError):
        set_start_date_for_user("2022-01-01")

def test_set_start_date_type_error():
    with pytest.raises(TypeCheckError):
        set_start_date_for_user(start_date=20220101, user_id="u1")

@patch("access_users.check_user_external_id", return_value={"user_id": "u1"})
@patch("access_users.put_request", return_value={"set": True})
def test_set_start_date_success(mock_put, mock_check):
    res = set_start_date_for_user("2022-02-02", user_id="u1")
    mock_check.assert_called_once_with("u1", None)
    mock_put.assert_called_once_with(
        au.ACCESS_START_DATE_ENDPOINT,
        params={"user_id": "u1"},
        payload={"start_date": "2022-02-02"}
    )
    assert res == {"set": True}
