import types
from datetime import datetime, timezone
from unittest.mock import ANY, patch

import pytest
from typeguard import TypeCheckError

from pykada.access_control import (
    AccessControlClient,
    activate_remote_unlock_for_user,
    create_pass_sdk_token,
    deactivate_remote_unlock_for_user,
    delete_profile_photo,
    find_access_user,
    get_access_user,
    get_access_users,
    get_all_access_users,
    get_profile_photo,
    remove_entry_code_for_user,
    resolve_user_id,
    send_pass_app_invite_for_user,
    set_ble_unlock,
    set_entry_code_for_user,
    update_access_user_dates,
    upload_profile_photo,
)
from pykada.endpoints import (
    ACCESS_REMOTE_UNLOCK_ACTIVATE_ENDPOINT,
    ACCESS_REMOTE_UNLOCK_DEACTIVATE_ENDPOINT,
    ACCESS_USER_ENDPOINT,
    V2_ACCESS_PASS_SDK_TOKEN_ENDPOINT,
    V2_ACCESS_USERS_ENDPOINT as USERS,
    V2_CORE_USERS_ENDPOINT,
)

RM = "pykada.verkada_requests.VerkadaRequestManager"
U1 = f"{USERS}/u1"
CHALLENGE = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"  # RFC 7636 example


REQUEST_CASES = [
    (get_access_users, {}, "get", USERS, {"params": {}}),
    (get_access_users, {"include_visitors": True, "limit": 1000, "cursor": "c"}, "get", USERS,
     {"params": {"include_visitors": True, "limit": 1000, "cursor": "c"}}),
    (get_access_user, {"user_id": "u1"}, "get", U1, {}),
    (find_access_user, {"email": "a@b.com"}, "get", ACCESS_USER_ENDPOINT,
     {"params": {"email": "a@b.com"}}),
    (find_access_user, {"employee_id": "E1"}, "get", ACCESS_USER_ENDPOINT,
     {"params": {"employee_id": "E1"}}),
    (update_access_user_dates, {"user_id": "u1", "start_date": "2025-07-17T21:06:20Z"},
     "patch", U1, {"payload": {"start_date": "2025-07-17T21:06:20Z"}}),
    (update_access_user_dates, {"user_id": "u1",
                                "start_date": datetime(2025, 1, 1, tzinfo=timezone.utc),
                                "end_date": "2025-12-31T23:59:59-08:00"},
     "patch", U1, {"payload": {"start_date": "2025-01-01T00:00:00Z",
                               "end_date": "2025-12-31T23:59:59-08:00"}}),
    (set_ble_unlock, {"user_id": "u1", "active": True}, "put", f"{U1}/ble",
     {"payload": {"active": True}}),
    (set_ble_unlock, {"user_id": "u1", "active": False}, "put", f"{U1}/ble",
     {"payload": {"active": False}}),
    (set_entry_code_for_user, {"user_id": "u1", "entry_code": "1234"}, "put",
     f"{U1}/entry_code", {"payload": {"entry_code": "1234"}}),
    (set_entry_code_for_user, {"user_id": "u1", "entry_code": "1234567890123456",
                               "override": True},
     "put", f"{U1}/entry_code", {"payload": {"entry_code": "1234567890123456",
                                             "override": True}}),
    (remove_entry_code_for_user, {"user_id": "u1"}, "delete", f"{U1}/entry_code", {}),
    (send_pass_app_invite_for_user, {"user_id": "u1"}, "post", f"{U1}/pass/invitations",
     {"payload": {}}),
    (send_pass_app_invite_for_user, {"user_id": "u1", "invitation_methods": ["email"]},
     "post", f"{U1}/pass/invitations", {"payload": {"invitation_methods": ["email"]}}),
    (create_pass_sdk_token, {"user_id": "u1", "code_challenge": CHALLENGE}, "post",
     V2_ACCESS_PASS_SDK_TOKEN_ENDPOINT,
     {"payload": {"user_id": "u1", "code_challenge": CHALLENGE}}),
    (delete_profile_photo, {"user_id": "u1"}, "delete", f"{U1}/profile_photo", {}),
    (activate_remote_unlock_for_user, {"user_id": "u1"}, "put",
     ACCESS_REMOTE_UNLOCK_ACTIVATE_ENDPOINT, {"params": {"user_id": "u1"}}),
    (deactivate_remote_unlock_for_user, {"external_id": "e1"}, "put",
     ACCESS_REMOTE_UNLOCK_DEACTIVATE_ENDPOINT, {"params": {"external_id": "e1"}}),
]


