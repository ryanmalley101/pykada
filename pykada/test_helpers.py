import os
import tempfile
import pytest
from typeguard import TypeCheckError

from pykada.helpers import (
    remove_null_fields,
    require_non_empty_str,
    check_user_external_id,
    verify_csv_columns,
    is_valid_date,
    is_valid_time,
    generate_random_alphanumeric_string,
    generate_random_numeric_string,
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
