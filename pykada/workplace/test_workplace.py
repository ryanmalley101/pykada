import base64
import types
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from typeguard import TypeCheckError

from pykada.endpoints import (
    GUEST_DENY_LIST_ENDPOINT,
    GUEST_SITES_ENDPOINT,
    GUEST_VISITS_ENDPOINT,
    V2_GUEST_APPROVED_LISTS_ENDPOINT as LISTS,
    V2_GUEST_EVENTS_ENDPOINT as EVENTS,
    V2_GUEST_HOSTS_ENDPOINT as HOSTS,
    V2_GUEST_TYPES_ENDPOINT as TYPES,
)
from pykada.workplace import (
    add_people_to_approved_lists,
    create_guest_deny_list,
    create_guest_event,
    delete_guest_deny_list,
    delete_guest_event,
    get_all_approved_list_members,
    get_all_approved_lists,
    get_all_guest_events,
    get_all_guest_hosts,
    get_all_guest_types,
    get_all_guest_visits,
    get_approved_list_members,
    get_approved_lists,
    get_guest_event,
    get_guest_events,
    get_guest_hosts,
    get_guest_sites,
    get_guest_types,
    get_guest_visits,
    remove_people_from_approved_lists,
    reset_approved_list,
)

RM = "pykada.verkada_requests.VerkadaRequestManager"
T0 = "2025-01-17T00:00:00Z"
T1 = "2025-01-17T12:00:00Z"
E0 = 1737072000  # T0 as epoch seconds
E1 = E0 + 12 * 3600
PERSON = {"full_name": "Ada Lovelace", "email": "ada@example.com", "approved_list_ids": ["l1"]}


REQUEST_CASES = [
    # v1
    (get_guest_sites, {}, "get", GUEST_SITES_ENDPOINT, {}),
    (get_guest_visits, {"site_id": "s1", "start_time": T0, "end_time": T1}, "get",
     GUEST_VISITS_ENDPOINT, {"params": {"site_id": "s1", "start_time": E0, "end_time": E1}}),
    (get_guest_visits, {"site_id": "s1", "start_time": T0, "end_time": T1, "page_size": 50,
                        "page_token": "p"}, "get", GUEST_VISITS_ENDPOINT,
     {"params": {"site_id": "s1", "start_time": E0, "end_time": E1, "page_size": 50,
                 "page_token": "p"}}),
    (delete_guest_deny_list, {"site_id": "s1"}, "delete", GUEST_DENY_LIST_ENDPOINT,
     {"params": {"site_id": "s1"}}),
    # events
    (get_guest_events, {"site_id": "s1", "start_time": datetime(2025, 1, 17, tzinfo=timezone.utc),
                        "end_time": T1, "limit": 200, "cursor": "c"}, "get", EVENTS,
     {"params": {"site_id": "s1", "start_time": T0, "end_time": T1, "limit": 200,
                 "cursor": "c"}}),
    (get_guest_event, {"guest_event_id": "ev1"}, "get", f"{EVENTS}/ev1", {}),
    (delete_guest_event, {"guest_event_id": "ev1"}, "delete", f"{EVENTS}/ev1", {}),
    # hosts and types
    (get_guest_hosts, {"site_id": "s1", "email": "h@example.com"}, "get", HOSTS,
     {"params": {"site_id": "s1", "email": "h@example.com"}}),
    (get_guest_types, {"site_id": "s1", "limit": 10}, "get", TYPES,
     {"params": {"site_id": "s1", "limit": 10}}),
    # approved lists
    (get_approved_lists, {}, "get", LISTS, {"params": {}}),
    (get_approved_lists, {"site_id": "s1", "limit": 1000}, "get", LISTS,
     {"params": {"site_id": "s1", "limit": 1000}}),
    (get_approved_list_members, {"approved_list_id": "l1", "cursor": "c"}, "get",
     f"{LISTS}/l1", {"params": {"cursor": "c"}}),
    (add_people_to_approved_lists, {"people": [PERSON]}, "patch", f"{LISTS}/add",
     {"payload": {"people": [PERSON]}}),
    (remove_people_from_approved_lists, {"people": [{"external_id": "x"}]}, "patch",
     f"{LISTS}/remove", {"payload": {"people": [{"external_id": "x"}]}}),
    (reset_approved_list, {"approved_list_id": "l1"}, "patch", f"{LISTS}/l1/reset", {}),
]


