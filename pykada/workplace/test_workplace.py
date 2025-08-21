import pytest
from unittest.mock import patch, mock_open
from pykada.workplace import *

# ------------------------
# get_guest_sites
# ------------------------

@patch("workplace.get_request")
def test_get_guest_sites_returns_dict(mock_get):
    mock_get.return_value = {"sites": []}
    result = get_guest_sites()
    assert isinstance(result, dict)

# ------------------------
# delete_guest_deny_list
# ------------------------

def test_delete_guest_deny_list_empty_site_id_raises():
    with pytest.raises(ValueError, match="site_id"):
        delete_guest_deny_list("")

@patch("workplace.delete_request")
def test_delete_guest_deny_list_valid(mock_delete):
    mock_delete.return_value = {"success": True}
    result = delete_guest_deny_list("site123")
    assert isinstance(result, dict)

# ------------------------
# create_guest_deny_list
# ------------------------

def test_create_guest_deny_list_empty_filename_raises():
    with pytest.raises(ValueError, match="filename"):
        create_guest_deny_list("", "site123")

def test_create_guest_deny_list_empty_site_id_raises():
    with pytest.raises(ValueError, match="site_id"):
        create_guest_deny_list("file.csv", "")

@patch("workplace.post_request")
@patch("builtins.open", new_callable=mock_open, read_data=b"test,data\n")
def test_create_guest_deny_list_valid(mock_file, mock_post):
    mock_post.return_value = {"success": True}
    result = create_guest_deny_list("file.csv", "site123")
    assert isinstance(result, dict)
    mock_file.assert_called_once_with("file.csv", "rb")

# ------------------------
# get_guest_visits
# ------------------------

def test_get_guest_visits_empty_site_id_raises():
    with pytest.raises(ValueError, match="site_id"):
        get_guest_visits("", 0, 100)

def test_get_guest_visits_time_range_too_large_raises():
    with pytest.raises(ValueError, match="time range"):
        get_guest_visits("site123", 0, 90000)

def test_get_guest_visits_invalid_page_size_raises():
    with pytest.raises(ValueError, match="page_size"):
        get_guest_visits("site123", 0, 100, page_size=300)

@patch("workplace.get_request")
def test_get_guest_visits_valid(mock_get):
    mock_get.return_value = {"visits": []}
    result = get_guest_visits("site123", 0, 100)
    assert isinstance(result, dict)
