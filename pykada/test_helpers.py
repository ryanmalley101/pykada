import os
from datetime import datetime, timedelta, timezone
import tempfile
import pytest
from typeguard import TypeCheckError

from pykada.helpers import (
    remove_null_fields,
    require_non_empty_str,
    check_user_external_id,
    check_user_id_or_external_id,
    path_segment,
    require_choice,
    check_limit,
    verify_csv_columns,
    is_valid_date,
    is_valid_time,
    generate_random_alphanumeric_string,
    generate_random_numeric_string,
    copy_docstring_from,
    to_iso8601,
    to_iso8601_duration,
    to_unix_seconds,
)


# ---------- remove_null_fields ----------

def test_remove_null_removes_none_values():
    assert remove_null_fields({"a": 1, "b": None, "c": "x"}) == {"a": 1, "c": "x"}


def test_remove_null_all_none_returns_empty():
    assert remove_null_fields({"a": None, "b": None}) == {}


def test_remove_null_no_none_unchanged():
    d = {"a": 1, "b": 2}
    assert remove_null_fields(d) == d


def test_remove_null_keeps_falsy_non_none():
    assert remove_null_fields({"a": 0, "b": False, "c": "", "d": None}) == {
        "a": 0, "b": False, "c": ""
    }


# ---------- require_non_empty_str ----------

def test_require_non_empty_str_valid():
    require_non_empty_str("hello", "field")


def test_require_non_empty_str_empty_raises():
    with pytest.raises(ValueError, match="field"):
        require_non_empty_str("", "field")


def test_require_non_empty_str_whitespace_raises():
    with pytest.raises(ValueError, match="field"):
        require_non_empty_str("   ", "field")


def test_require_non_empty_str_non_str_raises_type_error():
    with pytest.raises(TypeCheckError):
        require_non_empty_str(None, "field")


def test_require_non_empty_str_with_index_includes_index_in_message():
    with pytest.raises(ValueError, match="at index 3"):
        require_non_empty_str("", "item", idx=3)


# ---------- check_user_external_id ----------

def test_check_user_id_returns_correct_dict():
    assert check_user_external_id(user_id="u1") == {"user_id": "u1"}


def test_check_external_id_returns_correct_dict():
    assert check_user_external_id(external_id="e1") == {"external_id": "e1"}


def test_check_email_returns_correct_dict():
    assert check_user_external_id(email="a@b.com") == {"email": "a@b.com"}


def test_check_employee_id_returns_correct_dict():
    assert check_user_external_id(employee_id="emp1") == {"employee_id": "emp1"}


def test_check_no_id_provided_raises():
    with pytest.raises(ValueError, match="Exactly one"):
        check_user_external_id()


def test_check_two_ids_provided_raises():
    with pytest.raises(ValueError, match="Exactly one"):
        check_user_external_id(user_id="u1", external_id="e1")


def test_check_three_ids_provided_raises():
    with pytest.raises(ValueError, match="Exactly one"):
        check_user_external_id(user_id="u1", external_id="e1", email="a@b.com")


def test_check_result_has_no_none_values():
    result = check_user_external_id(user_id="u1")
    assert None not in result.values()


# ---------- verify_csv_columns ----------

def _write_csv(content: str) -> str:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8"
    )
    f.write(content)
    f.close()
    return f.name


def test_verify_csv_valid():
    path = _write_csv("License Plate,Name\nABC123,stolen\n")
    try:
        verify_csv_columns(path, ["License Plate", "Name"])
    finally:
        os.unlink(path)


def test_verify_csv_column_order_does_not_matter():
    path = _write_csv("Name,License Plate\nstolen,ABC123\n")
    try:
        verify_csv_columns(path, ["License Plate", "Name"])
    finally:
        os.unlink(path)


def test_verify_csv_file_not_found_raises():
    with pytest.raises(FileNotFoundError):
        verify_csv_columns("/no/such/file.csv", ["col"])


def test_verify_csv_empty_expected_list_raises():
    path = _write_csv("col\nval\n")
    try:
        with pytest.raises(ValueError, match="cannot be empty"):
            verify_csv_columns(path, [])
    finally:
        os.unlink(path)


def test_verify_csv_empty_file_raises():
    path = _write_csv("")
    try:
        with pytest.raises(ValueError, match="empty or has no header"):
            verify_csv_columns(path, ["col"])
    finally:
        os.unlink(path)


def test_verify_csv_wrong_column_count_raises():
    path = _write_csv("License Plate\nABC123\n")
    try:
        with pytest.raises(ValueError, match="column"):
            verify_csv_columns(path, ["License Plate", "Name"])
    finally:
        os.unlink(path)


def test_verify_csv_wrong_column_names_raises():
    path = _write_csv("Plate,Description\nABC,stolen\n")
    try:
        with pytest.raises(ValueError, match="incorrect column"):
            verify_csv_columns(path, ["License Plate", "Name"])
    finally:
        os.unlink(path)