@pytest.mark.parametrize("func, kwargs, method, url, request_kwargs", REQUEST_CASES,
                         ids=[f"{c[0].__name__}-{i}" for i, c in enumerate(REQUEST_CASES)])
def test_request_shape(func, kwargs, method, url, request_kwargs):
    with patch(f"{RM}.{method}", return_value={"ok": True}) as mock:
        assert func(**kwargs) == {"ok": True}
    mock.assert_called_once_with(url, **request_kwargs)


@patch(f"{RM}.get")
def test_get_all_access_users_walks_pages(mock_get):
    mock_get.side_effect = [{"items": [{"user_id": "a"}], "cursor": "c1"},
                            {"items": [{"user_id": "b"}], "cursor": None}]
    result = get_all_access_users(include_visitors=True)
    assert isinstance(result, types.GeneratorType)
    assert [u["user_id"] for u in result] == ["a", "b"]
    assert mock_get.call_args_list[1].kwargs["params"] == {
        "include_visitors": True, "limit": 100, "cursor": "c1"}


@patch(f"{RM}.get", return_value={"user_id": "u-9", "active": True})
def test_resolve_user_id_uses_core_users(mock_get):
    assert resolve_user_id("ext-9") == "u-9"
    mock_get.assert_called_once_with(V2_CORE_USERS_ENDPOINT, params={"external_id": "ext-9"})


def test_resolve_user_id_reuses_client_request_manager():
    client = AccessControlClient(api_key="key")
    with patch.object(client.request_manager, "get",
                      return_value={"user_id": "u-1"}) as mock_get:
        assert client.resolve_user_id("ext") == "u-1"
    mock_get.assert_called_once()


@patch(f"{RM}.get_image", return_value=b"\x89PNG")
def test_get_profile_photo(mock_get_image):
    assert get_profile_photo("u1", original=True) == b"\x89PNG"
    mock_get_image.assert_called_once_with(f"{U1}/profile_photo", params={"original": True})


@patch(f"{RM}.put", return_value={})
def test_upload_profile_photo_sends_multipart(mock_put, tmp_path):
    photo = tmp_path / "me.png"
    photo.write_bytes(b"png-bytes")
    assert upload_profile_photo("u1", str(photo), overwrite=True) == {}
    mock_put.assert_called_once_with(f"{U1}/profile_photo", params={"overwrite": True},
                                     files={"file": ANY})
    # No JSON headers are forced on the upload; the request manager strips content-type
    assert "headers" not in mock_put.call_args.kwargs


def test_upload_profile_photo_missing_file():
    with pytest.raises(FileNotFoundError):
        upload_profile_photo("u1", "/no/such/photo.png")


# ---------- validation ----------

@pytest.mark.parametrize("call, match", [
    (lambda: get_access_user(""), "user_id"),
    (lambda: set_ble_unlock(" ", True), "user_id"),
    (lambda: update_access_user_dates("u1"), "At least one"),
    (lambda: update_access_user_dates("u1", start_date="2025-07-17T21:06:20"), "timezone"),
    (lambda: update_access_user_dates("u1", start_date="2025-02-01T00:00:00Z",
                                      end_date="2025-01-01T00:00:00Z"), "before"),
    (lambda: update_access_user_dates("u1", start_date="2025-01-01T00:00:00Z",
                                      end_date="2025-01-01T00:00:00Z"), "before"),
    (lambda: set_entry_code_for_user("u1", "123"), "4 to 16 digits"),
    (lambda: set_entry_code_for_user("u1", "12345678901234567"), "4 to 16 digits"),
    (lambda: set_entry_code_for_user("u1", "12ab"), "4 to 16 digits"),
    (lambda: create_pass_sdk_token("u1", "too-short"), "code_challenge"),
    (lambda: create_pass_sdk_token("u1", CHALLENGE + "="), "code_challenge"),
    (lambda: create_pass_sdk_token("", CHALLENGE), "user_id"),
    (lambda: find_access_user(), "Exactly one"),
    (lambda: find_access_user(user_id="u1", email="a@b.com"), "Exactly one"),
    (lambda: activate_remote_unlock_for_user(), "Exactly one"),
])
def test_validation(call, match):
    with pytest.raises(ValueError, match=match):
        call()


def test_update_access_user_dates_rejects_epoch():
    with pytest.raises(TypeCheckError):
        update_access_user_dates("u1", start_date=1700000000)


def test_get_access_user_no_longer_takes_email():
    with pytest.raises(TypeError):
        get_access_user(email="a@b.com")
