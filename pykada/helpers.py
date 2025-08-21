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


def check_user_external_id(user_id: str = None, external_id:str = None):
    """
    Check if only one of user_id or external_id are provided.
    Throw an error if neither or both are provided.
    The AC API requires exactly one of these identifiers.

    :param user_id: The internal user identifier.
    :type user_id: Optional[str]
    :param external_id: The external user identifier.
    :type external_id: Optional[str]
    :return: A dictionary containing the provided identifier.
    """
    if (user_id is None and external_id is None) or (user_id is not None and external_id is not None):
        raise ValueError("Exactly one of user_id or external_id must be provided, not both or neither.")

    params = {"user_id": user_id, "external_id": external_id}
    params = remove_null_fields(params)
    return params


def verify_csv_columns(file_path: str, expected_headers_list: typing.List[str]) -> bool:
    """
    Verifies if a CSV file exists and contains exactly the columns
    specified in the expected_headers_list. The order of columns
    in the file does not matter.

    Args:
        file_path: The path to the CSV file.
        expected_headers_list: A list of strings representing the exact
                                names and number of columns expected in the CSV header.

    Returns:
        True if the file exists and has the specified columns,
        False otherwise.
    """
    # Convert the expected headers list to a set for efficient comparison (order doesn't matter)
    expected_headers_set: typing.Set[str] = set(expected_headers_list)
    expected_column_count = len(expected_headers_list)

    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        return False

    if expected_column_count == 0:
        print("Error: expected_headers_list cannot be empty.")
        return False

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)

            # Read the header row
            try:
                headers = next(reader)
            except StopIteration:
                print(f"Error: File '{file_path}' is empty or has no header row.")
                return False
            except Exception as e:
                 print(f"Error reading header from '{file_path}': {e}")
                 return False

            # Check if the number of columns matches the expected count
            if len(headers) != expected_column_count:
                print(f"Error: File '{file_path}' does not have the expected number of columns.")
                print(f"Expected {expected_column_count}, Found {len(headers)}.")
                print(f"Columns found: {headers}")
                return False

            # Check if the column names are the expected ones (order doesn't matter)
            actual_headers_set = set(headers)

            if actual_headers_set != expected_headers_set:
                print(f"Error: File '{file_path}' has incorrect column names.")
                print(f"Expected names: {expected_headers_set}, Found names: {actual_headers_set}")
                return False

            # If all checks pass
            print(f"File '{file_path}' successfully verified: has the expected {expected_column_count} columns.")
            return True

    except Exception as e:
        # Catch other potential CSV reading errors
        print(f"An unexpected error occurred while processing '{file_path}': {e}")
        return False


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