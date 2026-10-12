import pytest
from unittest.mock import patch

from pykada.endpoints import HELIX_BATCH_ENDPOINT, V2_BATCH_JOBS_ENDPOINT
from pykada.helix import create_helix_events_batch, get_batch_job_status
from pykada.helix import (
    create_helix_event_type, get_helix_event_types, update_helix_event_type,
    delete_helix_event_type, create_helix_event, get_helix_event,
    update_helix_event, delete_helix_event, search_helix_events
)

# -----------------------------
# Helix Event Type Tests
# -----------------------------

def test_create_helix_event_type_invalid_schema_raises():
    with pytest.raises(ValueError):
        create_helix_event_type({}, "eventName")
    with pytest.raises(ValueError):
        create_helix_event_type({"name": ""}, "eventName")
    with pytest.raises(ValueError):
        create_helix_event_type({"": "string"}, "eventName")
    with pytest.raises(ValueError):
        create_helix_event_type({"a" * 21: "string"}, "eventName")

@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"success": True})
def test_create_helix_event_type_valid(mock_post):
    result = create_helix_event_type({"item": "string"}, "eventName")
    assert isinstance(result, dict)

def test_get_helix_event_types_empty_params():
    with pytest.raises(ValueError):
        get_helix_event_types(event_type_uid="")
    with pytest.raises(ValueError):
        get_helix_event_types(name="")

@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"event_types": []})
def test_get_helix_event_types_valid(mock_get):
    assert isinstance(get_helix_event_types(), dict)

@patch("pykada.verkada_requests.VerkadaRequestManager.patch", return_value={"success": True})
def test_update_helix_event_type_valid(mock_patch):
    result = update_helix_event_type("uid123", {"item": "string"}, "newName")
    assert isinstance(result, dict)

@patch("pykada.verkada_requests.VerkadaRequestManager.delete", return_value={"deleted": True})
def test_delete_helix_event_type_valid(mock_delete):
    result = delete_helix_event_type("uid123")
    assert isinstance(result, dict)

# -----------------------------
# Helix Event Tests
# -----------------------------

def test_create_helix_event_invalid_inputs():
    with pytest.raises(ValueError):
        create_helix_event("", "uid", 1000)
    with pytest.raises(ValueError):
        create_helix_event("cam", "", 1000)
    with pytest.raises(ValueError):
        create_helix_event("cam", "uid", -1)

@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"created": True})
def test_create_helix_event_valid(mock_post):
    result = create_helix_event("cam123", "uid456", 1234567890)
    assert isinstance(result, dict)

def test_get_helix_event_invalid_inputs():
    with pytest.raises(ValueError):
        get_helix_event("", 1234567890, "uid")
    with pytest.raises(ValueError):
        get_helix_event("cam", -1, "uid")
    with pytest.raises(ValueError):
        get_helix_event("cam", 1234567890, "")

@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"event": {}})
def test_get_helix_event_valid(mock_get):
    result = get_helix_event("cam123", 1234567890, "uid456")
    assert isinstance(result, dict)

@patch("pykada.verkada_requests.VerkadaRequestManager.patch", return_value={"updated": True})
def test_update_helix_event_valid(mock_patch):
    result = update_helix_event("cam", 1234567890, "uid", flagged=True)
    assert isinstance(result, dict)

@patch("pykada.verkada_requests.VerkadaRequestManager.delete", return_value={"deleted": True})
def test_delete_helix_event_valid(mock_delete):
    result = delete_helix_event("cam", 1234567890, "uid")
    assert isinstance(result, dict)

# -----------------------------
# Helix Event Search Tests
# -----------------------------

def test_search_helix_events_invalid_inputs():
    with pytest.raises(ValueError):
        search_helix_events([], 1000, "uid", True, ["keyword"], 500)
    with pytest.raises(ValueError):
        search_helix_events(["cam"], 1000, "", True, ["keyword"], 500)
    with pytest.raises(ValueError):
        search_helix_events(["cam"], 1000, "uid", True, ["keyword"], -1)
    with pytest.raises(ValueError):
        search_helix_events(["cam"], -1, "uid", True, ["keyword"], 500)
    with pytest.raises(ValueError):
        search_helix_events(["cam"], 500, "uid", True, ["keyword"], 1000)
    with pytest.raises(ValueError):
        search_helix_events(["cam"], 1000, "uid", True, [""], 500)

@patch("pykada.verkada_requests.VerkadaRequestManager.post", return_value={"results": []})
def test_search_helix_events_valid(mock_post):
    result = search_helix_events(["cam123"], 2000, "uid123", True, ["motion"], 1000)
    assert isinstance(result, dict)



# ---------- batch create and job status ----------

_BATCH_EVENT = {"camera_id": "c1", "event_type_uid": "t1", "time_ms": 1700000000000}


@patch("pykada.verkada_requests.VerkadaRequestManager.post",
       return_value={"job_id": "j1", "status": "pending"})
def test_create_helix_events_batch(mock_post):
    assert create_helix_events_batch([_BATCH_EVENT])["job_id"] == "j1"
    mock_post.assert_called_once_with(HELIX_BATCH_ENDPOINT, payload={"items": [_BATCH_EVENT]})


@pytest.mark.parametrize("events, match", [
    ([], "between 1 and 1000"),
    ([_BATCH_EVENT] * 1001, "between 1 and 1000"),
    ([{"camera_id": "c1"}], r"events\[0\] is missing \['event_type_uid', 'time_ms'\]"),
])
def test_create_helix_events_batch_validation(events, match):
    with pytest.raises(ValueError, match=match):
        create_helix_events_batch(events)


@patch("pykada.verkada_requests.VerkadaRequestManager.get", return_value={"status": "completed"})
def test_get_batch_job_status(mock_get):
    assert get_batch_job_status("j1") == {"status": "completed"}
    mock_get.assert_called_once_with(f"{V2_BATCH_JOBS_ENDPOINT}/j1")


def test_get_batch_job_status_empty_id():
    with pytest.raises(ValueError, match="job_id"):
        get_batch_job_status("")