@pytest.mark.parametrize("func, kwargs, method, url, request_kwargs", REQUEST_CASES,
                         ids=[f"{c[0].__name__}-{i}" for i, c in enumerate(REQUEST_CASES)])
def test_request_shape(func, kwargs, method, url, request_kwargs):
    with patch(f"{RM}.{method}", return_value={"ok": True}) as mock:
        assert func(**kwargs) == {"ok": True}
    mock.assert_called_once_with(url, **request_kwargs)


# ——— deny lists (v1) ——— #

@patch(f"{RM}.post", return_value={"org_id": "o1"})
def test_create_guest_deny_list_encodes_csv(mock_post, tmp_path):
    csv_file = tmp_path / "deny.csv"
    csv_file.write_bytes(b"first_name,last_name\nJohn,Smith\n")
    create_guest_deny_list(str(csv_file), "s1")
    mock_post.assert_called_once_with(GUEST_DENY_LIST_ENDPOINT, params={"site_id": "s1"}, payload={
        "base64_ascii_deny_list_csv": base64.b64encode(csv_file.read_bytes()).decode("ascii")})


@pytest.mark.parametrize("args, match", [(("", "s1"), "filename"), (("f.csv", ""), "site_id")])
def test_create_guest_deny_list_validation(args, match):
    with pytest.raises(ValueError, match=match):
        create_guest_deny_list(*args)


# ——— visits (v1) ——— #

@patch(f"{RM}.get")
def test_get_all_guest_visits_splits_into_day_windows(mock_get):
    mock_get.side_effect = [
        {"visits": [{"visit_id": "a"}], "next_page_token": "p2"},
        {"visits": [{"visit_id": "b"}]},
        {"visits": [{"visit_id": "c"}]},
        {"visits": []},
    ]
    start = datetime(2025, 1, 17, tzinfo=timezone.utc)
    result = get_all_guest_visits("s1", start, start + timedelta(days=2, hours=6))
    assert isinstance(result, types.GeneratorType)
    assert [v["visit_id"] for v in result] == ["a", "b", "c"]
    windows = [(c.kwargs["params"]["start_time"], c.kwargs["params"]["end_time"])
               for c in mock_get.call_args_list]
    assert windows == [(E0, E0 + 86400), (E0, E0 + 86400),
                       (E0 + 86400, E0 + 2 * 86400), (E0 + 2 * 86400, E0 + 2 * 86400 + 6 * 3600)]
    assert mock_get.call_args_list[1].kwargs["params"]["page_token"] == "p2"


@patch(f"{RM}.get", return_value={"visits": []})
def test_get_all_guest_visits_zero_length_range_makes_one_request(mock_get):
    list(get_all_guest_visits("s1", T0, T0))
    assert mock_get.call_count == 1


@pytest.mark.parametrize("call, match", [
    (lambda: get_guest_visits("", T0, T1), "site_id"),
    (lambda: get_guest_visits("s1", T0, "2025-01-18T00:00:01Z"), "at most one day"),
    (lambda: get_guest_visits("s1", T0, T1, page_size=300), "page_size"),
    (lambda: get_guest_visits("s1", "2025-01-17T00:00:00", T1), "timezone"),
    (lambda: get_all_guest_visits("s1", T1, T0), "before"),
    (lambda: get_all_guest_visits("", T0, T1), "site_id"),
])
def test_visits_validation(call, match):
    with pytest.raises(ValueError, match=match):
        call()


def test_get_guest_visits_rejects_epoch_ints():
    with pytest.raises(TypeCheckError):
        get_guest_visits("s1", 0, 100)


# ——— guest events ——— #

