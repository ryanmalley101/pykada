import pytest
from typeguard import TypeCheckError
from unittest.mock import patch

from pykada import access_control_tests as ac
from pykada.access_control import delete_access_card, \
    add_card_to_user, activate_access_card, deactivate_access_card, \
    delete_license_plate_from_user, add_license_plate_to_user, \
    activate_license_plate, deactivate_license_plate, \
    delete_mfa_code_from_user, add_mfa_code_to_user


# ————— delete_access_card ————— #

@pytest.mark.parametrize("bad_id", ["", ""])
def test_delete_access_card_empty_card_id_raises_value(bad_id):
    with pytest.raises(ValueError):
        delete_access_card(bad_id, user_id="u1")

def test_delete_access_card_none_card_id_type_error():
    with pytest.raises(TypeCheckError):
        delete_access_card(None, user_id="u1")

@patch("access_credentials.check_user_external_id", return_value={"user_id": "u1"})
@patch("access_credentials.delete_request", return_value={"deleted": True})
def test_delete_access_card_calls_delete(mock_del, mock_check):
    res = delete_access_card("card123", user_id="u1")
    mock_check.assert_called_once_with("u1", None)
    mock_del.assert_called_once_with(
        ac.ACCESS_CARD_ENDPOINT,
        params={"user_id": "u1", "card_id": "card123"}
    )
    assert res == {"deleted": True}


# ————— add_card_to_user ————— #

def test_add_card_to_user_invalid_card_number_raises_value():
    # none of the three provided
    with pytest.raises(ValueError):
        add_card_to_user(user_id="u1")

    # more than one provided
    with pytest.raises(ValueError):
        add_card_to_user(user_id="u1", card_number="n", card_number_hex="h")

@patch("access_credentials.check_user_external_id", return_value={"external_id": "e1"})
@patch("access_credentials.post_request", return_value={"created": True})
def test_add_card_to_user_success(mock_post, mock_check):
    # supply exactly one format
    res = add_card_to_user(
        external_id="e1",
        active=True,
        card_number_hex="ABCD",
        facility_code="42",
        card_type="Standard"
    )
    mock_check.assert_called_once_with(None, "e1")
    mock_post.assert_called_once_with(
        ac.ACCESS_CARD_ENDPOINT,
        params={"external_id": "e1"},
        payload={
            "active": True,
            "facility_code": "42",
            "type": "Standard",
            "card_number_hex": "ABCD"
        }
    )
    assert res == {"created": True}


# ————— activate_access_card / deactivate_access_card ————— #

@pytest.mark.parametrize("func, endpoint", [
    (activate_access_card, ac.ACCESS_CARD_ACTIVATE_ENDPOINT),
    (deactivate_access_card, ac.ACCESS_CARD_DEACTIVATE_ENDPOINT),
])
@patch("access_credentials.check_user_external_id", return_value={"user_id": "u2"})
@patch("access_credentials.put_request", return_value={"ok": True})
def test_toggle_access_card_success(mock_put, mock_check, func, endpoint):
    result = func("card456", user_id="u2")
    mock_check.assert_called_once_with("u2", None)
    mock_put.assert_called_once_with(
        endpoint,
        params={"user_id": "u2", "card_id": "card456"}
    )
    assert result == {"ok": True}

def test_activate_access_card_empty_id_raises_value():
    with pytest.raises(ValueError):
        activate_access_card("", user_id="u1")

def test_deactivate_access_card_empty_id_raises_value():
    with pytest.raises(ValueError):
        deactivate_access_card("", external_id="e1")


# ————— delete_license_plate_from_user ————— #

@pytest.mark.parametrize("bad_plate", ["", ""])
def test_delete_license_plate_empty_raises_value(bad_plate):
    with pytest.raises(ValueError):
        delete_license_plate_from_user(bad_plate, user_id="u3")

