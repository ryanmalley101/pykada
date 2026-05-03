import pytest
from unittest.mock import patch

from pykada.endpoints import (
    FACE_UNLOCK_USERS_V2_ENDPOINT,
    FACE_UNLOCK_EXTERNAL_USERS_V2_ENDPOINT,
)
from pykada.access_control import (
    disable_face_unlock_for_user,
    enable_face_unlock_with_profile_photo_for_user,
    invite_user_to_enroll_face_unlock,
    enable_face_unlock_with_uploaded_photo_for_user,
    disable_face_unlock_for_external_user,
    enable_face_unlock_with_profile_photo_for_external_user,
    invite_external_user_to_enroll_face_unlock,
    enable_face_unlock_with_uploaded_photo_for_external_user,
)

# ——— disable_face_unlock_for_user ——— #

def test_disable_face_unlock_for_user_empty_id_raises():
    with pytest.raises(ValueError, match="user_id"):
        disable_face_unlock_for_user("")


@patch("pykada.verkada_requests.VerkadaRequestManager.delete", return_value={"disabled": True})
def test_disable_face_unlock_for_user_success(mock_delete):
    result = disable_face_unlock_for_user("u1")
    assert isinstance(result, dict)
    expected_url = f"{FACE_UNLOCK_USERS_V2_ENDPOINT}/u1/face_unlock"
    mock_delete.assert_called_once_with(expected_url)


# ——— enable_face_unlock_with_profile_photo_for_user ——— #

def test_enable_face_unlock_profile_photo_user_empty_id_raises():
    with pytest.raises(ValueError, match="user_id"):
        enable_face_unlock_with_profile_photo_for_user("")


@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"enabled": True})
def test_enable_face_unlock_profile_photo_user_success(mock_post):
    result = enable_face_unlock_with_profile_photo_for_user("u1")
    assert isinstance(result, dict)
    expected_url = f"{FACE_UNLOCK_USERS_V2_ENDPOINT}/u1/face_unlock/copy_user_photo"
    mock_post.assert_called_once_with(expected_url, payload={})


@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"enabled": True})
def test_enable_face_unlock_profile_photo_user_with_overwrite(mock_post):
    enable_face_unlock_with_profile_photo_for_user("u1", overwrite=True)
    _, kwargs = mock_post.call_args
    assert kwargs["payload"]["overwrite"] is True


# ——— invite_user_to_enroll_face_unlock ——— #

def test_invite_user_face_unlock_empty_id_raises():
    with pytest.raises(ValueError, match="user_id"):
        invite_user_to_enroll_face_unlock("")


@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"invited": True})
def test_invite_user_face_unlock_success(mock_post):
    result = invite_user_to_enroll_face_unlock("u1")
    assert isinstance(result, dict)
    expected_url = f"{FACE_UNLOCK_USERS_V2_ENDPOINT}/u1/face_unlock/invite"
    mock_post.assert_called_once_with(expected_url, payload={})


@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"invited": True})
def test_invite_user_face_unlock_with_methods(mock_post):
    invite_user_to_enroll_face_unlock("u1", invitation_methods=["email"])
    _, kwargs = mock_post.call_args
    assert kwargs["payload"]["invitation_methods"] == ["email"]


# ——— enable_face_unlock_with_uploaded_photo_for_user ——— #

def test_enable_face_unlock_upload_user_empty_id_raises():
    with pytest.raises(ValueError, match="user_id"):
        enable_face_unlock_with_uploaded_photo_for_user("")


@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"enabled": True})
def test_enable_face_unlock_upload_user_success(mock_post):
    result = enable_face_unlock_with_uploaded_photo_for_user("u1")
    assert isinstance(result, dict)
    expected_url = f"{FACE_UNLOCK_USERS_V2_ENDPOINT}/u1/face_unlock/upload_photo"
    mock_post.assert_called_once_with(expected_url, payload={})


# ——— disable_face_unlock_for_external_user ——— #

def test_disable_face_unlock_for_external_user_empty_id_raises():
    with pytest.raises(ValueError, match="external_id"):
        disable_face_unlock_for_external_user("")


@patch("pykada.verkada_requests.VerkadaRequestManager.delete", return_value={"disabled": True})
def test_disable_face_unlock_for_external_user_success(mock_delete):
    result = disable_face_unlock_for_external_user("ext1")
    assert isinstance(result, dict)
    expected_url = f"{FACE_UNLOCK_EXTERNAL_USERS_V2_ENDPOINT}/ext1/face_unlock"
    mock_delete.assert_called_once_with(expected_url)


# ——— enable_face_unlock_with_profile_photo_for_external_user ——— #

def test_enable_face_unlock_profile_photo_external_empty_id_raises():
    with pytest.raises(ValueError, match="external_id"):
        enable_face_unlock_with_profile_photo_for_external_user("")


@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"enabled": True})
def test_enable_face_unlock_profile_photo_external_success(mock_post):
    result = enable_face_unlock_with_profile_photo_for_external_user("ext1")
    assert isinstance(result, dict)
    expected_url = f"{FACE_UNLOCK_EXTERNAL_USERS_V2_ENDPOINT}/ext1/face_unlock/copy_user_photo"
    mock_post.assert_called_once_with(expected_url, payload={})


@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"enabled": True})
def test_enable_face_unlock_profile_photo_external_with_overwrite(mock_post):
    enable_face_unlock_with_profile_photo_for_external_user("ext1", overwrite=False)
    _, kwargs = mock_post.call_args
    assert kwargs["payload"]["overwrite"] is False


# ——— invite_external_user_to_enroll_face_unlock ——— #

def test_invite_external_user_face_unlock_empty_id_raises():
    with pytest.raises(ValueError, match="external_id"):
        invite_external_user_to_enroll_face_unlock("")


@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"invited": True})
def test_invite_external_user_face_unlock_success(mock_post):
    result = invite_external_user_to_enroll_face_unlock("ext1")
    assert isinstance(result, dict)
    expected_url = f"{FACE_UNLOCK_EXTERNAL_USERS_V2_ENDPOINT}/ext1/face_unlock/invite"
    mock_post.assert_called_once_with(expected_url, payload={})


@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"invited": True})
def test_invite_external_user_face_unlock_with_methods(mock_post):
    invite_external_user_to_enroll_face_unlock("ext1", invitation_methods=["sms", "email"])
    _, kwargs = mock_post.call_args
    assert kwargs["payload"]["invitation_methods"] == ["sms", "email"]


# ——— enable_face_unlock_with_uploaded_photo_for_external_user ——— #

def test_enable_face_unlock_upload_external_empty_id_raises():
    with pytest.raises(ValueError, match="external_id"):
        enable_face_unlock_with_uploaded_photo_for_external_user("")


@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"enabled": True})
def test_enable_face_unlock_upload_external_success(mock_post):
    result = enable_face_unlock_with_uploaded_photo_for_external_user("ext1")
    assert isinstance(result, dict)
    expected_url = f"{FACE_UNLOCK_EXTERNAL_USERS_V2_ENDPOINT}/ext1/face_unlock/upload_photo"
    mock_post.assert_called_once_with(expected_url, payload={})
