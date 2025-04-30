import pytest
from unittest.mock import patch
from core_command import (
    get_audit_logs, get_user, create_user, update_user, delete_user
)

# -----------------------------
# Audit Log Tests
# -----------------------------

def test_get_audit_logs_invalid_page_size():
    with pytest.raises(ValueError, match="page_size must be between 0 and 200"):
        get_audit_logs(page_size=500)

@patch("core_command.get_request")
def test_get_audit_logs_valid_defaults(mock_get):
    mock_get.return_value = {"logs": []}
    result = get_audit_logs()
    assert isinstance(result, dict)
    mock_get.assert_called_once()


# -----------------------------
# User Management Tests
# -----------------------------

@patch("core_command.get_request")
def test_get_user_valid_by_user_id(mock_get):
    mock_get.return_value = {"user": {"id": "123"}}
    result = get_user(user_id="123")
    assert isinstance(result, dict)

@patch("core_command.get_request")
def test_get_user_valid_by_external_id(mock_get):
    mock_get.return_value = {"user": {"external_id": "abc"}}
    result = get_user(external_id="abc")
    assert isinstance(result, dict)

def test_get_user_invalid_both_ids_missing():
    with pytest.raises(ValueError, match="Exactly one of user_id or external_id"):
        get_user()

def test_get_user_invalid_both_ids_given():
    with pytest.raises(ValueError, match="Exactly one of user_id or external_id"):
        get_user(user_id="123", external_id="abc")


@patch("core_command.post_request")
def test_create_user_valid(mock_post):
    mock_post.return_value = {"user": {"external_id": "abc"}}
    result = create_user(external_id="abc", first_name="John", last_name="Doe")
    assert isinstance(result, dict)

def test_create_user_invalid_missing_external_id():
    with pytest.raises(ValueError, match="Exactly one of user_id or external_id"):
        create_user()


@patch("core_command.patch_request")
def test_update_user_valid(mock_patch):
    mock_patch.return_value = {"updated": True}
    result = update_user(user_id="123", email="test@example.com")
    assert isinstance(result, dict)

def test_update_user_invalid_missing_both_ids():
    with pytest.raises(ValueError, match="Exactly one of user_id or external_id"):
        update_user()

@patch("core_command.delete_request")
def test_delete_user_valid(mock_delete):
    mock_delete.return_value = {"deleted": True}
    result = delete_user(user_id="123")
    assert isinstance(result, dict)

def test_delete_user_invalid_missing_ids():
    with pytest.raises(ValueError, match="Exactly one of user_id or external_id"):
        delete_user()