@patch("access_credentials.check_user_external_id", return_value={"external_id": "e3"})
@patch("access_credentials.delete_request", return_value={"removed": True})
def test_delete_license_plate_calls_delete(mock_del, mock_check):
    res = delete_license_plate_from_user("PLATE123", external_id="e3")
    mock_check.assert_called_once_with(None, "e3")
    mock_del.assert_called_once_with(
        ac.ACCESS_LICENSE_PLATE_ENDPOINT,
        params={"external_id": "e3", "license_plate_number": "PLATE123"}
    )
    assert res == {"removed": True}


# ————— add_license_plate_to_user ————— #

def test_add_license_plate_empty_number_raises_value():
    with pytest.raises(ValueError):
        add_license_plate_to_user("", user_id="u4")
#
# @patch("access_credentials.check_user_external_id", return_value={"user_id": "u4"})
# @patch("access_credentials.remove_null_fields", lambda payload: payload)
# @patch("access_credentials.post_request", return_value={"added": True})
# def test_add_license_plate_success(mock_post):
#     res = add_license_plate_to_user(
#         "PLATE999",
#         active=False,
#         name=None,
#         user_id="u4"
#     )
#     # name=None should be dropped by remove_null_fields stub
#     mock_post.assert_called_once_with(
#         ac.ACCESS_LICENSE_PLATE_ENDPOINT,
#         params={"user_id": "u4"},
#         payload={"license_plate_number": "PLATE999", "active": False}
#     )
#     assert res == {"added": True}


# ————— activate_license_plate / deactivate_license_plate ————— #

@pytest.mark.parametrize("func, endpoint", [
    (activate_license_plate, ac.ACCESS_LICENSE_PLATE_ACTIVATE_ENDPOINT),
    (deactivate_license_plate, ac.ACCESS_LICENSE_PLATE_DEACTIVATE_ENDPOINT),
])
@patch("access_credentials.check_user_external_id", return_value={"external_id": "e5"})
@patch("access_credentials.put_request", return_value={"done": True})
def test_toggle_license_plate_success(mock_put, mock_check, func, endpoint):
    out = func("PL123", external_id="e5")
    mock_check.assert_called_once_with(None, "e5")
    mock_put.assert_called_once_with(
        endpoint,
        params={"external_id": "e5", "license_plate_number": "PL123"}
    )
    assert out == {"done": True}

@pytest.mark.parametrize("func", [activate_license_plate, deactivate_license_plate])
def test_toggle_license_plate_empty_number_raises_value(func):
    with pytest.raises(ValueError):
        func("", user_id="u6")


# ————— delete_mfa_code_from_user / add_mfa_code_to_user ————— #

@pytest.mark.parametrize("func", [delete_mfa_code_from_user, add_mfa_code_to_user])
def test_mfa_code_empty_raises_value(func):
    with pytest.raises(ValueError):
        func("", user_id="u7")

@patch("access_credentials.check_user_external_id", return_value={"user_id": "u7"})
@patch("access_credentials.delete_request", return_value={"mfa_deleted": True})
def test_delete_mfa_code_success(mock_del, mock_check):
    res = delete_mfa_code_from_user("CODE1", user_id="u7")
    mock_check.assert_called_once_with("u7", None)
    mock_del.assert_called_once_with(
        ac.ACCESS_MFA_CODE_ENDPOINT,
        params={"user_id": "u7", "code": "CODE1"}
    )
    assert res == {"mfa_deleted": True}

@patch("access_credentials.check_user_external_id", return_value={"external_id": "e7"})
@patch("access_credentials.post_request", return_value={"mfa_added": True})
def test_add_mfa_code_success(mock_post, mock_check):
    res = add_mfa_code_to_user("CODE2", external_id="e7")
    mock_check.assert_called_once_with(None, "e7")
    mock_post.assert_called_once_with(
        ac.ACCESS_MFA_CODE_ENDPOINT,
        params={"external_id": "e7", "code": "CODE2"}
    )
    assert res == {"mfa_added": True}
