import types
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from typeguard import TypeCheckError

from pykada.core_command import (
    CoreCommandClient,
    create_user,
    delete_user,
    get_all_audit_logs,
    get_audit_logs,
    get_user,
    resolve_user_id,
    update_user,
)
from pykada.endpoints import V2_AUDIT_LOGS_ENDPOINT, V2_CORE_USERS_ENDPOINT

RM = "pykada.verkada_requests.VerkadaRequestManager"


# -----------------------------
# Audit logs
# -----------------------------

@patch(f"{RM}.get", return_value={"items": [], "cursor": None})
def test_get_audit_logs_no_args_sends_no_params(mock_get):
    result = get_audit_logs()
    assert isinstance(result, dict)
    mock_get.assert_called_once_with(V2_AUDIT_LOGS_ENDPOINT, params={})


@patch(f"{RM}.get", return_value={"items": [], "cursor": None})
def test_get_audit_logs_normalizes_timestamps_and_paging(mock_get):
    start = datetime(2025, 1, 17, 9, 0, tzinfo=timezone.utc)
    get_audit_logs(start_time=start, end_time="2025-01-17T10:00:00Z",
                   use_processed_timestamp=True, limit=50, cursor="Mg")
    mock_get.assert_called_once_with(V2_AUDIT_LOGS_ENDPOINT, params={
        "start_time": "2025-01-17T09:00:00Z",
        "end_time": "2025-01-17T10:00:00Z",
        "use_processed_timestamp": True,
        "limit": 50,
        "cursor": "Mg",
    })


@pytest.mark.parametrize("limit", [0, 201])
def test_get_audit_logs_invalid_limit(limit):
    with pytest.raises(ValueError, match="limit must be between 1 and 200"):
        get_audit_logs(limit=limit)


def test_get_audit_logs_rejects_epoch_ints():
    with pytest.raises(TypeCheckError):
        get_audit_logs(start_time=1721250380)


def test_get_audit_logs_rejects_naive_datetime():
    with pytest.raises(ValueError, match="timezone-aware"):
        get_audit_logs(start_time=datetime(2025, 1, 17, 9, 0))


@patch(f"{RM}.get")
def test_get_all_audit_logs_walks_cursor_pages(mock_get):
    mock_get.side_effect = [
        {"items": [{"event_name": "a"}], "cursor": "c1"},
        {"items": [{"event_name": "b"}], "cursor": None},
    ]
    result = get_all_audit_logs(start_time="2025-01-17T09:00:00Z",
                                end_time="2025-01-17T10:00:00Z")
    assert isinstance(result, types.GeneratorType)
    assert [e["event_name"] for e in result] == ["a", "b"]
    first, second = (c.kwargs["params"] for c in mock_get.call_args_list)
    assert "cursor" not in first and first["limit"] == 100
    assert second["cursor"] == "c1"
    assert first["end_time"] == second["end_time"] == "2025-01-17T10:00:00Z"


@patch(f"{RM}.get", return_value={"items": [], "cursor": None})
def test_get_all_audit_logs_pins_end_time(mock_get):
    list(get_all_audit_logs())
    end_time = mock_get.call_args.kwargs["params"]["end_time"]
    assert end_time.endswith("Z")


# -----------------------------
# Users
# -----------------------------

@patch(f"{RM}.get", return_value={"user_id": "123", "active": True})
def test_get_user_by_user_id(mock_get):
    assert get_user(user_id="123") == {"user_id": "123", "active": True}
    mock_get.assert_called_once_with(V2_CORE_USERS_ENDPOINT, params={"user_id": "123"})


@patch(f"{RM}.get", return_value={"user_id": "123", "active": True})
def test_get_user_by_external_id(mock_get):
    get_user(external_id="abc")
    mock_get.assert_called_once_with(V2_CORE_USERS_ENDPOINT, params={"external_id": "abc"})


@pytest.mark.parametrize("kwargs", [{}, {"user_id": "123", "external_id": "abc"}])
def test_get_user_requires_exactly_one_id(kwargs):
    with pytest.raises(ValueError, match="Exactly one of user_id or external_id"):
        get_user(**kwargs)


@patch(f"{RM}.get", return_value={"user_id": "u-123", "active": True})
def test_resolve_user_id(mock_get):
    assert resolve_user_id("ext-1") == "u-123"
    mock_get.assert_called_once_with(V2_CORE_USERS_ENDPOINT, params={"external_id": "ext-1"})


def test_resolve_user_id_empty_raises():
    with pytest.raises(ValueError, match="external_id"):
        resolve_user_id("  ")


@patch(f"{RM}.post", return_value={"user_id": "u1", "active": True})
def test_create_user(mock_post):
    result = create_user(external_id="abc", first_name="John", last_name="Doe")
    assert result["user_id"] == "u1"
    mock_post.assert_called_once_with(V2_CORE_USERS_ENDPOINT, payload={
        "external_id": "abc", "first_name": "John", "last_name": "Doe",
    })


def test_create_user_requires_a_name_or_email():
    with pytest.raises(ValueError, match="email, first_name, or last_name"):
        create_user(external_id="abc", phone="+15555550123")


@patch(f"{RM}.patch", return_value={"user_id": "123", "active": True})
def test_update_user_by_user_id(mock_patch):
    update_user(user_id="123", email="test@example.com")
    mock_patch.assert_called_once_with(V2_CORE_USERS_ENDPOINT,
                                       params={"user_id": "123"},
                                       payload={"email": "test@example.com"})


@patch(f"{RM}.patch", return_value={"user_id": "123", "active": True})
def test_update_user_identifier_not_sent_in_body(mock_patch):
    update_user(external_id="old", new_external_id="new", first_name="Jane")
    mock_patch.assert_called_once_with(V2_CORE_USERS_ENDPOINT,
                                       params={"external_id": "old"},
                                       payload={"external_id": "new", "first_name": "Jane"})


def test_update_user_requires_exactly_one_id():
    with pytest.raises(ValueError, match="Exactly one of user_id or external_id"):
        update_user(email="test@example.com")


def test_update_user_requires_a_field():
    with pytest.raises(ValueError, match="At least one field"):
        update_user(user_id="123")


@patch(f"{RM}.delete", return_value={})
def test_delete_user(mock_delete):
    assert delete_user(external_id="abc") == {}
    mock_delete.assert_called_once_with(V2_CORE_USERS_ENDPOINT, params={"external_id": "abc"})


def test_delete_user_requires_exactly_one_id():
    with pytest.raises(ValueError, match="Exactly one of user_id or external_id"):
        delete_user()


def test_client_methods_typechecked():
    client = CoreCommandClient(api_key="key")
    with pytest.raises(TypeCheckError):
        client.get_user(user_id=123)
