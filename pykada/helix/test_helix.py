import pytest
from unittest.mock import patch
from helix import (
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
        create_helix_event_type({"a"*21: "string"}, "eventName")

@patch("helix.post_request")
def test_create_helix_event_type_valid(mock_post):
    mock_post.return_value = {"success": True}
    result = create_helix_event_type({"item": "string"}, "eventName")
    assert isinstance(result, dict)

def test_get_helix_event_types_empty_params():
    with pytest.raises(ValueError):
        get_helix_event_types(event_type_uid="")
    with pytest.raises(ValueError):
        get_helix_event_types(name="")

@patch("helix.get_request")
def test_get_helix_event_types_valid(mock_get):
    mock_get.return_value = {"event_types": []}
    assert isinstance(get_helix_event_types(), dict)

@patch("helix.patch_request")
def test_update_helix_event_type_valid(mock_patch):
    mock_patch.return_value = {"success": True}
    result = update_helix_event_type("uid123", {"item": "string"}, "newName")
    assert isinstance(result, dict)

@patch("helix.delete_request")
def test_delete_helix_event_type_valid(mock_delete):
    mock_delete.return_value = {"deleted": True}
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

@patch("helix.post_request")
def test_create_helix_event_valid(mock_post):
    mock_post.return_value = {"created": True}
    result = create_helix_event("cam123", "uid456", 1234567890)
    assert isinstance(result, dict)

def test_get_helix_event_invalid_inputs():
    with pytest.raises(ValueError):
        get_helix_event("", 1234567890, "uid")
    with pytest.raises(ValueError):
        get_helix_event("cam", -1, "uid")
    with pytest.raises(ValueError):
        get_helix_event("cam", 1234567890, "")

@patch("helix.get_request")
def test_get_helix_event_valid(mock_get):
    mock_get.return_value = {"event": {}}
    result = get_helix_event("cam123", 1234567890, "uid456")
    assert isinstance(result, dict)

@patch("helix.patch_request")
def test_update_helix_event_valid(mock_patch):
    mock_patch.return_value = {"updated": True}
    result = update_helix_event("cam", 1234567890, "uid", flagged=True)
    assert isinstance(result, dict)

@patch("helix.delete_request")
def test_delete_helix_event_valid(mock_delete):
    mock_delete.return_value = {"deleted": True}
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
        search_helix_events(["cam"], 500, "uid", True, ["keyword"], 1000)  # start > end
    with pytest.raises(ValueError):
        search_helix_events(["cam"], 1000, "uid", True, [""], 500)

@patch("helix.post_request")
def test_search_helix_events_valid(mock_post):
    mock_post.return_value = {"results": []}
    result = search_helix_events(["cam123"], 2000, "uid123", True, ["motion"], 1000)
    assert isinstance(result, dict)