# ---------- is_valid_date ----------

def test_is_valid_date_valid_dates():
    assert is_valid_date("2025-01-15") is True
    assert is_valid_date("2000-12-31") is True
    assert is_valid_date("1999-06-01") is True


def test_is_valid_date_missing_leading_zeros():
    assert is_valid_date("2025-1-5") is False


def test_is_valid_date_wrong_separator():
    assert is_valid_date("01/15/2025") is False


def test_is_valid_date_compact_format():
    assert is_valid_date("20250115") is False


def test_is_valid_date_garbage():
    assert is_valid_date("not-a-date") is False


# ---------- is_valid_time ----------

def test_is_valid_time_boundaries():
    assert is_valid_time("00:00") is True
    assert is_valid_time("23:59") is True


def test_is_valid_time_typical():
    assert is_valid_time("09:30") is True
    assert is_valid_time("14:45") is True


def test_is_valid_time_missing_leading_zero():
    assert is_valid_time("9:30") is False
    assert is_valid_time("9:05") is False


def test_is_valid_time_hour_out_of_range():
    assert is_valid_time("24:00") is False


def test_is_valid_time_minute_out_of_range():
    assert is_valid_time("23:60") is False


def test_is_valid_time_wrong_separator():
    assert is_valid_time("09-30") is False


def test_is_valid_time_garbage():
    assert is_valid_time("noon") is False


# ---------- random generators ----------

def test_generate_alphanumeric_default_length():
    assert len(generate_random_alphanumeric_string()) == 16


def test_generate_alphanumeric_custom_length():
    assert len(generate_random_alphanumeric_string(20)) == 20


def test_generate_alphanumeric_only_alnum():
    assert generate_random_alphanumeric_string(200).isalnum()


def test_generate_numeric_default_length():
    assert len(generate_random_numeric_string()) == 16


def test_generate_numeric_custom_length():
    assert len(generate_random_numeric_string(12)) == 12


def test_generate_numeric_only_digits():
    assert generate_random_numeric_string(200).isdigit()


# ---------- copy_docstring_from ----------

def test_copy_docstring_from_copies_source_doc():
    def source():
        """Source docstring."""

    @copy_docstring_from(source)
    def target():
        pass

    assert target.__doc__ == "Source docstring."


def test_copy_docstring_from_appends_note():
    def source():
        """Source docstring."""

    @copy_docstring_from(source, note="Use carefully.")
    def target():
        pass

    assert "Source docstring." in target.__doc__
    assert "Use carefully." in target.__doc__
    assert "---" in target.__doc__


def test_copy_docstring_from_no_source_doc():
    def source():
        pass

    @copy_docstring_from(source)
    def target():
        pass

    assert target.__doc__ == ""


def test_copy_docstring_from_preserves_callable():
    def source():
        """Doc."""

    @copy_docstring_from(source)
    def target():
        return 42

    assert target() == 42


# ---------- to_iso8601 ----------

def test_to_iso8601_none_passes_through():
    assert to_iso8601(None) is None


def test_to_iso8601_utc_datetime_uses_z_suffix():
    dt = datetime(2025, 7, 17, 21, 6, 20, tzinfo=timezone.utc)
    assert to_iso8601(dt) == "2025-07-17T21:06:20Z"


def test_to_iso8601_offset_datetime_converted_to_utc():
    dt = datetime(2025, 7, 17, 14, 6, 20, tzinfo=timezone(timedelta(hours=-7)))
    assert to_iso8601(dt) == "2025-07-17T21:06:20Z"


def test_to_iso8601_keeps_subsecond_precision():
    dt = datetime(2025, 7, 17, 21, 6, 20, 123000, tzinfo=timezone.utc)
    assert to_iso8601(dt) == "2025-07-17T21:06:20.123000Z"


def test_to_iso8601_naive_datetime_raises():
    with pytest.raises(ValueError, match="timezone-aware"):
        to_iso8601(datetime(2025, 7, 17, 21, 6, 20), "start_time")


@pytest.mark.parametrize("value", [
    "2025-07-17T21:06:20Z",
    "2025-07-17T21:06:20z",
    "2025-07-17T21:06:20+00:00",
    "2025-07-17T14:06:20-07:00",
    "2025-07-17T21:06:20.123Z",
])
def test_to_iso8601_valid_strings_returned_unchanged(value):
    assert to_iso8601(value) == value


def test_to_iso8601_string_without_timezone_raises():
    with pytest.raises(ValueError, match="timezone"):
        to_iso8601("2025-07-17T21:06:20")


@pytest.mark.parametrize("value", ["", "yesterday", "1721250380", "2025-13-01T00:00:00Z"])
def test_to_iso8601_invalid_strings_raise(value):
    with pytest.raises(ValueError, match="ISO 8601"):
        to_iso8601(value)


