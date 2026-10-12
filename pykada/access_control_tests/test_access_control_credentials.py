from unittest.mock import patch

import pytest
from typeguard import TypeCheckError

from pykada.access_control import (
    activate_access_card,
    add_card_to_user,
    add_license_plate_to_user,
    add_mfa_code_to_user,
    add_qr_code_to_user,
    deactivate_access_card,
    delete_access_card,
    delete_license_plate_from_user,
    delete_mfa_code_from_user,
    delete_qr_code_from_user,
    set_license_plate_active,
    update_qr_code_state,
)
from pykada.endpoints import (
    ACCESS_CARD_ACTIVATE_ENDPOINT,
    ACCESS_CARD_DEACTIVATE_ENDPOINT,
    ACCESS_CARD_ENDPOINT,
    V2_ACCESS_EXTERNAL_USERS_ENDPOINT as EXT_USERS,
    V2_ACCESS_LICENSE_PLATES_ENDPOINT as PLATES,
    V2_ACCESS_MFA_CODES_ENDPOINT as MFA,
    V2_ACCESS_USERS_ENDPOINT as USERS,
)

RM = "pykada.verkada_requests.VerkadaRequestManager"

REQUEST_CASES = [
    # Cards (v1)
    (add_card_to_user, {"card_type": "HID 37-bit", "user_id": "u1", "card_number": "123",
                        "facility_code": "7", "active": True},
     "post", ACCESS_CARD_ENDPOINT,
     {"params": {"user_id": "u1"},
      "payload": {"type": "HID 37-bit", "card_number": "123", "facility_code": "7",
                  "active": True}}),
    (add_card_to_user, {"card_type": "DESFire CSN", "external_id": "e1",
                        "card_number_hex": "AB12"},
     "post", ACCESS_CARD_ENDPOINT,
     {"params": {"external_id": "e1"},
      "payload": {"type": "DESFire CSN", "card_number_hex": "AB12"}}),
    (activate_access_card, {"card_id": "c1", "user_id": "u1"}, "put",
     ACCESS_CARD_ACTIVATE_ENDPOINT, {"params": {"user_id": "u1", "card_id": "c1"}}),
    (deactivate_access_card, {"card_id": "c1", "external_id": "e1"}, "put",
     ACCESS_CARD_DEACTIVATE_ENDPOINT, {"params": {"external_id": "e1", "card_id": "c1"}}),
    (delete_access_card, {"card_id": "c1", "user_id": "u1"}, "delete",
     ACCESS_CARD_ENDPOINT, {"params": {"user_id": "u1", "card_id": "c1"}}),
    # License plates
    (add_license_plate_to_user, {"license_plate_number": "ABC123", "user_id": "u1"},
     "post", PLATES, {"payload": {"user_id": "u1", "license_plate_number": "ABC123"}}),
    (add_license_plate_to_user, {"license_plate_number": "ABC123", "external_id": "e1",
                                 "name": "Work car", "active": True},
     "post", PLATES, {"payload": {"external_id": "e1", "license_plate_number": "ABC123",
                                  "name": "Work car", "active": True}}),
    (set_license_plate_active, {"license_plate_number": "ABC 123", "active": False,
                                "user_id": "u1"},
     "patch", f"{PLATES}/ABC%20123", {"payload": {"user_id": "u1", "active": False}}),
    (delete_license_plate_from_user, {"license_plate_number": "ABC123", "external_id": "e1"},
     "delete", f"{PLATES}/ABC123", {"params": {"external_id": "e1"}}),
    # MFA codes
    (add_mfa_code_to_user, {"code": "123456", "user_id": "u1"}, "post", MFA,
     {"payload": {"user_id": "u1", "code": "123456"}}),
    (delete_mfa_code_from_user, {"code": "123456", "external_id": "e1"}, "delete",
     f"{MFA}/123456", {"params": {"external_id": "e1"}}),
    # QR codes
    (add_qr_code_to_user, {"encoding_type": "NONE", "user_id": "u1", "qr_code": "42"},
     "post", f"{USERS}/u1/credentials/qr_codes",
     {"payload": {"encoding_type": "NONE", "qr_code": "42"}}),
    (add_qr_code_to_user, {"encoding_type": "Standard 26-bit Wiegand", "external_id": "e/1",
                           "card_number": "100", "facility_code": "5", "active": True},
     "post", f"{EXT_USERS}/e%2F1/credentials/qr_codes",
     {"payload": {"encoding_type": "Standard 26-bit Wiegand", "card_number": "100",
                  "facility_code": "5", "active": True}}),
    (update_qr_code_state, {"encoding_type": "NONE", "user_id": "u1", "qr_code": "42",
                            "activation_state": "lost"},
     "patch", f"{USERS}/u1/credentials/qr_codes",
     {"params": {"encoding_type": "NONE", "qr_code": "42"},
      "payload": {"activation_state": "lost"}}),
    (delete_qr_code_from_user, {"encoding_type": "NONE", "external_id": "e1",
                                "card_number_hex": "FF"},
     "delete", f"{EXT_USERS}/e1/credentials/qr_codes",
     {"params": {"encoding_type": "NONE", "card_number_hex": "FF"}}),
]


