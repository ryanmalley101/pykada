import pytest
from unittest.mock import patch
from pykada.core_command import (
    get_audit_logs, get_all_audit_logs, get_user, create_user, update_user, delete_user
)

# -----------------------------
# Audit Log Tests
# -----------------------------

def test_get_audit_logs_invalid_page_size():
    with pytest.raises(ValueError, match="page_size must be between 0 and 200"):
        get_audit_logs(page_size=500)

@patch("pykada.verkada_requests.VerkadaRequestManager.get")
def test_get_audit_logs_valid_defaults(mock_get):
    mock_get.return_value = {"logs": []}
    result = get_audit_logs()
    assert isinstance(result, dict)
    mock_get.assert_called_once()


@patch("pykada.verkada_requests.VerkadaRequestManager.get",
       return_value={"audit_logs": [], "next_page_token": None})
def test_get_all_audit_logs_returns_generator(mock_get):
    import types
    result = get_all_audit_logs()
    assert isinstance(result, types.GeneratorType)


# -----------------------------
# User Management Tests
# -----------------------------

@patch("pykada.verkada_requests.VerkadaRequestManager.get")
def test_get_user_valid_by_user_id(mock_get):
    mock_get.return_value = {"user": {"id": "123"}}
    result = get_user(user_id="123")
    assert isinstance(result, dict)

@patch("pykada.verkada_requests.VerkadaRequestManager.get")
def test_get_user_valid_by_external_id(mock_get):
    mock_get.return_value = {"user": {"external_id": "abc"}}
    result = get_user(external_id="abc")
    assert isinstance(result, dict)

def test_get_user_invalid_both_ids_missing():
    with pytest.raises(ValueError, match="Exactly one of user_id, external_id, email, or employee_id"):
        get_user()

def test_get_user_invalid_both_ids_given():
    with pytest.raises(ValueError, match="Exactly one of user_id, external_id, email, or employee_id"):
        get_user(user_id="123", external_id="abc")


@patch("pykada.verkada_requests.VerkadaRequestManager.post")
def test_create_user_valid(mock_post):
    mock_post.return_value = {"user": {"external_id": "abc"}}
    result = create_user(external_id="abc", first_name="John", last_name="Doe")
    assert isinstance(result, dict)

@patch("pykada.verkada_requests.VerkadaRequestManager.put")
def test_update_user_valid(mock_put):
    mock_put.return_value = {"updated": True}
    result = update_user(user_id="123", email="test@example.com")
    assert isinstance(result, dict)

def test_update_user_invalid_missing_both_ids():
    with pytest.raises(ValueError, match="Exactly one of user_id, external_id, email, or employee_id"):
        update_user()

@patch("pykada.verkada_requests.VerkadaRequestManager.delete")
def test_delete_user_valid(mock_delete):
    mock_delete.return_value = {"deleted": True}
    result = delete_user(user_id="123")
    assert isinstance(result, dict)

def test_delete_user_invalid_missing_ids():
    with pytest.raises(ValueError, match="Exactly one of user_id, external_id, email, or employee_id"):
        delete_user()
