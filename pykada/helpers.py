"""
Shared utility functions for pykada.

Provides input validation helpers (:func:`require_non_empty_str`,
:func:`check_user_external_id`, :func:`verify_csv_columns`), random-string
generators, date/time format validators, and the
:func:`copy_docstring_from` decorator used to propagate docstrings from
client methods onto their functional wrapper equivalents.
"""
import csv
import os
import random
import re
import string
import typing
from typing import Optional
from typeguard import typechecked
import inspect


def remove_null_fields(obj: dict):
    """
    Removes fields with a value of None from a dictionary.
    :param obj:
    :return: A dictionary with no values of None
    """
    return {k: v for k, v in obj.items() if v is not None}


@typechecked
def require_non_empty_str(value: str, field_name: str, idx: Optional[int] = None) -> None:
    """
    Ensures that a value is a non-empty string.

    :param value: The string value to check.
    :param field_name: The name of the field for error messaging.
    :param idx: Optional index for context.
    :raises ValueError: If value is not a non-empty string.
    """
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        if idx is not None:
            msg += f" (at index {idx})"
        raise ValueError(msg)


def check_user_external_id(user_id: str = None, external_id: str = None,
                           email: str = None, employee_id: str = None):
    """
    Check that exactly one user identifier is provided.
    Raises ValueError if none or more than one are provided.

    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :param email: The user's email address.
    :type email: Optional[str]
    :param employee_id: The user's employee ID.
    :type employee_id: Optional[str]
    :return: A dictionary containing the provided identifier.
    """
    provided = [v for v in (user_id, external_id, email, employee_id) if v is not None]
    if len(provided) != 1:
        raise ValueError(
            "Exactly one of user_id, external_id, email, or employee_id must be provided."
        )

    params = {"user_id": user_id, "external_id": external_id,
              "email": email, "employee_id": employee_id}
    params = remove_null_fields(params)
    return params


def verify_csv_columns(file_path: str, expected_headers_list: typing.List[str]) -> None:
    """
    Verifies that a CSV file exists and contains exactly the columns specified
    in expected_headers_list. Column order does not matter.

    :param file_path: The path to the CSV file.
    :param expected_headers_list: The exact column names expected in the CSV header.
    :raises FileNotFoundError: If the file does not exist.
    :raises ValueError: If expected_headers_list is empty, the file has no header row,
                        or the columns do not match.
    """
    if not expected_headers_list:
        raise ValueError("expected_headers_list cannot be empty.")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at '{file_path}'")

    expected_headers_set: typing.Set[str] = set(expected_headers_list)
    expected_column_count = len(expected_headers_list)

    with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        try:
            headers = next(reader)
        except StopIteration:
            raise ValueError(f"File '{file_path}' is empty or has no header row.")

    if len(headers) != expected_column_count:
        raise ValueError(
            f"File '{file_path}' has {len(headers)} column(s) but expected "
            f"{expected_column_count}. Columns found: {headers}"
        )

    actual_headers_set = set(headers)
    if actual_headers_set != expected_headers_set:
        missing = expected_headers_set - actual_headers_set
        extra = actual_headers_set - expected_headers_set
        raise ValueError(
            f"File '{file_path}' has incorrect column names. "
            f"Missing: {missing}, Unexpected: {extra}"
        )


def generate_random_alphanumeric_string(length=16):
    """
    Generate a random alphanumeric string of the specified length.
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def generate_random_numeric_string(length=16):
    """
    Generate a random numeric string of the specified length.
    """
    characters = string.digits
    return ''.join(random.choice(characters) for _ in range(length))



def is_valid_date(date_str: str) -> bool:
    """
    Validates that a date string is in YYYY-MM-DD format.
    """
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    return bool(re.match(pattern, date_str))


def is_valid_time(time_str: str) -> bool:
    """
    Validates that a time string is in HH:MM format (00:00 to 23:59) with required leading zeros.
    """
    pattern = r"^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
    return bool(re.match(pattern, time_str))




def copy_docstring_from(source_func, note=None):
    """
    A decorator that copies and cleans the docstring from a source function
    and optionally appends a note to the end.
    """

    def wrapper(target_func):
        # Get the original docstring and handle cases where it might be empty
        original_doc = source_func.__doc__
        if not original_doc:
            original_doc = ""

        # Use inspect.cleandoc to fix any odd indentation from the source
        cleaned_doc = inspect.cleandoc(original_doc)

        # Append the note if one is provided
        if note:
            # The horizontal line (---) adds a nice visual separation
            target_func.__doc__ = f"{cleaned_doc}\n\n---\n\n**Note:** {note}"
        else:
            target_func.__doc__ = cleaned_doc

        return target_func

    return wrapper