import pytest
from unittest.mock import patch, mock_open

from pykada.endpoints import (
    GUEST_DENY_LIST_ENDPOINT,
    GUEST_SITES_ENDPOINT,
    GUEST_VISITS_ENDPOINT,
    GUEST_V2_EVENTS_ENDPOINT,
    GUEST_V2_APPROVED_LISTS_ADD_ENDPOINT,
    GUEST_V2_APPROVED_LISTS_REMOVE_ENDPOINT,
)
from pykada.workplace import (
    get_guest_sites,
    delete_guest_deny_list,
    create_guest_deny_list,
    get_guest_visits,
    get_all_guest_visits,
    get_guest_events,
    create_guest_event,
    get_guest_event,
    delete_guest_event,
    add_people_to_approved_lists,
    remove_people_from_approved_lists,
)


# ——— get_guest_sites ——— #

@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"sites": []})
def test_get_guest_sites_returns_dict(mock_get):
    result = get_guest_sites()
    assert isinstance(result, dict)
    mock_get.assert_called_once_with(GUEST_SITES_ENDPOINT)


# ——— delete_guest_deny_list ——— #

def test_delete_guest_deny_list_empty_site_id_raises():
    with pytest.raises(ValueError, match="site_id"):
        delete_guest_deny_list("")


@patch("pykada.verkada_requests.VerkadaRequestManager.delete", return_value={"success": True})
def test_delete_guest_deny_list_valid(mock_delete):
    result = delete_guest_deny_list("site123")
    assert isinstance(result, dict)
    mock_delete.assert_called_once_with(GUEST_DENY_LIST_ENDPOINT, params={"site_id": "site123"})


# ——— create_guest_deny_list ——— #

def test_create_guest_deny_list_empty_filename_raises():
    with pytest.raises(ValueError, match="filename"):
        create_guest_deny_list("", "site123")


def test_create_guest_deny_list_empty_site_id_raises():
    with pytest.raises(ValueError, match="site_id"):
        create_guest_deny_list("file.csv", "")


@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"success": True})
@patch("builtins.open", new_callable=mock_open, read_data=b"name,dob\nJohn,1990\n")
def test_create_guest_deny_list_valid(mock_file, mock_post):
    result = create_guest_deny_list("file.csv", "site123")
    assert isinstance(result, dict)
    mock_file.assert_called_once_with("file.csv", "rb")
    _, kwargs = mock_post.call_args
    assert kwargs["params"] == {"site_id": "site123"}
    assert "base64_ascii_deny_list_csv" in kwargs["payload"]


# ——— get_guest_visits ——— #

def test_get_guest_visits_empty_site_id_raises():
    with pytest.raises(ValueError, match="site_id"):
        get_guest_visits("", 0, 100)


def test_get_guest_visits_time_range_too_large_raises():
    with pytest.raises(ValueError, match="time range"):
        get_guest_visits("site123", 0, 90000)


def test_get_guest_visits_invalid_page_size_raises():
    with pytest.raises(ValueError, match="page_size"):
        get_guest_visits("site123", 0, 100, page_size=300)


@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"visits": []})
def test_get_guest_visits_valid(mock_get):
    result = get_guest_visits("site123", 0, 100)
    assert isinstance(result, dict)
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["site_id"] == "site123"


# ——— get_all_guest_visits ——— #

@patch("pykada.verkada_requests.VerkadaRequestManager.get",
       return_value={"visits": [], "next_page_token": None})
def test_get_all_guest_visits_returns_generator(mock_get):
    import types
    result = get_all_guest_visits("site123", 0, 86400)
    assert isinstance(result, types.GeneratorType)


# ——— get_guest_events ——— #

def test_get_guest_events_empty_site_id_raises():
    with pytest.raises(ValueError, match="site_id"):
        get_guest_events("", "2025-01-01T00:00:00Z", "2025-01-02T00:00:00Z")


def test_get_guest_events_empty_start_time_raises():
    with pytest.raises(ValueError, match="start_time"):
        get_guest_events("site1", "", "2025-01-02T00:00:00Z")