@pytest.mark.parametrize("func, kwargs, method, url, request_kwargs", REQUEST_CASES,
                         ids=[f"{c[0].__name__}-{i}" for i, c in enumerate(REQUEST_CASES)])
def test_request_shape(func, kwargs, method, url, request_kwargs):
    with patch(f"{RM}.{method}", return_value={"ok": True}) as mock:
        assert func(**kwargs) == {"ok": True}
    mock.assert_called_once_with(url, **request_kwargs)


@pytest.mark.parametrize("call, match", [
    # user identifier rules
    (lambda: add_license_plate_to_user("ABC123"), "Exactly one of user_id or external_id"),
    (lambda: add_mfa_code_to_user("1234", user_id="u1", external_id="e1"), "Exactly one"),
    (lambda: delete_access_card("c1"), "Exactly one"),
    (lambda: add_qr_code_to_user("NONE", qr_code="1"), "Exactly one"),
    # cards
    (lambda: add_card_to_user("HID 37-bit", user_id="u1"), "card_number"),
    (lambda: add_card_to_user("HID 37-bit", user_id="u1", card_number="1",
                              card_number_hex="1"), "card_number"),
    (lambda: add_card_to_user("", user_id="u1", card_number="1"), "card_type"),
    (lambda: activate_access_card("", user_id="u1"), "card_id"),
    # plates
    (lambda: add_license_plate_to_user("A", user_id="u1"), "2 to 16"),
    (lambda: add_license_plate_to_user("A" * 17, user_id="u1"), "2 to 16"),
    (lambda: set_license_plate_active("", True, user_id="u1"), "license_plate_number"),
    # MFA
    (lambda: add_mfa_code_to_user("123", user_id="u1"), "4 to 16 digits"),
    (lambda: add_mfa_code_to_user("abcd", user_id="u1"), "4 to 16 digits"),
    (lambda: delete_mfa_code_from_user("", user_id="u1"), "code"),
    # QR
    (lambda: update_qr_code_state("NONE", user_id="u1", qr_code="1"), "active or activation_state"),
    (lambda: update_qr_code_state("NONE", user_id="u1", active=False), "qr_code"),
    (lambda: delete_qr_code_from_user("NONE", user_id="u1", qr_code="1", card_number="2"),
     "qr_code"),
    (lambda: add_qr_code_to_user("", user_id="u1"), "encoding_type"),
])
def test_validation(call, match):
    with pytest.raises(ValueError, match=match):
        call()


def test_card_email_identifier_not_accepted():
    with pytest.raises(TypeError):
        add_card_to_user("HID 37-bit", email="a@b.com", card_number="1")


def test_set_license_plate_active_requires_bool():
    with pytest.raises(TypeCheckError):
        set_license_plate_active("ABC123", "yes", user_id="u1")