@patch(f"{RM}.post", return_value={"guest_event_id": "ev1"})
def test_create_guest_event_normalizes_times(mock_post):
    start = datetime(2025, 3, 1, 9, 0, tzinfo=timezone.utc)
    create_guest_event("s1", "gt1", "h1",
                       event_times=[{"start_time": start, "end_time": "2025-03-01T17:00:00Z"}],
                       event_name="Open House",
                       invitees=[{"full_name": "Ada Lovelace", "notes": "VIP"}],
                       rsvp_enabled=True)
    mock_post.assert_called_once_with(EVENTS, payload={
        "site_id": "s1", "guest_type_id": "gt1", "host_id": "h1",
        "event_times": [{"start_time": "2025-03-01T09:00:00Z",
                         "end_time": "2025-03-01T17:00:00Z"}],
        "event_name": "Open House",
        "invitees": [{"full_name": "Ada Lovelace", "notes": "VIP"}],
        "rsvp_enabled": True,
    })


SPAN = {"start_time": T0, "end_time": T1}


@pytest.mark.parametrize("kwargs, match", [
    ({"event_times": []}, "between 1 and 30"),
    ({"event_times": [SPAN] * 31}, "between 1 and 30"),
    ({"event_times": [{"start_time": T0}]}, r"event_times\[0\]"),
    ({"event_times": [{"start_time": T0, "end_time": "tomorrow"}]}, r"event_times\[0\].end_time"),
    ({"event_times": [SPAN], "invitees": [{"email": "a@b.com"}]}, r"invitees\[0\].full_name"),
    ({"event_times": [SPAN], "invitees": [{"full_name": "A B", "notes": "x" * 101}]},
     "100 characters"),
])
def test_create_guest_event_validation(kwargs, match):
    with pytest.raises(ValueError, match=match):
        create_guest_event("s1", "gt1", "h1", **kwargs)


@pytest.mark.parametrize("call, match", [
    (lambda: create_guest_event("", "gt1", "h1", [SPAN]), "site_id"),
    (lambda: get_guest_events("", T0, T1), "site_id"),
    (lambda: get_guest_events("s1", T0, T1, limit=201), "between 1 and 200"),
    (lambda: get_guest_event(""), "guest_event_id"),
    (lambda: delete_guest_event(" "), "guest_event_id"),
])
def test_events_validation(call, match):
    with pytest.raises(ValueError, match=match):
        call()


# ——— hosts, types, approved lists ——— #

@pytest.mark.parametrize("call, match", [
    (lambda: get_guest_hosts(""), "site_id"),
    (lambda: get_guest_hosts("s1", limit=201), "between 1 and 200"),
    (lambda: get_guest_types(""), "site_id"),
    (lambda: get_approved_lists(limit=1001), "between 1 and 1000"),
    (lambda: get_approved_list_members(""), "approved_list_id"),
    (lambda: reset_approved_list(""), "approved_list_id"),
    (lambda: add_people_to_approved_lists([]), "between 1 and 100"),
    (lambda: remove_people_from_approved_lists([{"person_id": "p"}] * 101), "between 1 and 100"),
])
def test_lists_validation(call, match):
    with pytest.raises(ValueError, match=match):
        call()


# ——— pagination generators ——— #

@pytest.mark.parametrize("gen_func, kwargs, url, items_key", [
    (get_all_guest_events, {"site_id": "s1", "start_time": T0, "end_time": T1}, EVENTS, "items"),
    (get_all_guest_hosts, {"site_id": "s1"}, HOSTS, "items"),
    (get_all_guest_types, {"site_id": "s1"}, TYPES, "items"),
    (get_all_approved_lists, {"site_id": "s1"}, LISTS, "items"),
    (get_all_approved_list_members, {"approved_list_id": "l1"}, f"{LISTS}/l1", "people"),
])
def test_get_all_walks_cursor_pages(gen_func, kwargs, url, items_key):
    with patch(f"{RM}.get") as mock_get:
        mock_get.side_effect = [{items_key: [1, 2], "cursor": "c1"},
                                {items_key: [3], "cursor": None}]
        result = gen_func(**kwargs)
        assert isinstance(result, types.GeneratorType)
        assert list(result) == [1, 2, 3]
    assert [c.args[0] for c in mock_get.call_args_list] == [url, url]
    assert mock_get.call_args_list[1].kwargs["params"]["cursor"] == "c1"