def test_get_guest_events_empty_end_time_raises():
    with pytest.raises(ValueError, match="end_time"):
        get_guest_events("site1", "2025-01-01T00:00:00Z", "")


@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"events": []})
def test_get_guest_events_valid(mock_get):
    result = get_guest_events("site1", "2025-01-01T00:00:00Z", "2025-01-02T00:00:00Z")
    assert isinstance(result, dict)


# ——— create_guest_event ——— #

def test_create_guest_event_empty_site_id_raises():
    with pytest.raises(ValueError, match="site_id"):
        create_guest_event("", "gt1", "host1", [{"start": "t1", "end": "t2"}])


def test_create_guest_event_empty_guest_type_id_raises():
    with pytest.raises(ValueError, match="guest_type_id"):
        create_guest_event("site1", "", "host1", [{"start": "t1", "end": "t2"}])


def test_create_guest_event_empty_host_id_raises():
    with pytest.raises(ValueError, match="host_id"):
        create_guest_event("site1", "gt1", "", [{"start": "t1", "end": "t2"}])


@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"event_id": "ev1"})
def test_create_guest_event_minimal(mock_post):
    result = create_guest_event(
        "site1", "gt1", "host1", [{"start": "t1", "end": "t2"}]
    )
    assert isinstance(result, dict)
    _, kwargs = mock_post.call_args
    assert kwargs["payload"]["site_id"] == "site1"
    assert kwargs["payload"]["guest_type_id"] == "gt1"
    assert kwargs["payload"]["host_id"] == "host1"


@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"event_id": "ev2"})
def test_create_guest_event_with_optional_fields(mock_post):
    result = create_guest_event(
        "site1", "gt1", "host1",
        event_times=[{"start": "t1", "end": "t2"}],
        event_name="Conference",
        rsvp_enabled=True,
        walk_in_enabled=False,
    )
    assert isinstance(result, dict)
    _, kwargs = mock_post.call_args
    assert kwargs["payload"]["event_name"] == "Conference"
    assert kwargs["payload"]["rsvp_enabled"] is True


# ——— get_guest_event ——— #

def test_get_guest_event_empty_id_raises():
    with pytest.raises(ValueError, match="guest_event_id"):
        get_guest_event("")


@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"event_id": "ev1"})
def test_get_guest_event_valid(mock_get):
    result = get_guest_event("ev1")
    assert isinstance(result, dict)
    expected_url = f"{GUEST_V2_EVENTS_ENDPOINT}/ev1"
    mock_get.assert_called_once_with(expected_url)


# ——— delete_guest_event ——— #

def test_delete_guest_event_empty_id_raises():
    with pytest.raises(ValueError, match="guest_event_id"):
        delete_guest_event("")


@patch("pykada.verkada_requests.VerkadaRequestManager.delete", return_value={"deleted": True})
def test_delete_guest_event_valid(mock_delete):
    result = delete_guest_event("ev1")
    assert isinstance(result, dict)
    expected_url = f"{GUEST_V2_EVENTS_ENDPOINT}/ev1"
    mock_delete.assert_called_once_with(expected_url)


# ——— add/remove people from approved lists ——— #

@patch("pykada.verkada_requests.VerkadaRequestManager.patch", return_value={"added": True})
def test_add_people_to_approved_lists(mock_patch):
    people = [{"name": "Alice", "list_id": "lst1"}]
    result = add_people_to_approved_lists(people)
    assert isinstance(result, dict)
    mock_patch.assert_called_once_with(
        GUEST_V2_APPROVED_LISTS_ADD_ENDPOINT, payload={"people": people}
    )


@patch("pykada.verkada_requests.VerkadaRequestManager.patch", return_value={"removed": True})
def test_remove_people_from_approved_lists(mock_patch):
    people = [{"name": "Bob", "list_id": "lst1"}]
    result = remove_people_from_approved_lists(people)
    assert isinstance(result, dict)
    mock_patch.assert_called_once_with(
        GUEST_V2_APPROVED_LISTS_REMOVE_ENDPOINT, payload={"people": people}
    )