def test_to_iso8601_epoch_int_raises_type_error():
    with pytest.raises(TypeError, match="datetime or ISO 8601"):
        to_iso8601(1721250380)


def test_to_iso8601_error_message_uses_field_name():
    with pytest.raises(ValueError, match="end_time"):
        to_iso8601("nope", "end_time")


# ---------- to_iso8601_duration ----------

def test_to_iso8601_duration_none_passes_through():
    assert to_iso8601_duration(None) is None


@pytest.mark.parametrize("td, expected", [
    (timedelta(0), "PT0S"),
    (timedelta(seconds=1), "PT1S"),
    (timedelta(minutes=5), "PT5M"),
    (timedelta(hours=1), "PT1H"),
    (timedelta(days=1), "P1D"),
    (timedelta(weeks=1), "P7D"),
    (timedelta(days=1, hours=2, minutes=3, seconds=4), "P1DT2H3M4S"),
    (timedelta(seconds=1, milliseconds=500), "PT1.5S"),
])
def test_to_iso8601_duration_from_timedelta(td, expected):
    assert to_iso8601_duration(td) == expected


def test_to_iso8601_duration_negative_raises():
    with pytest.raises(ValueError, match="negative"):
        to_iso8601_duration(timedelta(seconds=-1))


@pytest.mark.parametrize("value", ["PT5M", "PT1H", "P1D", "P1W", "PT0S", "P1DT12H", "PT1.5S"])
def test_to_iso8601_duration_valid_strings_returned_unchanged(value):
    assert to_iso8601_duration(value) == value


@pytest.mark.parametrize("value", ["", "P", "PT", "5m", "1_hour", "15_minutes", "P1H", "PT1D"])
def test_to_iso8601_duration_invalid_strings_raise(value):
    with pytest.raises(ValueError, match="ISO 8601 duration"):
        to_iso8601_duration(value)


def test_to_iso8601_duration_int_raises_type_error():
    with pytest.raises(TypeError):
        to_iso8601_duration(300)


# ---------- check_user_id_or_external_id ----------

def test_check_user_id_or_external_id_user_id():
    assert check_user_id_or_external_id(user_id="u1") == {"user_id": "u1"}


def test_check_user_id_or_external_id_external_id():
    assert check_user_id_or_external_id(external_id="e1") == {"external_id": "e1"}


@pytest.mark.parametrize("kwargs", [{}, {"user_id": "u1", "external_id": "e1"}])
def test_check_user_id_or_external_id_requires_exactly_one(kwargs):
    with pytest.raises(ValueError, match="Exactly one of user_id or external_id"):
        check_user_id_or_external_id(**kwargs)


# ---------- path_segment ----------

def test_path_segment_plain_id_unchanged():
    assert path_segment("8438a7f2-fdbc-4392", "camera_id") == "8438a7f2-fdbc-4392"


def test_path_segment_encodes_reserved_characters():
    assert path_segment("AB C/12?", "license_plate") == "AB%20C%2F12%3F"


@pytest.mark.parametrize("value", ["", "   "])
def test_path_segment_empty_raises(value):
    with pytest.raises(ValueError, match="camera_id"):
        path_segment(value, "camera_id")


# ---------- require_choice ----------

def test_require_choice_none_passes():
    require_choice(None, {"A": "a"}, "field")


def test_require_choice_valid_value_from_enum_dict():
    require_choice("a", {"A": "a", "B": "b"}, "field")


def test_require_choice_valid_list():
    require_choice(["a", "b"], ["a", "b", "c"], "field")


def test_require_choice_invalid_value_raises_with_field_name():
    with pytest.raises(ValueError, match="interval 'x' is not one of"):
        require_choice("x", {"A": "a"}, "interval")


def test_require_choice_invalid_list_member_raises():
    with pytest.raises(ValueError, match="'z'"):
        require_choice(["a", "z"], {"A": "a"}, "types")


# ---------- check_limit ----------

@pytest.mark.parametrize("limit", [None, 1, 200])
def test_check_limit_valid(limit):
    check_limit(limit, 200)


@pytest.mark.parametrize("limit", [0, -1, 201])
def test_check_limit_out_of_range_raises(limit):
    with pytest.raises(ValueError, match="limit must be between 1 and 200"):
        check_limit(limit, 200)


# ---------- to_unix_seconds ----------

def test_to_unix_seconds_none():
    assert to_unix_seconds(None) is None


@pytest.mark.parametrize("value", [
    datetime(2025, 7, 17, 21, 6, 20, tzinfo=timezone.utc),
    "2025-07-17T21:06:20Z",
    "2025-07-17T14:06:20-07:00",
])
def test_to_unix_seconds(value):
    assert to_unix_seconds(value) == 1752786380


def test_to_unix_seconds_rejects_naive():
    with pytest.raises(ValueError, match="timezone"):
        to_unix_seconds("2025-07-17T21:06:20")
