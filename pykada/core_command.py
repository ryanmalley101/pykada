"""
Core Command API client and functional wrappers for pykada.

The :class:`CoreCommandClient` provides access to organization-wide audit
logs and user management (create, read, update, delete) through Verkada's
v2 Core API.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Generator, Optional, Union

from typeguard import typechecked

from pykada.api_tokens import VerkadaTokenManager
from pykada.endpoints import V2_AUDIT_LOGS_ENDPOINT, V2_CORE_USERS_ENDPOINT
from pykada.helpers import (
    check_limit,
    check_user_id_or_external_id,
    copy_docstring_from,
    remove_null_fields,
    require_non_empty_str,
    to_iso8601,
)
from pykada.verkada_client import BaseClient
from pykada.verkada_requests import VerkadaRequestManager

Timestamp = Union[datetime, str]


class CoreCommandClient(BaseClient):
    """
    Client for interacting with Verkada's Core API.
    This client provides methods to retrieve audit logs and manage users.
    """

    def __init__(self,
                 api_key: Optional[str] = None,
                 token_manager: Optional[VerkadaTokenManager] = None,
                 request_manager: Optional[VerkadaRequestManager] = None,
                 api_version: Optional[str] = None):
        super().__init__(api_key, token_manager, request_manager, api_version)

    @typechecked
    def get_all_audit_logs(self,
                           start_time: Optional[Timestamp] = None,
                           end_time: Optional[Timestamp] = None,
                           use_processed_timestamp: Optional[bool] = None
                           ) -> Generator[Dict[str, Any], None, None]:
        """
        Returns all audit log entries in a time range, walking all pages automatically.

        If ``end_time`` is omitted it is pinned to the current time before the
        first request, so entries written while paginating can't shift items
        between pages.

        :param start_time: Start of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to one hour before
            ``end_time``.
        :param end_time: End of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to now.
        :param use_processed_timestamp: If True, filter on when entries finished
            processing rather than when the action occurred. Useful for
            regular polling so late-processed entries are still captured.
        :return: A generator that yields individual audit log entry dictionaries.
        :rtype: Generator
        """
        if end_time is None:
            end_time = datetime.now(timezone.utc)
        params = {
            "start_time": start_time,
            "end_time": end_time,
            "use_processed_timestamp": use_processed_timestamp,
        }
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_audit_logs(**kwargs),
            initial_params=params,
        )

    @typechecked
    def get_audit_logs(self,
                       start_time: Optional[Timestamp] = None,
                       end_time: Optional[Timestamp] = None,
                       use_processed_timestamp: Optional[bool] = None,
                       limit: Optional[int] = None,
                       cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve one page of audit log entries.

        :param start_time: Start of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to one hour before
            ``end_time``.
        :param end_time: End of the time range, as a timezone-aware
            ``datetime`` or ISO 8601 string. Defaults to now. Set it
            explicitly when paginating so the result set is stable.
        :param use_processed_timestamp: If True, filter on when entries finished
            processing rather than when the action occurred. Entries from
            before 2025-08-12 don't support this.
        :param limit: Maximum entries per page (1 to 200, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``limit`` is outside 1-200 or a timestamp is invalid.
        """
        check_limit(limit, 200)

        params = remove_null_fields({
            "start_time": to_iso8601(start_time, "start_time"),
            "end_time": to_iso8601(end_time, "end_time"),
            "use_processed_timestamp": use_processed_timestamp,
            "limit": limit,
            "cursor": cursor,
        })
        return self.request_manager.get(V2_AUDIT_LOGS_ENDPOINT, params=params)

    @typechecked
    def get_user(self,
                 user_id: Optional[str] = None,
                 external_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve a user by user ID or external ID.
        Exactly one of ``user_id`` or ``external_id`` must be provided.

        :param user_id: The Verkada user ID (a UUID).
        :param external_id: The customer-managed external ID set on the user.
        :return: The user object.
        :raises ValueError: If not exactly one identifier is provided.
        """
        params = check_user_id_or_external_id(user_id, external_id)
        return self.request_manager.get(V2_CORE_USERS_ENDPOINT, params=params)

    @typechecked
    def resolve_user_id(self, external_id: str) -> str:
        """
        Look up the Verkada user ID for an external ID.

        Many v2 endpoints identify users only by ``user_id`` in the URL path.
        Use this to translate an external ID first; it costs one API call.

        :param external_id: The customer-managed external ID set on the user.
        :return: The Verkada user ID.
        :raises ValueError: If ``external_id`` is empty.
        :raises VerkadaNotFoundError: If no user has that external ID.
        """
        require_non_empty_str(external_id, "external_id")
        return self.get_user(external_id=external_id)["user_id"]

    @typechecked
    def create_user(self,
                    external_id: Optional[str] = None,
                    company_name: Optional[str] = None,
                    department: Optional[str] = None,
                    department_id: Optional[str] = None,
                    email: Optional[str] = None,
                    employee_id: Optional[str] = None,
                    employee_title: Optional[str] = None,
                    employee_type: Optional[str] = None,
                    first_name: Optional[str] = None,
                    last_name: Optional[str] = None,
                    middle_name: Optional[str] = None,
                    phone: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a user in the organization.

        At least one of ``email``, ``first_name``, or ``last_name`` is required.

        :param external_id: Optional customer-managed external ID, usable to
            identify the user in later requests.
        :param company_name: Optional company name.
        :param department: Optional department name.
        :param department_id: Optional department ID.
        :param email: Optional email address.
        :param employee_id: Optional employee ID (need not be unique).
        :param employee_title: Optional employee title.
        :param employee_type: Optional employee type.
        :param first_name: Optional first name.
        :param last_name: Optional last name.
        :param middle_name: Optional middle name.
        :param phone: Optional phone number (E.164 preferred).
        :return: The created user object, including its ``user_id``.
        :raises ValueError: If none of email, first_name, or last_name is given.
        """
        if not any((email, first_name, last_name)):
            raise ValueError(
                "At least one of email, first_name, or last_name must be provided."
            )
        payload = remove_null_fields({
            "company_name": company_name,
            "department": department,
            "department_id": department_id,
            "email": email,
            "employee_id": employee_id,
            "employee_title": employee_title,
            "employee_type": employee_type,
            "external_id": external_id,
            "first_name": first_name,
            "last_name": last_name,
            "middle_name": middle_name,
            "phone": phone,
        })
        return self.request_manager.post(V2_CORE_USERS_ENDPOINT, payload=payload)

    @typechecked
    def update_user(self,
                    user_id: Optional[str] = None,
                    external_id: Optional[str] = None,
                    new_external_id: Optional[str] = None,
                    company_name: Optional[str] = None,
                    department: Optional[str] = None,
                    department_id: Optional[str] = None,
                    email: Optional[str] = None,
                    employee_id: Optional[str] = None,
                    employee_title: Optional[str] = None,
                    employee_type: Optional[str] = None,
                    first_name: Optional[str] = None,
                    last_name: Optional[str] = None,
                    middle_name: Optional[str] = None,
                    phone: Optional[str] = None) -> Dict[str, Any]:
        """
        Update a user's metadata. Only the fields provided are changed.

        Identify the user with exactly one of ``user_id`` or ``external_id``.
        To change the user's external ID, pass ``new_external_id``.

        :param user_id: The Verkada user ID of the user to update.
        :param external_id: The current external ID of the user to update.
        :param new_external_id: A new external ID to set on the user.
        :param company_name: Optional company name.
        :param department: Optional department name.
        :param department_id: Optional department ID.
        :param email: Optional email address.
        :param employee_id: Optional employee ID.
        :param employee_title: Optional employee title.
        :param employee_type: Optional employee type.
        :param first_name: Optional first name.
        :param last_name: Optional last name.
        :param middle_name: Optional middle name.
        :param phone: Optional phone number.
        :return: The updated user object.
        :raises ValueError: If not exactly one identifier is provided, or no
            fields to update are given.
        """
        params = check_user_id_or_external_id(user_id, external_id)
        payload = remove_null_fields({
            "company_name": company_name,
            "department": department,
            "department_id": department_id,
            "email": email,
            "employee_id": employee_id,
            "employee_title": employee_title,
            "employee_type": employee_type,
            "external_id": new_external_id,
            "first_name": first_name,
            "last_name": last_name,
            "middle_name": middle_name,
            "phone": phone,
        })
        if not payload:
            raise ValueError("At least one field to update must be provided.")
        return self.request_manager.patch(V2_CORE_USERS_ENDPOINT, params=params,
                                          payload=payload)

    @typechecked
    def delete_user(self,
                    user_id: Optional[str] = None,
                    external_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete a user by user ID or external ID.
        Exactly one of ``user_id`` or ``external_id`` must be provided.

        :param user_id: The Verkada user ID.
        :param external_id: The customer-managed external ID.
        :return: An empty dict (the API returns 204 No Content).
        :raises ValueError: If not exactly one identifier is provided.
        """
        params = check_user_id_or_external_id(user_id, external_id)
        return self.request_manager.delete(V2_CORE_USERS_ENDPOINT, params=params)


# ---------------------------------------------------------------------------
# Module-level default client — shared across all functional wrappers.
# ---------------------------------------------------------------------------
_default_core_client: Optional[CoreCommandClient] = None


def _get_default_client() -> CoreCommandClient:
    global _default_core_client
    if _default_core_client is None:
        _default_core_client = CoreCommandClient()
    return _default_core_client


_WRAPPER_NOTE = ("This is a functional wrapper for its equivalent method in the "
                 "CoreCommandClient. It reuses a module-level client configured "
                 "from VERKADA_API_KEY, making it best for one-off scripts. For "
                 "multiple API calls or a non-default key, instantiate a "
                 "CoreCommandClient directly.")


@copy_docstring_from(CoreCommandClient.get_all_audit_logs, note=_WRAPPER_NOTE)
@typechecked
def get_all_audit_logs(start_time: Optional[Timestamp] = None,
                       end_time: Optional[Timestamp] = None,
                       use_processed_timestamp: Optional[bool] = None):
    return _get_default_client().get_all_audit_logs(start_time, end_time,
                                                    use_processed_timestamp)


@copy_docstring_from(CoreCommandClient.get_audit_logs, note=_WRAPPER_NOTE)
@typechecked
def get_audit_logs(start_time: Optional[Timestamp] = None,
                   end_time: Optional[Timestamp] = None,
                   use_processed_timestamp: Optional[bool] = None,
                   limit: Optional[int] = None,
                   cursor: Optional[str] = None):
    return _get_default_client().get_audit_logs(start_time, end_time,
                                                use_processed_timestamp, limit, cursor)


@copy_docstring_from(CoreCommandClient.get_user, note=_WRAPPER_NOTE)
@typechecked
def get_user(user_id: Optional[str] = None, external_id: Optional[str] = None):
    return _get_default_client().get_user(user_id, external_id)


@copy_docstring_from(CoreCommandClient.resolve_user_id, note=_WRAPPER_NOTE)
@typechecked
def resolve_user_id(external_id: str):
    return _get_default_client().resolve_user_id(external_id)


@copy_docstring_from(CoreCommandClient.create_user, note=_WRAPPER_NOTE)
@typechecked
def create_user(external_id: Optional[str] = None, company_name: Optional[str] = None,
                department: Optional[str] = None, department_id: Optional[str] = None,
                email: Optional[str] = None, employee_id: Optional[str] = None,
                employee_title: Optional[str] = None, employee_type: Optional[str] = None,
                first_name: Optional[str] = None, last_name: Optional[str] = None,
                middle_name: Optional[str] = None, phone: Optional[str] = None):
    return _get_default_client().create_user(
        external_id, company_name, department, department_id, email, employee_id,
        employee_title, employee_type, first_name, last_name, middle_name, phone)


@copy_docstring_from(CoreCommandClient.update_user, note=_WRAPPER_NOTE)
@typechecked
def update_user(user_id: Optional[str] = None, external_id: Optional[str] = None,
                new_external_id: Optional[str] = None, company_name: Optional[str] = None,
                department: Optional[str] = None, department_id: Optional[str] = None,
                email: Optional[str] = None, employee_id: Optional[str] = None,
                employee_title: Optional[str] = None, employee_type: Optional[str] = None,
                first_name: Optional[str] = None, last_name: Optional[str] = None,
                middle_name: Optional[str] = None, phone: Optional[str] = None):
    return _get_default_client().update_user(
        user_id, external_id, new_external_id, company_name, department, department_id,
        email, employee_id, employee_title, employee_type, first_name, last_name,
        middle_name, phone)


@copy_docstring_from(CoreCommandClient.delete_user, note=_WRAPPER_NOTE)
@typechecked
def delete_user(user_id: Optional[str] = None, external_id: Optional[str] = None):
    return _get_default_client().delete_user(user_id, external_id)
