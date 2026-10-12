"""
Access Control API client and functional wrappers for pykada.

The :class:`AccessControlClient` covers doors, access users and groups,
credentials (cards, license plates, MFA codes, QR codes, entry codes, BLE,
face unlock), access levels and their schedules, door exception calendars,
and scenarios (lockdowns) through Verkada's v2 Access API.

A few operations have no v2 endpoint yet and still use v1: access cards,
door unlocks, remote unlock, and looking a user up by email or employee ID
(:meth:`AccessControlClient.find_access_user`).

Most v2 user endpoints identify the user by Verkada ``user_id`` only. To work
from an external ID, translate it first with
:meth:`AccessControlClient.resolve_user_id`.

Module-level functional wrappers share a single lazily-initialized
:class:`AccessControlClient` instance.
"""
import re
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional, Union

from typeguard import typechecked

from pykada.api_tokens import VerkadaTokenManager
from pykada.endpoints import (
    ACCESS_ADMIN_UNLOCK_ENDPOINT,
    ACCESS_CARD_ACTIVATE_ENDPOINT,
    ACCESS_CARD_DEACTIVATE_ENDPOINT,
    ACCESS_CARD_ENDPOINT,
    ACCESS_REMOTE_UNLOCK_ACTIVATE_ENDPOINT,
    ACCESS_REMOTE_UNLOCK_DEACTIVATE_ENDPOINT,
    ACCESS_USER_ENDPOINT,
    ACCESS_USER_UNLOCK_ENDPOINT,
    V2_ACCESS_DOORS_ENDPOINT,
    V2_ACCESS_EXCEPTION_CALENDARS_ENDPOINT,
    V2_ACCESS_EXTERNAL_USERS_ENDPOINT,
    V2_ACCESS_GROUPS_ENDPOINT,
    V2_ACCESS_LEVELS_ENDPOINT,
    V2_ACCESS_LICENSE_PLATES_ENDPOINT,
    V2_ACCESS_MFA_CODES_ENDPOINT,
    V2_ACCESS_PASS_SDK_TOKEN_ENDPOINT,
    V2_ACCESS_SCENARIOS_ENDPOINT,
    V2_ACCESS_USERS_ENDPOINT,
)
from pykada.enums import DOOR_STATUS_ENUM, FREQUENCY_ENUM, WEEKDAY_FULL_ENUM
from pykada.helpers import (
    check_limit,
    check_user_external_id,
    check_user_id_or_external_id,
    copy_docstring_from,
    is_valid_date,
    is_valid_time,
    path_segment,
    remove_null_fields,
    require_choice,
    require_non_empty_str,
    to_iso8601,
)
from pykada.verkada_client import BaseClient
from pykada.verkada_requests import VerkadaRequestManager

Timestamp = Union[datetime, str]

_DIGITS_4_TO_16_RE = re.compile(r"^[0-9]{4,16}$")
_CODE_CHALLENGE_RE = re.compile(r"^[A-Za-z0-9_-]{43,128}$")
_HH_MM_SS_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d:[0-5]\d$")


def _digits_4_to_16(value: str, field_name: str) -> None:
    if not _DIGITS_4_TO_16_RE.match(value):
        raise ValueError(f"{field_name} must be 4 to 16 digits.")


def _parse_iso8601(value: str) -> datetime:
    return datetime.fromisoformat(value[:-1] + "+00:00" if value[-1:] in "Zz" else value)


def _hh_mm(value: str, field_name: str) -> str:
    if not is_valid_time(value):
        raise ValueError(
            f"{field_name} must be in HH:MM format (00:00 to 23:59) with leading zeros; "
            f"got {value!r}.")
    return value


def _weekly_rule(weekday: str) -> Dict[str, Any]:
    require_choice(weekday, WEEKDAY_FULL_ENUM, "weekday")
    return {"frequency": "WEEKLY", "interval": 1, "by_day": [weekday]}


@typechecked
def build_access_schedule_event(weekday: str, start_time: str, end_time: str) -> Dict[str, Any]:
    """
    Build a v2 Access Schedule Event: one weekly window during which an Access
    Level grants access.

    :param weekday: Full weekday name, e.g. ``"Monday"``
        (see :data:`pykada.enums.WEEKDAY_FULL_ENUM`).
    :param start_time: Local start time as ``HH:MM`` (``00:00`` to ``23:59``).
    :param end_time: Local end time as ``HH:MM``; must be after ``start_time``.
    :return: The event in the v2 request shape (with a weekly ``recurrence_rule``).
    :raises ValueError: If the weekday or times are invalid.
    """
    start = _hh_mm(start_time, "start_time")
    end = _hh_mm(end_time, "end_time")
    if end <= start:
        raise ValueError(f"end_time must be after start_time; got {start}-{end}.")
    return {"recurrence_rule": _weekly_rule(weekday), "start_time": start, "end_time": end}


