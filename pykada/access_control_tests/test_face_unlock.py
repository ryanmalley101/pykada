from unittest.mock import ANY, patch

import pytest

from pykada.access_control import (
    disable_face_unlock,
    enable_face_unlock_with_profile_photo,
    enable_face_unlock_with_uploaded_photo,
    invite_user_to_enroll_face_unlock,
)
from pykada.endpoints import (
    V2_ACCESS_EXTERNAL_USERS_ENDPOINT as EXT_USERS,
    V2_ACCESS_USERS_ENDPOINT as USERS,
)

RM = "pykada.verkada_requests.VerkadaRequestManager"


@pytest.mark.parametrize("ids, base", [
    ({"user_id": "u1"}, f"{USERS}/u1"),
    ({"external_id": "ext 1"}, f"{EXT_USERS}/ext%201"),
])
class TestFaceUnlockRoutes:
    def test_disable(self, ids, base):
        with patch(f"{RM}.delete", return_value={}) as mock:
            disable_face_unlock(**ids)
        mock.assert_called_once_with(f"{base}/face_unlock")

    def test_copy_profile_photo(self, ids, base):
        with patch(f"{RM}.post", return_value={"user_id": "u1"}) as mock:
            enable_face_unlock_with_profile_photo(**ids, overwrite=True)
        mock.assert_called_once_with(f"{base}/face_unlock/copy_user_photo",
                                     payload={"overwrite": True})

    def test_invite(self, ids, base):
        with patch(f"{RM}.post", return_value={}) as mock:
            invite_user_to_enroll_face_unlock(**ids, invitation_methods=["sms"])
        mock.assert_called_once_with(f"{base}/face_unlock/invite",
                                     payload={"invitation_methods": ["sms"]})

    def test_upload_photo_is_multipart(self, ids, base, tmp_path):
        photo = tmp_path / "face.jpg"
        photo.write_bytes(b"jpeg")
        with patch(f"{RM}.post", return_value={"identity_id": "i1"}) as mock:
            enable_face_unlock_with_uploaded_photo(str(photo), **ids, overwrite=True)
        mock.assert_called_once_with(f"{base}/face_unlock/upload_photo",
                                     files={"file": ANY}, data={"overwrite": "true"})


@patch(f"{RM}.post", return_value={})
def test_copy_profile_photo_defaults_send_empty_body(mock_post):
    enable_face_unlock_with_profile_photo(user_id="u1")
    mock_post.assert_called_once_with(f"{USERS}/u1/face_unlock/copy_user_photo", payload={})


@patch(f"{RM}.post", return_value={})
def test_upload_photo_without_overwrite_sends_no_form_fields(mock_post, tmp_path):
    photo = tmp_path / "face.jpg"
    photo.write_bytes(b"jpeg")
    enable_face_unlock_with_uploaded_photo(str(photo), user_id="u1")
    assert mock_post.call_args.kwargs["data"] is None


@pytest.mark.parametrize("call", [
    lambda: disable_face_unlock(),
    lambda: disable_face_unlock(user_id="u1", external_id="e1"),
    lambda: enable_face_unlock_with_profile_photo(),
    lambda: invite_user_to_enroll_face_unlock(user_id=""),
])
def test_identifier_validation(call):
    with pytest.raises(ValueError):
        call()


def test_upload_photo_missing_file():
    with pytest.raises(FileNotFoundError):
        enable_face_unlock_with_uploaded_photo("/no/such.jpg", user_id="u1")