def _schedule_events(events: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    built = []
    for idx, event in enumerate(events):
        missing = {"weekday", "start_time", "end_time"} - set(event)
        if missing:
            raise ValueError(
                f"access_schedule_events[{idx}] is missing {sorted(missing)}; each event "
                f"needs weekday, start_time and end_time.")
        built.append(build_access_schedule_event(event["weekday"], event["start_time"],
                                                 event["end_time"]))
    return built


class AccessControlClient(BaseClient):
    """
    Client for interacting with Verkada's Access Control API.
    """
    @typechecked
    def __init__(self,
                 api_key: Optional[str] = None,
                 token_manager: Optional[VerkadaTokenManager] = None,
                 request_manager: Optional[VerkadaRequestManager] = None,
                 api_version: Optional[str] = None):
        """
        Initializes the AccessControlClient.

        :param api_key: Optional API key for authentication. If not provided, it will be fetched from environment variables.
        :param token_manager: Optional custom VerkadaTokenManager instance.
        :param request_manager: Optional custom VerkadaRequestManager instance.
        :param api_version: Optional ``x-verkada-api-version`` header value.
        """
        super().__init__(api_key, token_manager, request_manager, api_version)

    def _user_url(self, user_id: str) -> str:
        return f"{V2_ACCESS_USERS_ENDPOINT}/{path_segment(user_id, 'user_id')}"

    def _user_or_external_url(self, user_id: Optional[str],
                              external_id: Optional[str]) -> str:
        check_user_id_or_external_id(user_id, external_id)
        if user_id is not None:
            return self._user_url(user_id)
        return (f"{V2_ACCESS_EXTERNAL_USERS_ENDPOINT}/"
                f"{path_segment(external_id, 'external_id')}")

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    @typechecked
    def resolve_user_id(self, external_id: str) -> str:
        """
        Look up the Verkada user ID for an external ID.

        Most v2 access user endpoints take ``user_id`` only. This costs one API
        call to ``GET /v2/core/users`` and needs Core read permission.

        :param external_id: The customer-managed external ID set on the user.
        :return: The Verkada user ID.
        :raises ValueError: If ``external_id`` is empty.
        :raises VerkadaNotFoundError: If no user has that external ID.
        """
        from pykada.core_command import CoreCommandClient
        return CoreCommandClient(request_manager=self.request_manager).resolve_user_id(
            external_id)

    @typechecked
    def get_all_access_users(self, include_visitors: Optional[bool] = None
                             ) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every access user in the organization, walking all pages automatically.

        :param include_visitors: If True, include visitors. Defaults to False.
        :return: A generator that yields individual access user dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_access_users(**kwargs),
            initial_params={"include_visitors": include_visitors},
        )

    @typechecked
    def get_access_users(self,
                         include_visitors: Optional[bool] = None,
                         limit: Optional[int] = None,
                         cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of access users.

        Each item has the user's ``user_id``, name, email, employee and
        department details, ``external_id``, ``is_visitor`` and profile photo
        metadata.

        :param include_visitors: If True, include visitors. Defaults to False.
        :param limit: Maximum users per page (1 to 1000, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``limit`` is outside 1-1000.
        """
        check_limit(limit, 1000)
        params = remove_null_fields({"include_visitors": include_visitors,
                                     "limit": limit, "cursor": cursor})
        return self.request_manager.get(V2_ACCESS_USERS_ENDPOINT, params=params)

    @typechecked
    def get_access_user(self, user_id: str) -> Dict[str, Any]:
        """
        Returns the core access information for a user.

        Includes start/end dates (RFC 3339), BLE and remote unlock state, entry
        code, and profile photo metadata. Credentials and group membership are
        not included; use :meth:`find_access_user` for the full v1 record.

        :param user_id: The Verkada user ID.
        :return: The access user.
        :raises ValueError: If ``user_id`` is empty.
        """
        return self.request_manager.get(self._user_url(user_id))

    @typechecked
    def find_access_user(self,
                         user_id: Optional[str] = None,
                         external_id: Optional[str] = None,
                         email: Optional[str] = None,
                         employee_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Look up an access user by user ID, external ID, email, or employee ID.

        Uses the v1 endpoint, which v2 has no equivalent for. Unlike
        :meth:`get_access_user` it returns the full record, including access
        groups, cards, license plates, MFA codes, QR codes and face credential.
        Exactly one identifier must be provided.

        :param user_id: The Verkada user ID.
        :param external_id: The customer-managed external ID.
        :param email: The user's email address.
        :param employee_id: The user's organization-defined employee ID.
        :return: The v1 Access Information Object.
        :raises ValueError: If not exactly one identifier is provided.
        """
        params = check_user_external_id(user_id, external_id, email, employee_id)
        return self.request_manager.get(ACCESS_USER_ENDPOINT, params=params)

    @typechecked
    def update_access_user_dates(self, user_id: str,
                                 start_date: Optional[Timestamp] = None,
                                 end_date: Optional[Timestamp] = None) -> Dict[str, Any]:
        """
        Set when a user's credentials become valid and/or stop being valid.

        Only the dates provided are changed. Before ``start_date`` and after
        ``end_date`` every access method for the user is denied.

        :param user_id: The Verkada user ID.
        :param start_date: When credentials become valid, as a timezone-aware
            ``datetime`` or ISO 8601 string with a timezone.
        :param end_date: When credentials stop being valid.
        :return: The updated access user.
        :raises ValueError: If ``user_id`` is empty, neither date is given, a
            date is invalid, or ``start_date`` is not before ``end_date``.
        """
        start = to_iso8601(start_date, "start_date")
        end = to_iso8601(end_date, "end_date")
        if start is None and end is None:
            raise ValueError("At least one of start_date or end_date must be provided.")
        if start is not None and end is not None and _parse_iso8601(start) >= _parse_iso8601(end):
            raise ValueError("start_date must be before end_date.")
        payload = remove_null_fields({"start_date": start, "end_date": end})
        return self.request_manager.patch(self._user_url(user_id), payload=payload)

    @typechecked
    def set_ble_unlock(self, user_id: str, active: bool) -> Dict[str, Any]:
        """
        Turn Bluetooth (BLE) unlock on or off for a user.

        :param user_id: The Verkada user ID.
        :param active: ``True`` to allow BLE unlock; ``False`` to revoke it.
        :return: ``{"user_id": str, "ble_unlock": bool}``.
        :raises ValueError: If ``user_id`` is empty.
        """
        return self.request_manager.put(f"{self._user_url(user_id)}/ble",
                                        payload={"active": active})

    @typechecked
    def activate_remote_unlock_for_user(self,
                                        user_id: Optional[str] = None,
                                        external_id: Optional[str] = None,
                                        email: Optional[str] = None,
                                        employee_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Allow a user to unlock doors remotely. Uses v1 (no v2 endpoint yet).
        Exactly one identifier must be provided.

        :param user_id: The Verkada user ID.
        :param external_id: The customer-managed external ID.
        :param email: The user's email address.
        :param employee_id: The user's employee ID.
        :return: The updated v1 Access Information Object.
        :raises ValueError: If not exactly one identifier is provided.
        """
        params = check_user_external_id(user_id, external_id, email, employee_id)
        return self.request_manager.put(ACCESS_REMOTE_UNLOCK_ACTIVATE_ENDPOINT, params=params)

    @typechecked
    def deactivate_remote_unlock_for_user(self,
                                          user_id: Optional[str] = None,
                                          external_id: Optional[str] = None,
                                          email: Optional[str] = None,
                                          employee_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Revoke a user's remote unlock. Uses v1 (no v2 endpoint yet).
        Exactly one identifier must be provided.

        :param user_id: The Verkada user ID.
        :param external_id: The customer-managed external ID.
        :param email: The user's email address.
        :param employee_id: The user's employee ID.
        :return: The updated v1 Access Information Object.
        :raises ValueError: If not exactly one identifier is provided.
        """
        params = check_user_external_id(user_id, external_id, email, employee_id)
        return self.request_manager.put(ACCESS_REMOTE_UNLOCK_DEACTIVATE_ENDPOINT, params=params)

    @typechecked
    def set_entry_code_for_user(self, user_id: str, entry_code: str,
                                override: Optional[bool] = None) -> Dict[str, Any]:
        """
        Set a user's keypad entry code (PIN).

        Entry codes must be unique within the organization. With
        ``override=True`` the code is taken from any other user that has it
        (their code is cleared); otherwise a duplicate raises
        ``VerkadaConflictError``.

        :param user_id: The Verkada user ID.
        :param entry_code: 4 to 16 digits.
        :param override: Take the code from another user if it's in use.
            Defaults to False.
        :return: ``{"user_id": str}``.
        :raises ValueError: If ``user_id`` is empty or ``entry_code`` isn't 4-16 digits.
        """
        _digits_4_to_16(entry_code, "entry_code")
        payload = remove_null_fields({"entry_code": entry_code, "override": override})
        return self.request_manager.put(f"{self._user_url(user_id)}/entry_code",
                                        payload=payload)

    @typechecked
    def remove_entry_code_for_user(self, user_id: str) -> Dict[str, Any]:
        """
        Remove a user's keypad entry code. Raises ``VerkadaNotFoundError`` if
        the user has none.

        :param user_id: The Verkada user ID.
        :return: An empty dict (the API returns 204 No Content).
        :raises ValueError: If ``user_id`` is empty.
        """
        return self.request_manager.delete(f"{self._user_url(user_id)}/entry_code")

    @typechecked
    def send_pass_app_invite_for_user(self, user_id: str,
                                      invitation_methods: Optional[List[str]] = None
                                      ) -> Dict[str, Any]:
        """
        Email a user an invitation to set up the Verkada Pass mobile app.

        :param user_id: The Verkada user ID.
        :param invitation_methods: Delivery channels. Only ``"email"`` is
            supported today (the default); others are reported back in
            ``invitations_failed``.
        :return: ``user_id``, ``invitations_sent`` and ``invitations_failed``.
        :raises ValueError: If ``user_id`` is empty.
        """
        payload = remove_null_fields({"invitation_methods": invitation_methods})
        return self.request_manager.post(f"{self._user_url(user_id)}/pass/invitations",
                                         payload=payload)

    @typechecked
    def create_pass_sdk_token(self, user_id: str, code_challenge: str) -> Dict[str, Any]:
        """
        Create a single-use Pass App SDK token for a user.

        Your backend passes the token to your mobile app, which exchanges it
        (with the PKCE ``code_verifier``) for a Pass App session. It expires
        after a few minutes.

        :param user_id: The Verkada user ID.
        :param code_challenge: PKCE challenge, ``base64url(SHA-256(code_verifier))``
            without ``=`` padding (43 to 128 characters).
        :return: ``{"sdk_token": str}``.
        :raises ValueError: If ``user_id`` is empty or ``code_challenge`` is malformed.
        """
        require_non_empty_str(user_id, "user_id")
        if not _CODE_CHALLENGE_RE.match(code_challenge):
            raise ValueError("code_challenge must be 43-128 base64url characters "
                             "(A-Z, a-z, 0-9, '-', '_') with no padding.")
        return self.request_manager.post(V2_ACCESS_PASS_SDK_TOKEN_ENDPOINT,
                                         payload={"user_id": user_id,
                                                  "code_challenge": code_challenge})

    @typechecked
    def get_profile_photo(self, user_id: str, original: Optional[bool] = None) -> bytes:
        """
        Returns a user's profile photo.

        :param user_id: The Verkada user ID.
        :param original: If True, return the original upload rather than the
            cropped image (the default).
        :return: Raw image bytes.
        :raises ValueError: If ``user_id`` is empty.
        """
        params = remove_null_fields({"original": original})
        return self.request_manager.get_image(f"{self._user_url(user_id)}/profile_photo",
                                              params=params)

    @typechecked
    def upload_profile_photo(self, user_id: str, photo_path: str,
                             overwrite: Optional[bool] = None) -> Dict[str, Any]:
        """
        Upload a profile photo for a user (JPG, JPEG or PNG, at most 10 MB).

        :param user_id: The Verkada user ID.
        :param photo_path: Local path to the image file.
        :param overwrite: Replace an existing photo. Without it, uploading over
            an existing photo raises ``VerkadaConflictError``.
        :return: An empty dict on success.
        :raises ValueError: If ``user_id`` is empty.
        :raises FileNotFoundError: If ``photo_path`` doesn't exist.
        """
        url = f"{self._user_url(user_id)}/profile_photo"
        params = remove_null_fields({"overwrite": overwrite})
        with open(photo_path, 'rb') as photo_file:
            return self.request_manager.put(url, params=params,
                                            files={'file': photo_file})

    @typechecked
    def delete_profile_photo(self, user_id: str) -> Dict[str, Any]:
        """
        Delete a user's profile photo.

        :param user_id: The Verkada user ID.
        :return: An empty dict (the API returns 204 No Content).
        :raises ValueError: If ``user_id`` is empty.
        """
        return self.request_manager.delete(f"{self._user_url(user_id)}/profile_photo")

    # ------------------------------------------------------------------
    # Face unlock
    # ------------------------------------------------------------------

    @typechecked
    def disable_face_unlock(self, user_id: Optional[str] = None,
                            external_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Disable face unlock for a user, deleting their face credential and any
        pending enrollment invitations. Exactly one identifier must be provided.

        :param user_id: The Verkada user ID.
        :param external_id: The customer-managed external ID.
        :return: The API response (empty on success).
        :raises ValueError: If not exactly one identifier is provided.
        """
        url = f"{self._user_or_external_url(user_id, external_id)}/face_unlock"
        return self.request_manager.delete(url)

    @typechecked
    def enable_face_unlock_with_profile_photo(self, user_id: Optional[str] = None,
                                              external_id: Optional[str] = None,
                                              overwrite: Optional[bool] = None
                                              ) -> Dict[str, Any]:
        """
        Enable face unlock using the user's existing profile photo, which must
        meet face recognition quality requirements. Exactly one identifier must
        be provided.

        :param user_id: The Verkada user ID.
        :param external_id: The customer-managed external ID.
        :param overwrite: Replace an existing face credential. Defaults to False.
        :return: ``{"user_id": str, "identity_id": str}``.
        :raises ValueError: If not exactly one identifier is provided.
        """
        url = f"{self._user_or_external_url(user_id, external_id)}/face_unlock/copy_user_photo"
        return self.request_manager.post(url, payload=remove_null_fields({"overwrite": overwrite}))

    @typechecked
    def enable_face_unlock_with_uploaded_photo(self, photo_path: str,
                                               user_id: Optional[str] = None,
                                               external_id: Optional[str] = None,
                                               overwrite: Optional[bool] = None
                                               ) -> Dict[str, Any]:
        """
        Enable face unlock by uploading a photo of the user's face, which must
        meet face recognition quality requirements. Exactly one identifier must
        be provided.

        :param photo_path: Local path to the image file.
        :param user_id: The Verkada user ID.
        :param external_id: The customer-managed external ID.
        :param overwrite: Replace an existing face credential. Defaults to False.
        :return: ``{"user_id": str, "identity_id": str}``.
        :raises ValueError: If not exactly one identifier is provided.
        :raises FileNotFoundError: If ``photo_path`` doesn't exist.
        """
        url = f"{self._user_or_external_url(user_id, external_id)}/face_unlock/upload_photo"
        data = {"overwrite": "true" if overwrite else "false"} if overwrite is not None else None
        with open(photo_path, 'rb') as photo_file:
            return self.request_manager.post(url, files={'file': photo_file}, data=data)

    @typechecked
    def invite_user_to_enroll_face_unlock(self, user_id: Optional[str] = None,
                                          external_id: Optional[str] = None,
                                          invitation_methods: Optional[List[str]] = None
                                          ) -> Dict[str, Any]:
        """
        Invite a user to enroll their face from a mobile device. Exactly one
        identifier must be provided.

        :param user_id: The Verkada user ID.
        :param external_id: The customer-managed external ID.
        :param invitation_methods: ``"email"`` and/or ``"sms"``. Defaults to both.
        :return: ``user_id``, ``live_link_id``, ``invitations_sent`` and
            ``invitations_failed``.
        :raises ValueError: If not exactly one identifier is provided.
        """
        url = f"{self._user_or_external_url(user_id, external_id)}/face_unlock/invite"
        payload = remove_null_fields({"invitation_methods": invitation_methods})
        return self.request_manager.post(url, payload=payload)

    # ------------------------------------------------------------------
    # Credentials
    # ------------------------------------------------------------------

    @typechecked
    def add_card_to_user(self, card_type: str,
                         user_id: Optional[str] = None,
                         external_id: Optional[str] = None,
                         card_number: Optional[str] = None,
                         card_number_hex: Optional[str] = None,
                         facility_code: Optional[str] = None,
                         active: Optional[bool] = None) -> Dict[str, Any]:
        """
        Add an access card to a user. Uses v1 (no v2 endpoint yet).

        Provide exactly one of ``card_number`` (with ``facility_code``) or
        ``card_number_hex``, and exactly one of ``user_id`` or ``external_id``.

        :param card_type: The card format, e.g. ``"Standard 26-bit Wiegand"``
            (see :data:`pykada.enums.VALID_CARD_TYPES_ENUM`).
        :param user_id: The Verkada user ID.
        :param external_id: The customer-managed external ID.
        :param card_number: The card number.
        :param card_number_hex: The card number in hexadecimal.
        :param facility_code: The facility code (used with ``card_number``).
        :param active: Whether the card is active. Defaults to False.
        :return: The created card, including its ``card_id``.
        :raises ValueError: If ``card_type`` is empty, or the identifier or
            card number rules aren't met.
        """
        require_non_empty_str(card_type, "card_type")
        params = check_user_id_or_external_id(user_id, external_id)
        if (card_number is None) == (card_number_hex is None):
            raise ValueError("Exactly one of card_number or card_number_hex must be provided.")
        payload = remove_null_fields({
            "type": card_type,
            "card_number": card_number,
            "card_number_hex": card_number_hex,
            "facility_code": facility_code,
            "active": active,
        })
        return self.request_manager.post(ACCESS_CARD_ENDPOINT, params=params, payload=payload)

    @typechecked
    def activate_access_card(self, card_id: str, user_id: Optional[str] = None,
                             external_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Activate a user's access card. Uses v1 (no v2 endpoint yet).

        :param card_id: The card's ``card_id``.
        :param user_id: The Verkada user ID.
        :param external_id: The customer-managed external ID.
        :return: The updated card.
        :raises ValueError: If ``card_id`` is empty or not exactly one user
            identifier is provided.
        """
        require_non_empty_str(card_id, "card_id")
        params = {**check_user_id_or_external_id(user_id, external_id), "card_id": card_id}
        return self.request_manager.put(ACCESS_CARD_ACTIVATE_ENDPOINT, params=params)

    @typechecked
    def deactivate_access_card(self, card_id: str, user_id: Optional[str] = None,
                               external_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Deactivate a user's access card. Uses v1 (no v2 endpoint yet).

        :param card_id: The card's ``card_id``.
        :param user_id: The Verkada user ID.
        :param external_id: The customer-managed external ID.
        :return: The updated card.
        :raises ValueError: If ``card_id`` is empty or not exactly one user
            identifier is provided.
        """
        require_non_empty_str(card_id, "card_id")
        params = {**check_user_id_or_external_id(user_id, external_id), "card_id": card_id}
        return self.request_manager.put(ACCESS_CARD_DEACTIVATE_ENDPOINT, params=params)

    @typechecked
    def delete_access_card(self, card_id: str, user_id: Optional[str] = None,
                           external_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete a user's access card. Uses v1 (no v2 endpoint yet).

        :param card_id: The card's ``card_id``.
        :param user_id: The Verkada user ID.
        :param external_id: The customer-managed external ID.
        :return: The API response.
        :raises ValueError: If ``card_id`` is empty or not exactly one user
            identifier is provided.
        """
        require_non_empty_str(card_id, "card_id")
        params = {**check_user_id_or_external_id(user_id, external_id), "card_id": card_id}
        return self.request_manager.delete(ACCESS_CARD_ENDPOINT, params=params)

    @typechecked
    def add_license_plate_to_user(self, license_plate_number: str,
                                  user_id: Optional[str] = None,
                                  external_id: Optional[str] = None,
                                  name: Optional[str] = None,
                                  active: Optional[bool] = None) -> Dict[str, Any]:
        """
        Add a license plate credential to a user. Exactly one of ``user_id`` or
        ``external_id`` must be provided.

        :param license_plate_number: The plate number (2 to 16 characters),
            unique within the organization.
        :param user_id: The Verkada user ID.
        :param external_id: The customer-managed external ID.
        :param name: Display name for the credential. Defaults to the plate number.
        :param active: Whether the credential is active. Defaults to False.
        :return: The created license plate credential.
        :raises ValueError: If the plate isn't 2-16 characters or not exactly
            one user identifier is provided.
        """
        if not 2 <= len(license_plate_number) <= 16:
            raise ValueError("license_plate_number must be 2 to 16 characters.")
        payload = remove_null_fields({
            **check_user_id_or_external_id(user_id, external_id),
            "license_plate_number": license_plate_number,
            "name": name,
            "active": active,
        })
        return self.request_manager.post(V2_ACCESS_LICENSE_PLATES_ENDPOINT, payload=payload)

    @typechecked
    def set_license_plate_active(self, license_plate_number: str, active: bool,
                                 user_id: Optional[str] = None,
                                 external_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Activate or deactivate a user's license plate credential. Exactly one of
        ``user_id`` or ``external_id`` must be provided.

        :param license_plate_number: The plate number of the credential.
        :param active: ``True`` to activate; ``False`` to deactivate.
        :param user_id: The Verkada user ID that owns the plate.
        :param external_id: The customer-managed external ID that owns the plate.
        :return: The updated license plate credential.
        :raises ValueError: If the plate is empty or not exactly one user
            identifier is provided.
        """
        url = (f"{V2_ACCESS_LICENSE_PLATES_ENDPOINT}/"
               f"{path_segment(license_plate_number, 'license_plate_number')}")
        payload = {**check_user_id_or_external_id(user_id, external_id), "active": active}
        return self.request_manager.patch(url, payload=payload)

    @typechecked
    def delete_license_plate_from_user(self, license_plate_number: str,
                                       user_id: Optional[str] = None,
                                       external_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete a license plate credential from a user. Exactly one of
        ``user_id`` or ``external_id`` must be provided.

        :param license_plate_number: The plate number of the credential.
        :param user_id: The Verkada user ID that owns the plate.
        :param external_id: The customer-managed external ID that owns the plate.
        :return: An empty dict (the API returns 204 No Content).
        :raises ValueError: If the plate is empty or not exactly one user
            identifier is provided.
        """
        url = (f"{V2_ACCESS_LICENSE_PLATES_ENDPOINT}/"
               f"{path_segment(license_plate_number, 'license_plate_number')}")
        return self.request_manager.delete(
            url, params=check_user_id_or_external_id(user_id, external_id))

    @typechecked
    def add_mfa_code_to_user(self, code: str,
                             user_id: Optional[str] = None,
                             external_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Add an MFA code credential to a user. Exactly one of ``user_id`` or
        ``external_id`` must be provided.

        :param code: 4 to 16 digits, unique per user within the organization.
        :param user_id: The Verkada user ID.
        :param external_id: The customer-managed external ID.
        :return: ``{"code": str, "user_id": str}``.
        :raises ValueError: If ``code`` isn't 4-16 digits or not exactly one
            user identifier is provided.
        """
        _digits_4_to_16(code, "code")
        payload = {**check_user_id_or_external_id(user_id, external_id), "code": code}
        return self.request_manager.post(V2_ACCESS_MFA_CODES_ENDPOINT, payload=payload)

    @typechecked
    def delete_mfa_code_from_user(self, code: str,
                                  user_id: Optional[str] = None,
                                  external_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete an MFA code credential from a user. Exactly one of ``user_id`` or
        ``external_id`` must be provided.

        :param code: The MFA code to delete.
        :param user_id: The Verkada user ID.
        :param external_id: The customer-managed external ID.
        :return: An empty dict (the API returns 204 No Content).
        :raises ValueError: If ``code`` is empty or not exactly one user
            identifier is provided.
        """
        url = f"{V2_ACCESS_MFA_CODES_ENDPOINT}/{path_segment(code, 'code')}"
        return self.request_manager.delete(
            url, params=check_user_id_or_external_id(user_id, external_id))

    @staticmethod
    def _qr_code_selector(encoding_type, qr_code, card_number, card_number_hex,
                          facility_code) -> dict:
        require_non_empty_str(encoding_type, "encoding_type")
        if sum(v is not None for v in (qr_code, card_number, card_number_hex)) != 1:
            raise ValueError(
                "Exactly one of qr_code, card_number or card_number_hex must be provided.")
        return remove_null_fields({
            "encoding_type": encoding_type,
            "qr_code": qr_code,
            "card_number": card_number,
            "card_number_hex": card_number_hex,
            "facility_code": facility_code,
        })

    @typechecked
    def add_qr_code_to_user(self, encoding_type: str,
                            user_id: Optional[str] = None,
                            external_id: Optional[str] = None,
                            qr_code: Optional[str] = None,
                            card_number: Optional[str] = None,
                            card_number_hex: Optional[str] = None,
                            facility_code: Optional[str] = None,
                            active: Optional[bool] = None,
                            activation_state: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a QR code credential to a user. Exactly one of ``user_id`` or
        ``external_id`` must be provided.

        :param encoding_type: A QR encoding (``"NONE"``, ``"VISIT_KEY_BASE_10"``,
            ``"GUEST_STRIPPED_BIT_BASE_10"``) or a card type for card-based encodings.
        :param user_id: The Verkada user ID.
        :param external_id: The customer-managed external ID.
        :param qr_code: The QR code data (base 10).
        :param card_number: The card number, for card-based encodings.
        :param card_number_hex: The card number in hexadecimal.
        :param facility_code: The facility code, for card types that use one.
        :param active: Whether the QR code grants access. Defaults to True.
        :param activation_state: Detailed state, e.g. ``"active"``. Defaults to ``"active"``.
        :return: The created QR code credential.
        :raises ValueError: If ``encoding_type`` is empty or not exactly one
            user identifier is provided.
        """
        require_non_empty_str(encoding_type, "encoding_type")
        url = f"{self._user_or_external_url(user_id, external_id)}/credentials/qr_codes"
        payload = remove_null_fields({
            "encoding_type": encoding_type,
            "qr_code": qr_code,
            "card_number": card_number,
            "card_number_hex": card_number_hex,
            "facility_code": facility_code,
            "active": active,
            "activation_state": activation_state,
        })
        return self.request_manager.post(url, payload=payload)

    @typechecked
    def update_qr_code_state(self, encoding_type: str,
                             user_id: Optional[str] = None,
                             external_id: Optional[str] = None,
                             qr_code: Optional[str] = None,
                             card_number: Optional[str] = None,
                             card_number_hex: Optional[str] = None,
                             facility_code: Optional[str] = None,
                             active: Optional[bool] = None,
                             activation_state: Optional[str] = None) -> Dict[str, Any]:
        """
        Change whether a user's QR code credential is active, deactivated, lost, etc.

        Identify the user with exactly one of ``user_id`` or ``external_id``,
        and the QR code with ``encoding_type`` plus exactly one of ``qr_code``,
        ``card_number`` or ``card_number_hex``.

        :param encoding_type: The QR code's encoding type.
        :param user_id: The Verkada user ID.
        :param external_id: The customer-managed external ID.
        :param qr_code: The QR code data.
        :param card_number: The card number.
        :param card_number_hex: The card number in hexadecimal.
        :param facility_code: The facility code, for card types that use one.
        :param active: Whether the QR code grants access.
        :param activation_state: Detailed state, e.g. ``"deactivated"`` or ``"lost"``.
        :return: The updated QR code credential.
        :raises ValueError: If the identifiers are wrong or neither ``active``
            nor ``activation_state`` is given.
        """
        url = f"{self._user_or_external_url(user_id, external_id)}/credentials/qr_codes"
        params = self._qr_code_selector(encoding_type, qr_code, card_number,
                                        card_number_hex, facility_code)
        payload = remove_null_fields({"active": active, "activation_state": activation_state})
        if not payload:
            raise ValueError("At least one of active or activation_state must be provided.")
        return self.request_manager.patch(url, params=params, payload=payload)

    @typechecked
    def delete_qr_code_from_user(self, encoding_type: str,
                                 user_id: Optional[str] = None,
                                 external_id: Optional[str] = None,
                                 qr_code: Optional[str] = None,
                                 card_number: Optional[str] = None,
                                 card_number_hex: Optional[str] = None,
                                 facility_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete a QR code credential from a user.

        Identify the user with exactly one of ``user_id`` or ``external_id``,
        and the QR code with ``encoding_type`` plus exactly one of ``qr_code``,
        ``card_number`` or ``card_number_hex``.

        :param encoding_type: The QR code's encoding type.
        :param user_id: The Verkada user ID.
        :param external_id: The customer-managed external ID.
        :param qr_code: The QR code data.
        :param card_number: The card number.
        :param card_number_hex: The card number in hexadecimal.
        :param facility_code: The facility code, for card types that use one.
        :return: The API response.
        :raises ValueError: If the user or QR code identifiers are wrong.
        """
        url = f"{self._user_or_external_url(user_id, external_id)}/credentials/qr_codes"
        params = self._qr_code_selector(encoding_type, qr_code, card_number,
                                        card_number_hex, facility_code)
        return self.request_manager.delete(url, params=params)

    # ------------------------------------------------------------------
    # Access groups
    # ------------------------------------------------------------------

    @typechecked
    def get_all_access_groups(self) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every access group in the organization, walking all pages automatically.

        :return: A generator that yields ``{"group_id", "name"}`` dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_access_groups(**kwargs),
        )

    @typechecked
    def get_access_groups(self,
                          limit: Optional[int] = None,
                          cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of access groups.

        :param limit: Maximum groups per page (1 to 1000, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``limit`` is outside 1-1000.
        """
        check_limit(limit, 1000)
        params = remove_null_fields({"limit": limit, "cursor": cursor})
        return self.request_manager.get(V2_ACCESS_GROUPS_ENDPOINT, params=params)

    @typechecked
    def get_access_group(self, group_id: str) -> Dict[str, Any]:
        """
        Returns an access group and its members.

        :param group_id: The access group ID.
        :return: ``group_id``, ``name`` and member ``user_ids``.
        :raises ValueError: If ``group_id`` is empty.
        """
        url = f"{V2_ACCESS_GROUPS_ENDPOINT}/{path_segment(group_id, 'group_id')}"
        return self.request_manager.get(url)

    @typechecked
    def create_access_group(self, name: str) -> Dict[str, Any]:
        """
        Create an access group. Names must be unique within the organization;
        a duplicate raises ``VerkadaConflictError``.

        :param name: The group name (1 to 255 characters).
        :return: The created access group.
        :raises ValueError: If ``name`` is empty or over 255 characters.
        """
        require_non_empty_str(name, "name")
        if len(name) > 255:
            raise ValueError("name must be at most 255 characters.")
        return self.request_manager.post(V2_ACCESS_GROUPS_ENDPOINT, payload={"name": name})

    @typechecked
    def delete_access_group(self, group_id: str) -> Dict[str, Any]:
        """
        Delete an access group.

        :param group_id: The access group ID.
        :return: An empty dict (the API returns 204 No Content).
        :raises ValueError: If ``group_id`` is empty.
        """
        url = f"{V2_ACCESS_GROUPS_ENDPOINT}/{path_segment(group_id, 'group_id')}"
        return self.request_manager.delete(url)

    @typechecked
    def add_user_to_access_group(self, group_id: str, user_id: str) -> Dict[str, Any]:
        """
        Add a user to an access group.

        :param group_id: The access group ID.
        :param user_id: The Verkada user ID. To use an external ID, translate
            it first with :meth:`resolve_user_id`.
        :return: The updated access group.
        :raises ValueError: If ``group_id`` or ``user_id`` is empty.
        """
        url = (f"{V2_ACCESS_GROUPS_ENDPOINT}/{path_segment(group_id, 'group_id')}"
               f"/users/{path_segment(user_id, 'user_id')}")
        return self.request_manager.put(url)

    @typechecked
    def remove_user_from_access_group(self, group_id: str, user_id: str) -> Dict[str, Any]:
        """
        Remove a user from an access group.

        :param group_id: The access group ID.
        :param user_id: The Verkada user ID. To use an external ID, translate
            it first with :meth:`resolve_user_id`.
        :return: An empty dict (the API returns 204 No Content).
        :raises ValueError: If ``group_id`` or ``user_id`` is empty.
        """
        url = (f"{V2_ACCESS_GROUPS_ENDPOINT}/{path_segment(group_id, 'group_id')}"
               f"/users/{path_segment(user_id, 'user_id')}")
        return self.request_manager.delete(url)

    # ------------------------------------------------------------------
    # Access levels
    # ------------------------------------------------------------------

    @typechecked
    def get_all_access_levels(self) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every Access Level visible to the API key, walking all pages automatically.

        :return: A generator that yields individual Access Level dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_access_levels(**kwargs),
        )

    @typechecked
    def get_access_levels(self,
                          limit: Optional[int] = None,
                          cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of Access Levels whose sites are in the API key's scope.

        Each level includes its ``access_groups``, ``sites``, ``doors``,
        ``access_schedule_events`` and an RFC 3339 ``last_updated_at``.

        :param limit: Maximum levels per page (1 to 1000, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``limit`` is outside 1-1000.
        """
        check_limit(limit, 1000)
        params = remove_null_fields({"limit": limit, "cursor": cursor})
        return self.request_manager.get(V2_ACCESS_LEVELS_ENDPOINT, params=params)

    @typechecked
    def get_access_level(self, access_level_id: str) -> Dict[str, Any]:
        """
        Returns an Access Level and its weekly schedule events.

        :param access_level_id: The Access Level ID.
        :return: The Access Level.
        :raises ValueError: If ``access_level_id`` is empty.
        """
        url = f"{V2_ACCESS_LEVELS_ENDPOINT}/{path_segment(access_level_id, 'access_level_id')}"
        return self.request_manager.get(url)

    @typechecked
    def create_access_level(self, name: str,
                            sites: List[str],
                            access_groups: List[str],
                            doors: List[str],
                            access_schedule_events: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Create an Access Level granting groups access to doors during weekly windows.

        Requires "Door Access Management" permission on every site and
        "Manage via API" enabled on every door.

        :param name: Unique name, at most 100 characters, without ``<>{}[]``.
        :param sites: Site IDs (at least one) containing the doors.
        :param access_groups: Access Group IDs granted access.
        :param doors: Door IDs, each in one of ``sites``.
        :param access_schedule_events: Weekly windows, each a dict like
            ``{"weekday": "Monday", "start_time": "09:00", "end_time": "17:00"}``.
            Windows on the same weekday must not overlap or touch.
        :return: The created Access Level.
        :raises ValueError: If ``name`` or ``sites`` is empty, or an event is invalid.
        """
        require_non_empty_str(name, "name")
        if not sites:
            raise ValueError("sites must contain at least one site ID.")
        payload = {
            "name": name,
            "sites": sites,
            "access_groups": access_groups,
            "doors": doors,
            "access_schedule_events": _schedule_events(access_schedule_events),
        }
        return self.request_manager.post(V2_ACCESS_LEVELS_ENDPOINT, payload=payload)

    @typechecked
    def update_access_level(self, access_level_id: str,
                            name: Optional[str] = None,
                            sites: Optional[List[str]] = None,
                            access_groups: Optional[List[str]] = None,
                            doors: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Change some of an Access Level's fields, leaving the rest as they are.

        Each list you pass replaces the existing one, so send the complete
        intended list. Schedule events can't be changed here; use the
        ``*_access_schedule_event*`` methods.

        :param access_level_id: The Access Level ID.
        :param name: New unique name.
        :param sites: Complete replacement list of site IDs (at least one).
        :param access_groups: Complete replacement list of Access Group IDs.
        :param doors: Complete replacement list of door IDs.
        :return: The updated Access Level.
        :raises ValueError: If ``access_level_id`` is empty, no field is given,
            or ``sites`` is an empty list.
        """
        if sites is not None and not sites:
            raise ValueError("sites must contain at least one site ID.")
        payload = remove_null_fields({"name": name, "sites": sites,
                                      "access_groups": access_groups, "doors": doors})
        if not payload:
            raise ValueError("At least one field to update must be provided.")
        url = f"{V2_ACCESS_LEVELS_ENDPOINT}/{path_segment(access_level_id, 'access_level_id')}"
        return self.request_manager.patch(url, payload=payload)

    @typechecked
    def delete_access_level(self, access_level_id: str) -> Dict[str, Any]:
        """
        Delete an Access Level.

        :param access_level_id: The Access Level ID.
        :return: An empty dict (the API returns 204 No Content).
        :raises ValueError: If ``access_level_id`` is empty.
        """
        url = f"{V2_ACCESS_LEVELS_ENDPOINT}/{path_segment(access_level_id, 'access_level_id')}"
        return self.request_manager.delete(url)

    def _schedule_events_url(self, access_level_id: str, event_id: Optional[str] = None) -> str:
        url = (f"{V2_ACCESS_LEVELS_ENDPOINT}/"
               f"{path_segment(access_level_id, 'access_level_id')}/access_schedule_events")
        return f"{url}/{path_segment(event_id, 'event_id')}" if event_id is not None else url

    @typechecked
    def add_access_schedule_event_to_access_level(self, access_level_id: str,
                                                  weekday: str,
                                                  start_time: str,
                                                  end_time: str) -> Dict[str, Any]:
        """
        Add a weekly window to an Access Level.

        It must not overlap or touch another window on the same weekday
        (otherwise ``VerkadaValidationError``).

        :param access_level_id: The Access Level ID.
        :param weekday: Full weekday name, e.g. ``"Monday"``.
        :param start_time: Local start time as ``HH:MM``.
        :param end_time: Local end time as ``HH:MM``; after ``start_time``.
        :return: The created schedule event.
        :raises ValueError: If ``access_level_id`` is empty or the window is invalid.
        """
        return self.request_manager.post(
            self._schedule_events_url(access_level_id),
            payload=build_access_schedule_event(weekday, start_time, end_time))

    @typechecked
    def get_access_schedule_event(self, access_level_id: str, event_id: str) -> Dict[str, Any]:
        """
        Returns one weekly window of an Access Level.

        :param access_level_id: The Access Level ID.
        :param event_id: The schedule event ID.
        :return: The schedule event.
        :raises ValueError: If either ID is empty.
        """
        return self.request_manager.get(self._schedule_events_url(access_level_id, event_id))

    @typechecked
    def update_access_schedule_event_on_access_level(self, access_level_id: str,
                                                     event_id: str,
                                                     weekday: Optional[str] = None,
                                                     start_time: Optional[str] = None,
                                                     end_time: Optional[str] = None
                                                     ) -> Dict[str, Any]:
        """
        Change some of a weekly window's fields, leaving the rest as they are.

        :param access_level_id: The Access Level ID.
        :param event_id: The schedule event ID.
        :param weekday: New full weekday name.
        :param start_time: New local start time as ``HH:MM``.
        :param end_time: New local end time as ``HH:MM``.
        :return: The updated schedule event.
        :raises ValueError: If either ID is empty, no field is given, or a
            value is invalid.
        """
        payload = remove_null_fields({
            "recurrence_rule": _weekly_rule(weekday) if weekday is not None else None,
            "start_time": _hh_mm(start_time, "start_time") if start_time is not None else None,
            "end_time": _hh_mm(end_time, "end_time") if end_time is not None else None,
        })
        if not payload:
            raise ValueError("At least one of weekday, start_time or end_time must be provided.")
        if start_time is not None and end_time is not None and end_time <= start_time:
            raise ValueError(f"end_time must be after start_time; got {start_time}-{end_time}.")
        return self.request_manager.patch(self._schedule_events_url(access_level_id, event_id),
                                          payload=payload)

    @typechecked
    def delete_access_schedule_event_on_access_level(self, access_level_id: str,
                                                     event_id: str) -> Dict[str, Any]:
        """
        Remove one weekly window from an Access Level. The level is kept even
        if it has no windows left (it then grants no access).

        :param access_level_id: The Access Level ID.
        :param event_id: The schedule event ID.
        :return: An empty dict (the API returns 204 No Content).
        :raises ValueError: If either ID is empty.
        """
        return self.request_manager.delete(self._schedule_events_url(access_level_id, event_id))

    # ------------------------------------------------------------------
    # Doors
    # ------------------------------------------------------------------

    @typechecked
    def get_all_doors(self,
                      door_ids: Optional[List[str]] = None,
                      site_ids: Optional[List[str]] = None
                      ) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every matching door, walking all pages automatically.

        :param door_ids: Only return these doors. Can't be combined with ``site_ids``.
        :param site_ids: Only return doors at these sites.
        :return: A generator that yields individual door dictionaries.
        :rtype: Generator
        :raises ValueError: If both ``door_ids`` and ``site_ids`` are given.
        """
        if door_ids and site_ids:
            raise ValueError("Only one of door_ids or site_ids can be used.")
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_doors(**kwargs),
            initial_params={"door_ids": door_ids, "site_ids": site_ids},
        )

    @typechecked
    def get_doors(self,
                  door_ids: Optional[List[str]] = None,
                  site_ids: Optional[List[str]] = None,
                  limit: Optional[int] = None,
                  cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of doors.

        Each door has its ``door_id``, ``name``, ``site``, ACU, nearby
        ``camera_info``, ``timezone`` and whether ``api_control_enabled``.

        :param door_ids: Only return these doors. Can't be combined with ``site_ids``.
        :param site_ids: Only return doors at these sites.
        :param limit: Maximum doors per page (1 to 1000, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If both filters are given or ``limit`` is outside 1-1000.
        """
        if door_ids and site_ids:
            raise ValueError("Only one of door_ids or site_ids can be used.")
        check_limit(limit, 1000)
        params = remove_null_fields({
            "door_ids": ",".join(door_ids) if door_ids else None,
            "site_ids": ",".join(site_ids) if site_ids else None,
            "limit": limit,
            "cursor": cursor,
        })
        return self.request_manager.get(V2_ACCESS_DOORS_ENDPOINT, params=params)

    @typechecked
    def unlock_door_as_admin(self, door_id: str) -> Dict[str, Any]:
        """
        Unlock a door regardless of any user's permissions. Uses v1 (no v2
        endpoint yet).

        :param door_id: The door ID.
        :return: ``{"door_id": str, "unlock_duration": int}``.
        :raises ValueError: If ``door_id`` is empty.
        """
        require_non_empty_str(door_id, "door_id")
        return self.request_manager.post(ACCESS_ADMIN_UNLOCK_ENDPOINT,
                                         payload={"door_id": door_id})

    @typechecked
    def unlock_door_as_user(self, door_id: str, user_id: Optional[str] = None,
                            external_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Unlock a door as a user; only granted if the user has access to it
        through an Access Level. Uses v1 (no v2 endpoint yet).

        :param door_id: The door ID.
        :param user_id: The Verkada user ID.
        :param external_id: The customer-managed external ID.
        :return: ``{"door_id": str, "unlock_duration": int}``.
        :raises ValueError: If ``door_id`` is empty or not exactly one user
            identifier is provided.
        """
        require_non_empty_str(door_id, "door_id")
        payload = {**check_user_id_or_external_id(user_id, external_id), "door_id": door_id}
        return self.request_manager.post(ACCESS_USER_UNLOCK_ENDPOINT, payload=payload)

    # ------------------------------------------------------------------
    # Door exception calendars
    # ------------------------------------------------------------------

    def _calendar_url(self, calendar_id: str) -> str:
        return (f"{V2_ACCESS_EXCEPTION_CALENDARS_ENDPOINT}/"
                f"{path_segment(calendar_id, 'calendar_id')}")

    @typechecked
    def get_all_door_exception_calendars(self,
                                         last_updated_after: Optional[Timestamp] = None
                                         ) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every door exception calendar, walking all pages automatically.

        :param last_updated_after: Only return calendars updated after this
            time, as a timezone-aware ``datetime`` or ISO 8601 string.
        :return: A generator that yields individual calendar dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_door_exception_calendars(**kwargs),
            initial_params={"last_updated_after": last_updated_after},
        )

    @typechecked
    def get_door_exception_calendars(self,
                                     last_updated_after: Optional[Timestamp] = None,
                                     limit: Optional[int] = None,
                                     cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of door exception calendars for the authorized sites.

        :param last_updated_after: Only return calendars updated after this
            time, as a timezone-aware ``datetime`` or ISO 8601 string.
        :param limit: Maximum calendars per page (1 to 1000, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``limit`` is outside 1-1000 or the timestamp is invalid.
        """
        check_limit(limit, 1000)
        params = remove_null_fields({
            "last_updated_after": to_iso8601(last_updated_after, "last_updated_after"),
            "limit": limit,
            "cursor": cursor,
        })
        return self.request_manager.get(V2_ACCESS_EXCEPTION_CALENDARS_ENDPOINT, params=params)

    @typechecked
    def get_door_exception_calendar(self, calendar_id: str) -> Dict[str, Any]:
        """
        Returns a door exception calendar and its exceptions.

        :param calendar_id: The calendar ID.
        :return: ``calendar_id``, ``name``, ``doors``, ``exceptions`` and an
            RFC 3339 ``last_updated_at``.
        :raises ValueError: If ``calendar_id`` is empty.
        """
        return self.request_manager.get(self._calendar_url(calendar_id))

    @staticmethod
    def _calendar_body(name, doors, exceptions) -> dict:
        require_non_empty_str(name, "name")
        for idx, door in enumerate(doors):
            require_non_empty_str(door, "door", idx)
        for idx, exc in enumerate(exceptions):
            validate_door_exception(exc, idx)
        return {"name": name, "doors": doors, "exceptions": exceptions}

    @typechecked
    def create_door_exception_calendar(self, name: str,
                                       doors: List[str],
                                       exceptions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a door exception calendar.

        :param name: The calendar name.
        :param doors: Door IDs the exceptions apply to.
        :param exceptions: Exception objects; see :func:`validate_door_exception`
            for the shape. Recurrence ``by_day`` uses full weekday names.
        :return: The created calendar.
        :raises ValueError: If ``name`` or a door ID is empty, or an exception is invalid.
        """
        return self.request_manager.post(V2_ACCESS_EXCEPTION_CALENDARS_ENDPOINT,
                                         payload=self._calendar_body(name, doors, exceptions))

    @typechecked
    def update_door_exception_calendar(self, calendar_id: str,
                                       name: str,
                                       doors: List[str],
                                       exceptions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Replace a door exception calendar. Anything not supplied is removed;
        include an exception's ``exception_id`` to keep it rather than recreate it.

        :param calendar_id: The calendar ID.
        :param name: The calendar name.
        :param doors: Door IDs the exceptions apply to.
        :param exceptions: The complete list of exception objects.
        :return: The updated calendar.
        :raises ValueError: If an ID, ``name`` or door ID is empty, or an
            exception is invalid.
        """
        return self.request_manager.put(self._calendar_url(calendar_id),
                                        payload=self._calendar_body(name, doors, exceptions))

    @typechecked
    def delete_door_exception_calendar(self, calendar_id: str) -> Dict[str, Any]:
        """
        Delete a door exception calendar.

        :param calendar_id: The calendar ID.
        :return: An empty dict (the API returns 204 No Content).
        :raises ValueError: If ``calendar_id`` is empty.
        """
        return self.request_manager.delete(self._calendar_url(calendar_id))

    @typechecked
    def get_exception_on_door_exception_calendar(self, calendar_id: str,
                                                 exception_id: str) -> Dict[str, Any]:
        """
        Returns one exception on a door exception calendar.

        :param calendar_id: The calendar ID.
        :param exception_id: The exception ID.
        :return: The exception.
        :raises ValueError: If either ID is empty.
        """
        url = (f"{self._calendar_url(calendar_id)}/exceptions/"
               f"{path_segment(exception_id, 'exception_id')}")
        return self.request_manager.get(url)

    @typechecked
    def add_exception_to_door_exception_calendar(self, calendar_id: str,
                                                 exception: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add an exception to a door exception calendar.

        :param calendar_id: The calendar ID.
        :param exception: The exception object; see :func:`validate_door_exception`.
        :return: The created exception.
        :raises ValueError: If ``calendar_id`` is empty or the exception is invalid.
        """
        validate_door_exception(exception)
        return self.request_manager.post(f"{self._calendar_url(calendar_id)}/exceptions",
                                         payload=exception)

    @typechecked
    def update_exception_on_door_exception_calendar(self, calendar_id: str,
                                                    exception_id: str,
                                                    exception: Dict[str, Any]) -> Dict[str, Any]:
        """
        Replace an exception on a door exception calendar. Supply every field
        that should remain set.

        :param calendar_id: The calendar ID.
        :param exception_id: The exception ID.
        :param exception: The complete exception object; see :func:`validate_door_exception`.
        :return: The updated exception.
        :raises ValueError: If either ID is empty or the exception is invalid.
        """
        validate_door_exception(exception)
        url = (f"{self._calendar_url(calendar_id)}/exceptions/"
               f"{path_segment(exception_id, 'exception_id')}")
        return self.request_manager.put(url, payload=exception)

    @typechecked
    def delete_exception_on_door_exception_calendar(self, calendar_id: str,
                                                    exception_id: str) -> Dict[str, Any]:
        """
        Delete an exception from a door exception calendar.

        :param calendar_id: The calendar ID.
        :param exception_id: The exception ID.
        :return: An empty dict (the API returns 204 No Content).
        :raises ValueError: If either ID is empty.
        """
        url = (f"{self._calendar_url(calendar_id)}/exceptions/"
               f"{path_segment(exception_id, 'exception_id')}")
        return self.request_manager.delete(url)

    # ------------------------------------------------------------------
    # Scenarios
    # ------------------------------------------------------------------

    @typechecked
    def get_all_access_scenarios(self,
                                 scenario_ids: Optional[List[str]] = None,
                                 site_ids: Optional[List[str]] = None,
                                 scenario_types: Optional[List[str]] = None
                                 ) -> Generator[Dict[str, Any], None, None]:
        """
        Returns every matching access scenario (lockdown), walking all pages automatically.

        :param scenario_ids: Only return these scenarios.
        :param site_ids: Only return scenarios that apply to these sites.
        :param scenario_types: Only return these types, e.g. ``["LOCKDOWN", "EVACUATE"]``.
        :return: A generator that yields individual scenario dictionaries.
        :rtype: Generator
        """
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_access_scenarios(**kwargs),
            initial_params={"scenario_ids": scenario_ids, "site_ids": site_ids,
                            "scenario_types": scenario_types},
        )

    @typechecked
    def get_access_scenarios(self,
                             scenario_ids: Optional[List[str]] = None,
                             site_ids: Optional[List[str]] = None,
                             scenario_types: Optional[List[str]] = None,
                             limit: Optional[int] = None,
                             cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns one page of access scenarios (lockdowns).

        API keys scoped to specific sites only see scenarios in those sites;
        filtering on a site outside the key's scope raises ``VerkadaForbiddenError``.

        :param scenario_ids: Only return these scenarios.
        :param site_ids: Only return scenarios that apply to these sites.
        :param scenario_types: Only return these types, e.g. ``["LOCKDOWN", "EVACUATE"]``.
        :param limit: Maximum scenarios per page (1 to 1000, server default 100).
        :param cursor: Cursor from a previous response's ``cursor`` field.
        :return: ``{"items": [...], "cursor": str | None}``.
        :raises ValueError: If ``limit`` is outside 1-1000.
        """
        check_limit(limit, 1000)
        params = remove_null_fields({
            "scenario_ids": scenario_ids or None,
            "site_ids": site_ids or None,
            "scenario_types": scenario_types or None,
            "limit": limit,
            "cursor": cursor,
        })
        return self.request_manager.get(V2_ACCESS_SCENARIOS_ENDPOINT, params=params)

    @typechecked
    def activate_access_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """
        Activate an access scenario. Activating an active scenario is a no-op.

        Requires "Manage via API" enabled for scenarios. Site-scoped keys can
        only activate scenarios entirely within their sites.

        :param scenario_id: The scenario ID.
        :return: An empty dict on success.
        :raises ValueError: If ``scenario_id`` is empty.
        """
        url = f"{V2_ACCESS_SCENARIOS_ENDPOINT}/{path_segment(scenario_id, 'scenario_id')}/activate"
        return self.request_manager.post(url)

    @typechecked
    def release_access_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """
        Release an access scenario. Releasing an inactive scenario is a no-op.

        :param scenario_id: The scenario ID.
        :return: An empty dict on success.
        :raises ValueError: If ``scenario_id`` is empty.
        """
        url = f"{V2_ACCESS_SCENARIOS_ENDPOINT}/{path_segment(scenario_id, 'scenario_id')}/release"
        return self.request_manager.post(url)


# ---------------------------------------------------------------------------
# Door exception validation
# ---------------------------------------------------------------------------

def _is_valid_exception_time(value) -> bool:
    return isinstance(value, str) and (is_valid_time(value) or bool(_HH_MM_SS_RE.match(value)))


def _positive_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


@typechecked
def validate_recurrence_rule(rr: Dict[str, Any],
                             idx: Optional[int] = None) -> None:
    """
    Validates a v2 recurrence rule (RFC 5545 style) for a door exception.

    :param rr: The recurrence rule object. ``by_day`` uses full weekday
        names, e.g. ``["Monday"]``.
    :param idx: Optional index for context.
    :raises ValueError: If any required field is missing or invalid.
    """
    # frequency: required, must be one of the allowed values
    if "frequency" not in rr:
        raise ValueError(
            f"Exception at index {idx}: 'frequency' is required in recurrence_rule")
    frequency = rr["frequency"]
    valid_frequencies = list(FREQUENCY_ENUM.values())
    if frequency not in valid_frequencies:
        raise ValueError(
            f"Exception at index {idx}: 'frequency' must be one of {valid_frequencies}")

    # interval: required positive integer
    if "interval" not in rr:
        raise ValueError(
            f"Exception at index {idx}: 'interval' is required in recurrence_rule")
    if not _positive_int(rr["interval"]):
        raise ValueError(
            f"Exception at index {idx}: 'interval' must be a positive integer in recurrence_rule")

    # WEEKLY: by_day is required
    if frequency == FREQUENCY_ENUM["WEEKLY"] and "by_day" not in rr:
        raise ValueError(
            f"Exception at index {idx}: 'by_day' is required for WEEKLY frequency")

    # MONTHLY/YEARLY: either by_month_day or by_set_pos is required (not both)
    if frequency in (FREQUENCY_ENUM["MONTHLY"], FREQUENCY_ENUM["YEARLY"]):
        has_month_day = "by_month_day" in rr
        has_set_pos = "by_set_pos" in rr
        if not has_month_day and not has_set_pos:
            raise ValueError(
                f"Exception at index {idx}: either 'by_month_day' or 'by_set_pos' is required for MONTHLY or YEARLY frequency")
        if has_month_day and has_set_pos:
            raise ValueError(
                f"Exception at index {idx}: only one of 'by_month_day' or 'by_set_pos' is allowed")

    # YEARLY: by_month is required
    if frequency == FREQUENCY_ENUM["YEARLY"] and "by_month" not in rr:
        raise ValueError(
            f"Exception at index {idx}: 'by_month' is required for YEARLY frequency")

    # by_day: validate values and frequency constraints
    if "by_day" in rr:
        if not isinstance(rr["by_day"], list) or not all(
                isinstance(day, str) and day.strip() for day in rr["by_day"]):
            raise ValueError(
                f"Exception at index {idx}: 'by_day' must be a list of non-empty strings")
        if not set(rr["by_day"]).issubset(set(WEEKDAY_FULL_ENUM.values())):
            raise ValueError(
                f"Exception at index {idx}: 'by_day' values must be full weekday names, "
                f"one of {list(WEEKDAY_FULL_ENUM.values())}")
        if frequency == FREQUENCY_ENUM["DAILY"]:
            raise ValueError(
                f"Exception at index {idx}: 'by_day' is not supported for DAILY frequency")
        if frequency == FREQUENCY_ENUM["WEEKLY"] and len(rr["by_day"]) < 1:
            raise ValueError(
                f"Exception at index {idx}: 'by_day' must contain at least one value for WEEKLY frequency")
        if frequency in (FREQUENCY_ENUM["MONTHLY"], FREQUENCY_ENUM["YEARLY"]):
            if "by_set_pos" not in rr or rr["by_set_pos"] is None:
                raise ValueError(
                    f"Exception at index {idx}: 'by_set_pos' is required when 'by_day' is provided for MONTHLY or YEARLY frequency")
            if len(rr["by_day"]) != 1:
                raise ValueError(
                    f"Exception at index {idx}: 'by_day' must contain exactly one value for MONTHLY or YEARLY frequency")

    # by_month: YEARLY only, integer 1–12
    if "by_month" in rr:
        if frequency != FREQUENCY_ENUM["YEARLY"]:
            raise ValueError(
                f"Exception at index {idx}: 'by_month' is only supported for YEARLY frequency")
        if not isinstance(rr["by_month"], int) or isinstance(rr["by_month"], bool) or not (
                1 <= rr["by_month"] <= 12):
            raise ValueError(
                f"Exception at index {idx}: 'by_month' must be an integer between 1 and 12")

    # by_month_day: MONTHLY or YEARLY only, integer 1–31
    if "by_month_day" in rr:
        if frequency not in (FREQUENCY_ENUM["MONTHLY"], FREQUENCY_ENUM["YEARLY"]):
            raise ValueError(
                f"Exception at index {idx}: 'by_month_day' is only supported for MONTHLY or YEARLY frequency")
        if not isinstance(rr["by_month_day"], int) or isinstance(rr["by_month_day"], bool) or not (
                1 <= rr["by_month_day"] <= 31):
            raise ValueError(
                f"Exception at index {idx}: 'by_month_day' must be an integer between 1 and 31")

    # by_set_pos: MONTHLY or YEARLY only, integer 1–5
    if "by_set_pos" in rr:
        if frequency not in (FREQUENCY_ENUM["MONTHLY"], FREQUENCY_ENUM["YEARLY"]):
            raise ValueError(
                f"Exception at index {idx}: 'by_set_pos' is only supported for MONTHLY or YEARLY frequency")
        if not isinstance(rr["by_set_pos"], int) or isinstance(rr["by_set_pos"], bool) or not (
                1 <= rr["by_set_pos"] <= 5):
            raise ValueError(
                f"Exception at index {idx}: 'by_set_pos' must be an integer between 1 and 5")

    # count and until: mutually exclusive
    if "count" in rr and "until" in rr:
        raise ValueError(
            f"Exception at index {idx}: only one of 'count' or 'until' may be provided in recurrence_rule")
    if "count" in rr:
        if not _positive_int(rr["count"]):
            raise ValueError(
                f"Exception at index {idx}: 'count' must be a positive integer")
    if "until" in rr:
        if not isinstance(rr["until"], str) or not is_valid_date(rr["until"]):
            raise ValueError(
                f"Exception at index {idx}: 'until' must be a valid date in YYYY-MM-DD format")

    # excluded_dates: list of YYYY-MM-DD strings
    if "excluded_dates" in rr:
        if not isinstance(rr["excluded_dates"], list) or not all(
                isinstance(d, str) and is_valid_date(d) for d in rr["excluded_dates"]):
            raise ValueError(
                f"Exception at index {idx}: 'excluded_dates' must be a list of valid dates in YYYY-MM-DD format")


@typechecked
def validate_door_exception(exc: Dict[str, Any],
                            idx: Optional[int] = None) -> None:
    """
    Validates a v2 door exception object.

    Required: ``date`` (``YYYY-MM-DD``) and ``door_status`` (see
    :data:`pykada.enums.DOOR_STATUS_ENUM`). Unless ``all_day_default`` is
    True, ``start_time`` and ``end_time`` (``HH:MM`` or ``HH:MM:SS``) are also
    required. Optional: ``first_person_in`` / ``first_person_in_group_ids``,
    ``double_badge`` / ``double_badge_group_ids``, and a ``recurrence_rule``
    (see :func:`validate_recurrence_rule`).

    :param exc: The door exception object.
    :param idx: Optional index for context.
    :raises ValueError: If any required field is missing or invalid.
    """
    if "date" not in exc:
        raise ValueError(f"Exception at index {idx}: 'date' is required")
    require_non_empty_str(exc["date"], "date", idx)
    if not is_valid_date(exc["date"]):
        raise ValueError(
            f"Exception at index {idx}: 'date' must be in YYYY-MM-DD format")

    if "door_status" not in exc:
        raise ValueError(
            f"Exception at index {idx}: 'door_status' is required")
    require_non_empty_str(exc["door_status"], "door_status", idx)
    if exc["door_status"] not in list(DOOR_STATUS_ENUM.values()):
        raise ValueError(
            f"Exception at index {idx}: 'door_status' must be one of {list(DOOR_STATUS_ENUM.values())}")

    double_badge = exc.get("double_badge", False)
    if double_badge:
        if exc["door_status"] != DOOR_STATUS_ENUM["ACCESS_CONTROLLED"]:
            raise ValueError(
                f"Exception at index {idx}: when double_badge is True, door_status must be "
                f"'{DOOR_STATUS_ENUM['ACCESS_CONTROLLED']}'")

    if "double_badge_group_ids" in exc:
        if not double_badge:
            raise ValueError(
                f"Exception at index {idx}: double_badge must also be set to True if "
                f"double_badge_group_ids are provided")

    first_person_in = exc.get("first_person_in", False)
    if first_person_in:
        allowed_statuses = [
            DOOR_STATUS_ENUM["CARD_AND_CODE"],
            DOOR_STATUS_ENUM["ACCESS_CONTROLLED"],
            DOOR_STATUS_ENUM["UNLOCKED"],
        ]
        if exc["door_status"] not in allowed_statuses:
            raise ValueError(
                f"Exception at index {idx}: when first_person_in is True, door_status must be "
                f"one of {allowed_statuses}")

    if "first_person_in_group_ids" in exc:
        if not first_person_in:
            raise ValueError(
                f"Exception at index {idx}: first_person_in must also be set to True if "
                f"first_person_in_group_ids are provided")

    all_day = exc.get("all_day_default", False)
    if all_day:
        if exc["door_status"] != DOOR_STATUS_ENUM["ACCESS_CONTROLLED"]:
            raise ValueError(
                f"Exception at index {idx}: when all_day_default is True, door_status must be "
                f"'{DOOR_STATUS_ENUM['ACCESS_CONTROLLED']}'")
        if double_badge:
            raise ValueError(
                f"Exception at index {idx}: double_badge must be False when all_day_default is True")
        if first_person_in:
            raise ValueError(
                f"Exception at index {idx}: first_person_in must be False when all_day_default is True")
        if "start_time" in exc and exc["start_time"] not in (None, "", "00:00", "00:00:00"):
            raise ValueError(
                f"Exception at index {idx}: when all_day_default is True, start_time must be '00:00' or not provided")
        if "end_time" in exc and exc["end_time"] not in (None, "", "23:59", "23:59:59"):
            raise ValueError(
                f"Exception at index {idx}: when all_day_default is True, end_time must be '23:59' or not provided")
    else:
        for field in ("start_time", "end_time"):
            if field not in exc:
                raise ValueError(
                    f"Exception at index {idx}: '{field}' is required for non all-day exceptions")
            require_non_empty_str(exc[field], field, idx)
            if not _is_valid_exception_time(exc[field]):
                raise ValueError(
                    f"Exception at index {idx}: '{field}' must be in HH:MM or HH:MM:SS format")

    if "recurrence_rule" in exc:
        validate_recurrence_rule(exc["recurrence_rule"], idx)


# ---------------------------------------------------------------------------
# Module-level default client — shared across all functional wrappers.
# ---------------------------------------------------------------------------
_default_ac_client: Optional[AccessControlClient] = None


def _get_default_client() -> AccessControlClient:
    global _default_ac_client
    if _default_ac_client is None:
        _default_ac_client = AccessControlClient()
    return _default_ac_client


_WRAPPER_NOTE = ("This is a functional wrapper for its equivalent method in the "
                 "AccessControlClient. It reuses a module-level client configured "
                 "from VERKADA_API_KEY, making it best for one-off scripts. For "
                 "multiple API calls or a non-default key, instantiate an "
                 "AccessControlClient directly.")


@copy_docstring_from(AccessControlClient.resolve_user_id, note=_WRAPPER_NOTE)
@typechecked
def resolve_user_id(external_id: str):
    return _get_default_client().resolve_user_id(external_id)


@copy_docstring_from(AccessControlClient.get_all_access_users, note=_WRAPPER_NOTE)
@typechecked
def get_all_access_users(include_visitors: Optional[bool] = None):
    return _get_default_client().get_all_access_users(include_visitors)


@copy_docstring_from(AccessControlClient.get_access_users, note=_WRAPPER_NOTE)
@typechecked
def get_access_users(include_visitors: Optional[bool] = None, limit: Optional[int] = None,
                     cursor: Optional[str] = None):
    return _get_default_client().get_access_users(include_visitors, limit, cursor)


@copy_docstring_from(AccessControlClient.get_access_user, note=_WRAPPER_NOTE)
@typechecked
def get_access_user(user_id: str):
    return _get_default_client().get_access_user(user_id)


@copy_docstring_from(AccessControlClient.find_access_user, note=_WRAPPER_NOTE)
@typechecked
def find_access_user(user_id: Optional[str] = None, external_id: Optional[str] = None,
                     email: Optional[str] = None, employee_id: Optional[str] = None):
    return _get_default_client().find_access_user(user_id, external_id, email,
                                                  employee_id)


@copy_docstring_from(AccessControlClient.update_access_user_dates, note=_WRAPPER_NOTE)
@typechecked
def update_access_user_dates(user_id: str, start_date: Optional[Timestamp] = None,
                             end_date: Optional[Timestamp] = None):
    return _get_default_client().update_access_user_dates(user_id, start_date, end_date)


@copy_docstring_from(AccessControlClient.set_ble_unlock, note=_WRAPPER_NOTE)
@typechecked
def set_ble_unlock(user_id: str, active: bool):
    return _get_default_client().set_ble_unlock(user_id, active)


@copy_docstring_from(AccessControlClient.activate_remote_unlock_for_user,
                     note=_WRAPPER_NOTE)
@typechecked
def activate_remote_unlock_for_user(user_id: Optional[str] = None,
                                    external_id: Optional[str] = None,
                                    email: Optional[str] = None,
                                    employee_id: Optional[str] = None):
    return _get_default_client().activate_remote_unlock_for_user(user_id, external_id,
                                                                 email, employee_id)


@copy_docstring_from(AccessControlClient.deactivate_remote_unlock_for_user,
                     note=_WRAPPER_NOTE)
@typechecked
def deactivate_remote_unlock_for_user(user_id: Optional[str] = None,
                                      external_id: Optional[str] = None,
                                      email: Optional[str] = None,
                                      employee_id: Optional[str] = None):
    return _get_default_client().deactivate_remote_unlock_for_user(user_id,
                                                                   external_id, email,
                                                                   employee_id)


@copy_docstring_from(AccessControlClient.set_entry_code_for_user, note=_WRAPPER_NOTE)
@typechecked
def set_entry_code_for_user(user_id: str, entry_code: str, override: Optional[bool] = None):
    return _get_default_client().set_entry_code_for_user(user_id, entry_code, override)


@copy_docstring_from(AccessControlClient.remove_entry_code_for_user, note=_WRAPPER_NOTE)
@typechecked
def remove_entry_code_for_user(user_id: str):
    return _get_default_client().remove_entry_code_for_user(user_id)


@copy_docstring_from(AccessControlClient.send_pass_app_invite_for_user,
                     note=_WRAPPER_NOTE)
@typechecked
def send_pass_app_invite_for_user(user_id: str,
                                  invitation_methods: Optional[List[str]] = None):
    return _get_default_client().send_pass_app_invite_for_user(user_id,
                                                               invitation_methods)


@copy_docstring_from(AccessControlClient.create_pass_sdk_token, note=_WRAPPER_NOTE)
@typechecked
def create_pass_sdk_token(user_id: str, code_challenge: str):
    return _get_default_client().create_pass_sdk_token(user_id, code_challenge)


@copy_docstring_from(AccessControlClient.get_profile_photo, note=_WRAPPER_NOTE)
@typechecked
def get_profile_photo(user_id: str, original: Optional[bool] = None):
    return _get_default_client().get_profile_photo(user_id, original)


@copy_docstring_from(AccessControlClient.upload_profile_photo, note=_WRAPPER_NOTE)
@typechecked
def upload_profile_photo(user_id: str, photo_path: str, overwrite: Optional[bool] = None):
    return _get_default_client().upload_profile_photo(user_id, photo_path, overwrite)


@copy_docstring_from(AccessControlClient.delete_profile_photo, note=_WRAPPER_NOTE)
@typechecked
def delete_profile_photo(user_id: str):
    return _get_default_client().delete_profile_photo(user_id)


@copy_docstring_from(AccessControlClient.disable_face_unlock, note=_WRAPPER_NOTE)
@typechecked
def disable_face_unlock(user_id: Optional[str] = None, external_id: Optional[str] = None):
    return _get_default_client().disable_face_unlock(user_id, external_id)


@copy_docstring_from(AccessControlClient.enable_face_unlock_with_profile_photo,
                     note=_WRAPPER_NOTE)
@typechecked
def enable_face_unlock_with_profile_photo(user_id: Optional[str] = None,
                                          external_id: Optional[str] = None,
                                          overwrite: Optional[bool] = None):
    return _get_default_client().enable_face_unlock_with_profile_photo(user_id,
                                                                       external_id,
                                                                       overwrite)


@copy_docstring_from(AccessControlClient.enable_face_unlock_with_uploaded_photo,
                     note=_WRAPPER_NOTE)
@typechecked
def enable_face_unlock_with_uploaded_photo(photo_path: str, user_id: Optional[str] = None,
                                           external_id: Optional[str] = None,
                                           overwrite: Optional[bool] = None):
    return _get_default_client().enable_face_unlock_with_uploaded_photo(photo_path,
                                                                        user_id,
                                                                        external_id,
                                                                        overwrite)


@copy_docstring_from(AccessControlClient.invite_user_to_enroll_face_unlock,
                     note=_WRAPPER_NOTE)
@typechecked
def invite_user_to_enroll_face_unlock(user_id: Optional[str] = None,
                                      external_id: Optional[str] = None,
                                      invitation_methods: Optional[List[str]] = None):
    return _get_default_client().invite_user_to_enroll_face_unlock(user_id,
                                                                   external_id,
                                                                   invitation_methods)


@copy_docstring_from(AccessControlClient.add_card_to_user, note=_WRAPPER_NOTE)
@typechecked
def add_card_to_user(card_type: str, user_id: Optional[str] = None,
                     external_id: Optional[str] = None, card_number: Optional[str] = None,
                     card_number_hex: Optional[str] = None,
                     facility_code: Optional[str] = None, active: Optional[bool] = None):
    return _get_default_client().add_card_to_user(card_type, user_id, external_id,
                                                  card_number, card_number_hex,
                                                  facility_code, active)


@copy_docstring_from(AccessControlClient.activate_access_card, note=_WRAPPER_NOTE)
@typechecked
def activate_access_card(card_id: str, user_id: Optional[str] = None,
                         external_id: Optional[str] = None):
    return _get_default_client().activate_access_card(card_id, user_id, external_id)


@copy_docstring_from(AccessControlClient.deactivate_access_card, note=_WRAPPER_NOTE)
@typechecked
def deactivate_access_card(card_id: str, user_id: Optional[str] = None,
                           external_id: Optional[str] = None):
    return _get_default_client().deactivate_access_card(card_id, user_id, external_id)


@copy_docstring_from(AccessControlClient.delete_access_card, note=_WRAPPER_NOTE)
@typechecked
def delete_access_card(card_id: str, user_id: Optional[str] = None,
                       external_id: Optional[str] = None):
    return _get_default_client().delete_access_card(card_id, user_id, external_id)


@copy_docstring_from(AccessControlClient.add_license_plate_to_user, note=_WRAPPER_NOTE)
@typechecked
def add_license_plate_to_user(license_plate_number: str, user_id: Optional[str] = None,
                              external_id: Optional[str] = None, name: Optional[str] = None,
                              active: Optional[bool] = None):
    return _get_default_client().add_license_plate_to_user(license_plate_number,
                                                           user_id, external_id, name,
                                                           active)


@copy_docstring_from(AccessControlClient.set_license_plate_active, note=_WRAPPER_NOTE)
@typechecked
def set_license_plate_active(license_plate_number: str, active: bool,
                             user_id: Optional[str] = None, external_id: Optional[str] = None):
    return _get_default_client().set_license_plate_active(license_plate_number, active,
                                                          user_id, external_id)


@copy_docstring_from(AccessControlClient.delete_license_plate_from_user,
                     note=_WRAPPER_NOTE)
@typechecked
def delete_license_plate_from_user(license_plate_number: str,
                                   user_id: Optional[str] = None,
                                   external_id: Optional[str] = None):
    return _get_default_client().delete_license_plate_from_user(license_plate_number,
                                                                user_id, external_id)


@copy_docstring_from(AccessControlClient.add_mfa_code_to_user, note=_WRAPPER_NOTE)
@typechecked
def add_mfa_code_to_user(code: str, user_id: Optional[str] = None,
                         external_id: Optional[str] = None):
    return _get_default_client().add_mfa_code_to_user(code, user_id, external_id)


@copy_docstring_from(AccessControlClient.delete_mfa_code_from_user, note=_WRAPPER_NOTE)
@typechecked
def delete_mfa_code_from_user(code: str, user_id: Optional[str] = None,
                              external_id: Optional[str] = None):
    return _get_default_client().delete_mfa_code_from_user(code, user_id, external_id)


@copy_docstring_from(AccessControlClient.add_qr_code_to_user, note=_WRAPPER_NOTE)
@typechecked
def add_qr_code_to_user(encoding_type: str, user_id: Optional[str] = None,
                        external_id: Optional[str] = None, qr_code: Optional[str] = None,
                        card_number: Optional[str] = None,
                        card_number_hex: Optional[str] = None,
                        facility_code: Optional[str] = None, active: Optional[bool] = None,
                        activation_state: Optional[str] = None):
    return _get_default_client().add_qr_code_to_user(encoding_type, user_id,
                                                     external_id, qr_code, card_number,
                                                     card_number_hex, facility_code,
                                                     active, activation_state)


@copy_docstring_from(AccessControlClient.update_qr_code_state, note=_WRAPPER_NOTE)
@typechecked
def update_qr_code_state(encoding_type: str, user_id: Optional[str] = None,
                         external_id: Optional[str] = None, qr_code: Optional[str] = None,
                         card_number: Optional[str] = None,
                         card_number_hex: Optional[str] = None,
                         facility_code: Optional[str] = None, active: Optional[bool] = None,
                         activation_state: Optional[str] = None):
    return _get_default_client().update_qr_code_state(encoding_type, user_id,
                                                      external_id, qr_code,
                                                      card_number, card_number_hex,
                                                      facility_code, active,
                                                      activation_state)


@copy_docstring_from(AccessControlClient.delete_qr_code_from_user, note=_WRAPPER_NOTE)
@typechecked
def delete_qr_code_from_user(encoding_type: str, user_id: Optional[str] = None,
                             external_id: Optional[str] = None,
                             qr_code: Optional[str] = None,
                             card_number: Optional[str] = None,
                             card_number_hex: Optional[str] = None,
                             facility_code: Optional[str] = None):
    return _get_default_client().delete_qr_code_from_user(encoding_type, user_id,
                                                          external_id, qr_code,
                                                          card_number, card_number_hex,
                                                          facility_code)


@copy_docstring_from(AccessControlClient.get_all_access_groups, note=_WRAPPER_NOTE)
@typechecked
def get_all_access_groups():
    return _get_default_client().get_all_access_groups()


@copy_docstring_from(AccessControlClient.get_access_groups, note=_WRAPPER_NOTE)
@typechecked
def get_access_groups(limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().get_access_groups(limit, cursor)


@copy_docstring_from(AccessControlClient.get_access_group, note=_WRAPPER_NOTE)
@typechecked
def get_access_group(group_id: str):
    return _get_default_client().get_access_group(group_id)


@copy_docstring_from(AccessControlClient.create_access_group, note=_WRAPPER_NOTE)
@typechecked
def create_access_group(name: str):
    return _get_default_client().create_access_group(name)


@copy_docstring_from(AccessControlClient.delete_access_group, note=_WRAPPER_NOTE)
@typechecked
def delete_access_group(group_id: str):
    return _get_default_client().delete_access_group(group_id)


@copy_docstring_from(AccessControlClient.add_user_to_access_group, note=_WRAPPER_NOTE)
@typechecked
def add_user_to_access_group(group_id: str, user_id: str):
    return _get_default_client().add_user_to_access_group(group_id, user_id)


@copy_docstring_from(AccessControlClient.remove_user_from_access_group,
                     note=_WRAPPER_NOTE)
@typechecked
def remove_user_from_access_group(group_id: str, user_id: str):
    return _get_default_client().remove_user_from_access_group(group_id, user_id)


@copy_docstring_from(AccessControlClient.get_all_access_levels, note=_WRAPPER_NOTE)
@typechecked
def get_all_access_levels():
    return _get_default_client().get_all_access_levels()


@copy_docstring_from(AccessControlClient.get_access_levels, note=_WRAPPER_NOTE)
@typechecked
def get_access_levels(limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().get_access_levels(limit, cursor)


@copy_docstring_from(AccessControlClient.get_access_level, note=_WRAPPER_NOTE)
@typechecked
def get_access_level(access_level_id: str):
    return _get_default_client().get_access_level(access_level_id)


@copy_docstring_from(AccessControlClient.create_access_level, note=_WRAPPER_NOTE)
@typechecked
def create_access_level(name: str, sites: List[str], access_groups: List[str],
                        doors: List[str], access_schedule_events: List[Dict[str, str]]):
    return _get_default_client().create_access_level(name, sites, access_groups, doors,
                                                     access_schedule_events)


@copy_docstring_from(AccessControlClient.update_access_level, note=_WRAPPER_NOTE)
@typechecked
def update_access_level(access_level_id: str, name: Optional[str] = None,
                        sites: Optional[List[str]] = None,
                        access_groups: Optional[List[str]] = None,
                        doors: Optional[List[str]] = None):
    return _get_default_client().update_access_level(access_level_id, name, sites,
                                                     access_groups, doors)


@copy_docstring_from(AccessControlClient.delete_access_level, note=_WRAPPER_NOTE)
@typechecked
def delete_access_level(access_level_id: str):
    return _get_default_client().delete_access_level(access_level_id)


@copy_docstring_from(AccessControlClient.add_access_schedule_event_to_access_level,
                     note=_WRAPPER_NOTE)
@typechecked
def add_access_schedule_event_to_access_level(access_level_id: str, weekday: str,
                                              start_time: str, end_time: str):
    return _get_default_client().add_access_schedule_event_to_access_level(access_level_id,
                                                                           weekday,
                                                                           start_time,
                                                                           end_time)


@copy_docstring_from(AccessControlClient.get_access_schedule_event, note=_WRAPPER_NOTE)
@typechecked
def get_access_schedule_event(access_level_id: str, event_id: str):
    return _get_default_client().get_access_schedule_event(access_level_id, event_id)


@copy_docstring_from(AccessControlClient.update_access_schedule_event_on_access_level,
                     note=_WRAPPER_NOTE)
@typechecked
def update_access_schedule_event_on_access_level(access_level_id: str, event_id: str,
                                                 weekday: Optional[str] = None,
                                                 start_time: Optional[str] = None,
                                                 end_time: Optional[str] = None):
    return _get_default_client().update_access_schedule_event_on_access_level(access_level_id,
                                                                              event_id,
                                                                              weekday,
                                                                              start_time,
                                                                              end_time)


@copy_docstring_from(AccessControlClient.delete_access_schedule_event_on_access_level,
                     note=_WRAPPER_NOTE)
@typechecked
def delete_access_schedule_event_on_access_level(access_level_id: str, event_id: str):
    return _get_default_client().delete_access_schedule_event_on_access_level(access_level_id,
                                                                              event_id)


@copy_docstring_from(AccessControlClient.get_all_doors, note=_WRAPPER_NOTE)
@typechecked
def get_all_doors(door_ids: Optional[List[str]] = None, site_ids: Optional[List[str]] = None):
    return _get_default_client().get_all_doors(door_ids, site_ids)


@copy_docstring_from(AccessControlClient.get_doors, note=_WRAPPER_NOTE)
@typechecked
def get_doors(door_ids: Optional[List[str]] = None, site_ids: Optional[List[str]] = None,
              limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().get_doors(door_ids, site_ids, limit, cursor)


@copy_docstring_from(AccessControlClient.unlock_door_as_admin, note=_WRAPPER_NOTE)
@typechecked
def unlock_door_as_admin(door_id: str):
    return _get_default_client().unlock_door_as_admin(door_id)


@copy_docstring_from(AccessControlClient.unlock_door_as_user, note=_WRAPPER_NOTE)
@typechecked
def unlock_door_as_user(door_id: str, user_id: Optional[str] = None,
                        external_id: Optional[str] = None):
    return _get_default_client().unlock_door_as_user(door_id, user_id, external_id)


@copy_docstring_from(AccessControlClient.get_all_door_exception_calendars,
                     note=_WRAPPER_NOTE)
@typechecked
def get_all_door_exception_calendars(last_updated_after: Optional[Timestamp] = None):
    return _get_default_client().get_all_door_exception_calendars(last_updated_after)


@copy_docstring_from(AccessControlClient.get_door_exception_calendars,
                     note=_WRAPPER_NOTE)
@typechecked
def get_door_exception_calendars(last_updated_after: Optional[Timestamp] = None,
                                 limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().get_door_exception_calendars(last_updated_after,
                                                              limit, cursor)


@copy_docstring_from(AccessControlClient.get_door_exception_calendar,
                     note=_WRAPPER_NOTE)
@typechecked
def get_door_exception_calendar(calendar_id: str):
    return _get_default_client().get_door_exception_calendar(calendar_id)


@copy_docstring_from(AccessControlClient.create_door_exception_calendar,
                     note=_WRAPPER_NOTE)
@typechecked
def create_door_exception_calendar(name: str, doors: List[str],
                                   exceptions: List[Dict[str, Any]]):
    return _get_default_client().create_door_exception_calendar(name, doors, exceptions)


@copy_docstring_from(AccessControlClient.update_door_exception_calendar,
                     note=_WRAPPER_NOTE)
@typechecked
def update_door_exception_calendar(calendar_id: str, name: str, doors: List[str],
                                   exceptions: List[Dict[str, Any]]):
    return _get_default_client().update_door_exception_calendar(calendar_id, name,
                                                                doors, exceptions)


@copy_docstring_from(AccessControlClient.delete_door_exception_calendar,
                     note=_WRAPPER_NOTE)
@typechecked
def delete_door_exception_calendar(calendar_id: str):
    return _get_default_client().delete_door_exception_calendar(calendar_id)


@copy_docstring_from(AccessControlClient.get_exception_on_door_exception_calendar,
                     note=_WRAPPER_NOTE)
@typechecked
def get_exception_on_door_exception_calendar(calendar_id: str, exception_id: str):
    return _get_default_client().get_exception_on_door_exception_calendar(calendar_id,
                                                                          exception_id)


@copy_docstring_from(AccessControlClient.add_exception_to_door_exception_calendar,
                     note=_WRAPPER_NOTE)
@typechecked
def add_exception_to_door_exception_calendar(calendar_id: str, exception: Dict[str, Any]):
    return _get_default_client().add_exception_to_door_exception_calendar(calendar_id,
                                                                          exception)


@copy_docstring_from(AccessControlClient.update_exception_on_door_exception_calendar,
                     note=_WRAPPER_NOTE)
@typechecked
def update_exception_on_door_exception_calendar(calendar_id: str, exception_id: str,
                                                exception: Dict[str, Any]):
    return _get_default_client().update_exception_on_door_exception_calendar(calendar_id,
                                                                             exception_id,
                                                                             exception)


@copy_docstring_from(AccessControlClient.delete_exception_on_door_exception_calendar,
                     note=_WRAPPER_NOTE)
@typechecked
def delete_exception_on_door_exception_calendar(calendar_id: str, exception_id: str):
    return _get_default_client().delete_exception_on_door_exception_calendar(calendar_id,
                                                                             exception_id)


@copy_docstring_from(AccessControlClient.get_all_access_scenarios, note=_WRAPPER_NOTE)
@typechecked
def get_all_access_scenarios(scenario_ids: Optional[List[str]] = None,
                             site_ids: Optional[List[str]] = None,
                             scenario_types: Optional[List[str]] = None):
    return _get_default_client().get_all_access_scenarios(scenario_ids, site_ids,
                                                          scenario_types)


@copy_docstring_from(AccessControlClient.get_access_scenarios, note=_WRAPPER_NOTE)
@typechecked
def get_access_scenarios(scenario_ids: Optional[List[str]] = None,
                         site_ids: Optional[List[str]] = None,
                         scenario_types: Optional[List[str]] = None,
                         limit: Optional[int] = None, cursor: Optional[str] = None):
    return _get_default_client().get_access_scenarios(scenario_ids, site_ids,
                                                      scenario_types, limit, cursor)


@copy_docstring_from(AccessControlClient.activate_access_scenario, note=_WRAPPER_NOTE)
@typechecked
def activate_access_scenario(scenario_id: str):
    return _get_default_client().activate_access_scenario(scenario_id)


@copy_docstring_from(AccessControlClient.release_access_scenario, note=_WRAPPER_NOTE)
@typechecked
def release_access_scenario(scenario_id: str):
    return _get_default_client().release_access_scenario(scenario_id)
