"""
Token management for pykada.

:class:`VerkadaTokenManager` fetches and caches a short-lived Verkada API
token, automatically refreshing it before expiry (25-minute buffer on a
30-minute token lifetime).

Module-level helpers :func:`get_default_token_manager` and
:func:`get_default_api_token` provide a shared manager bootstrapped from the
``VERKADA_API_KEY`` environment variable or a ``.env`` file. The ``.env`` file
is looked up from the current working directory the first time a default is
needed, and never overrides variables already set in the environment.

The region comes from ``VERKADA_BASE_URL`` or ``VERKADA_REGION`` when a client
isn't given ``region=``/``base_url=`` explicitly.
"""
import datetime
import logging
import os
from typing import Optional

import requests
from dotenv import load_dotenv, find_dotenv

from pykada.endpoints import (
    DEFAULT_BASE_URL,
    GET_TOKEN_ENDPOINT,
    V2_STREAMING_TOKEN_ENDPOINT,
    base_url_for_region,
    rebase_url,
)
from pykada.exceptions import VerkadaAuthError, VerkadaError

logger = logging.getLogger(__name__)

TOKEN_TIMEOUT_SECONDS = 30


def load_env_file() -> None:
    """
    Load a ``.env`` file from the current working directory (or its parents).

    Variables already set in the environment win, so an exported
    ``VERKADA_API_KEY`` is never replaced by a stale ``.env`` value.
    """
    path = find_dotenv(usecwd=True)
    if path:
        load_dotenv(dotenv_path=path, override=False)


def resolve_base_url(region: Optional[str] = None, base_url: Optional[str] = None) -> str:
    """
    Work out which API host to use.

    Precedence: an explicit ``base_url``, then an explicit ``region``, then the
    ``VERKADA_BASE_URL`` and ``VERKADA_REGION`` environment variables (including
    ``.env``), then the default ``https://api.verkada.com``.

    :param region: A region such as ``"eu"`` or ``"api.eu"``; see
        :data:`pykada.endpoints.REGION_ENUM`.
    :param base_url: A full base URL, e.g. ``"https://api.eu.verkada.com"``
        (useful for proxies or testing).
    :raises ValueError: If both are given or the region is unknown.
    """
    if region and base_url:
        raise ValueError("Provide region or base_url, not both.")
    if base_url:
        return base_url.rstrip("/")
    if region:
        return base_url_for_region(region)
    load_env_file()
    if os.getenv("VERKADA_BASE_URL"):
        return os.environ["VERKADA_BASE_URL"].rstrip("/")
    if os.getenv("VERKADA_REGION"):
        return base_url_for_region(os.environ["VERKADA_REGION"])
    return DEFAULT_BASE_URL

class VerkadaTokenManager:
    """
    Manages a specific type of Verkada API token, caching it and refreshing it only when needed.
    """

    def __init__(self,
                 api_key: str,
                 token_url: str = GET_TOKEN_ENDPOINT,
                 response_json_key: str = "token",
                 token_lifetime_minutes: int = 30,
                 base_url: Optional[str] = None):
        """
        Initializes the token manager for a specific token type.

        Args:
            api_key (str): Your Verkada API key.
            token_url (str): The URL endpoint to fetch this specific token (e.g., "https://api.verkada.com/token").
            response_json_key (str): The key in the JSON response that holds the token value (e.g., "token" or "jwt").
            token_lifetime_minutes (int): The expected lifetime of the token in minutes. Defaults to 30.
            base_url (str): API base URL for the organization's region, e.g.
                "https://api.eu.verkada.com". When given, ``token_url`` is moved
                onto that host. Defaults to ``token_url`` as passed.
        """

        if not api_key:
            raise VerkadaAuthError(
                "Missing API key. Please provide it to the VerkadaTokenManager."
            )
        self._api_key = api_key
        self._base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._token_url = rebase_url(token_url, base_url) if base_url else token_url
        self._response_json_key = response_json_key
        self._token_lifetime_minutes = token_lifetime_minutes

        self._token = None
        self._token_expiry = None  # datetime object representing when the token expires

        # Define a buffer time before actual expiry to refresh the token.
        # We'll use 25 minutes (1500 seconds) as a safe buffer for a 30-minute token.
        self._refresh_buffer_seconds = 25 * 60

    @property
    def api_key(self) -> str:
        """The API key backing this token manager, so a second manager
        (e.g. for a different token type, like streaming JWTs) can be
        built for the same credential without re-plumbing it."""
        return self._api_key

    @property
    def base_url(self) -> str:
        """The API base URL this manager fetches tokens from."""
        return self._base_url

    def _fetch_new_token(self) -> tuple[str, datetime.datetime]:
        """
        Fetches a new token and its expiry from the Verkada API using the specified URL.

        Returns:
            tuple[str, datetime.datetime]: A tuple containing the new token string
                                           and its expiry datetime.

        Raises:
            RuntimeError: If token retrieval fails or the response structure is unexpected.
        """
        logger.debug(f"Fetching a new token from {self._token_url}...")
        headers = {
            "accept": "application/json",
            "x-api-key": self._api_key
        }

        try:
            # Determine if it's a GET or POST based on the endpoint (as per original code)
            if self._response_json_key == "jwt": # Assuming streaming token uses GET
                response = requests.get(self._token_url, headers=headers,
                                        timeout=TOKEN_TIMEOUT_SECONDS)
            else: # Assuming regular token uses POST
                response = requests.post(self._token_url, headers=headers,
                                         timeout=TOKEN_TIMEOUT_SECONDS)
        except requests.exceptions.RequestException as e:
            raise VerkadaError(
                f"Network error fetching token from {self._token_url}: {e}",
                endpoint=self._token_url,
            ) from e

        if response.status_code == 401:
            raise VerkadaAuthError(
                "Invalid API key. Token request returned 401 Unauthorized.",
                status_code=401,
                endpoint=self._token_url,
            )
        if not response.ok:
            raise VerkadaError(
                f"Token request to {self._token_url} failed with HTTP {response.status_code}: {response.text}",
                status_code=response.status_code,
                response_body=response.text,
                endpoint=self._token_url,
            )

        try:
            response_data = response.json()
            new_token = response_data[self._response_json_key]
        except (KeyError, ValueError) as e:
            raise VerkadaError(
                f"Unexpected token response from {self._token_url}: "
                f"missing '{self._response_json_key}' key.",
                endpoint=self._token_url,
            ) from e

        # Calculate expiry based on the specified token lifetime
        new_token_expiry = datetime.datetime.now(datetime.timezone.utc) + \
                           datetime.timedelta(minutes=self._token_lifetime_minutes)
        logger.debug(f"New token fetched successfully. Expires at: {new_token_expiry}")
        return new_token, new_token_expiry

    def get_token(self) -> str:
        """
        Retrieves the current valid API token. If the token is missing or
        about to expire, a new one is fetched.

        Returns:
            str: The valid Verkada API token.
        """
        current_time_utc = datetime.datetime.now(datetime.timezone.utc)

        # Check if a token exists and if it's still valid (with buffer)
        if self._token and self._token_expiry:
            time_until_expiry = (self._token_expiry - current_time_utc).total_seconds()
            if time_until_expiry > self._refresh_buffer_seconds:
                logger.debug(f"Using cached token for {self._response_json_key} (still valid).")
                return self._token
            else:
                logger.debug(f"Cached token for {self._response_json_key} expiring soon ({int(time_until_expiry)} seconds left). Refreshing...")
        else:
            logger.debug(f"No token cached for {self._response_json_key} or token already expired. Fetching a new one.")

        # If we reach here, the token needs to be refreshed or fetched for the first time
        try:
            self._token, self._token_expiry = self._fetch_new_token()
            return self._token
        except RuntimeError as e:
            logger.debug(f"Failed to get a valid token: {e}")
            raise # Re-raise the exception after logging

# --- Default token managers ---
# Built lazily from VERKADA_API_KEY (environment or .env) on first use, so a key
# set after import still works and importing pykada has no side effects.
default_token_manager: Optional[VerkadaTokenManager] = None
default_streaming_token_manager: Optional[VerkadaTokenManager] = None

_NO_KEY_MESSAGE = ("No API key found. Set VERKADA_API_KEY in your environment "
                   "or a .env file, or pass api_key directly to the client.")


def _build_default_managers() -> None:
    global default_token_manager, default_streaming_token_manager
    load_env_file()
    api_key = os.getenv("VERKADA_API_KEY")
    if not api_key:
        return
    base_url = resolve_base_url()
    if default_token_manager is None:
        default_token_manager = VerkadaTokenManager(
            api_key=api_key, token_url=GET_TOKEN_ENDPOINT, response_json_key="token",
            token_lifetime_minutes=30, base_url=base_url)
    if default_streaming_token_manager is None:
        default_streaming_token_manager = VerkadaTokenManager(
            api_key=api_key, token_url=V2_STREAMING_TOKEN_ENDPOINT, response_json_key="jwt",
            token_lifetime_minutes=30, base_url=base_url)


def get_default_token_manager() -> VerkadaTokenManager:
    """
    Returns the shared token manager for API tokens, built from
    ``VERKADA_API_KEY`` on first use.

    :raises VerkadaAuthError: If no API key is configured.
    """
    if default_token_manager is None:
        _build_default_managers()
    if default_token_manager is None:
        raise VerkadaAuthError(_NO_KEY_MESSAGE)
    return default_token_manager


def get_default_streaming_token_manager() -> VerkadaTokenManager:
    """
    Returns the shared token manager for streaming JWTs, built from
    ``VERKADA_API_KEY`` on first use.

    This is a distinct token from the standard ``x-verkada-auth`` API
    token: it's fetched from the footage token endpoint and is what the
    footage streaming endpoint expects as its ``jwt`` query parameter.

    :raises VerkadaAuthError: If no API key is configured.
    """
    if default_streaming_token_manager is None:
        _build_default_managers()
    if default_streaming_token_manager is None:
        raise VerkadaAuthError(_NO_KEY_MESSAGE)
    return default_streaming_token_manager


def get_default_api_token() -> str:
    """
    Retrieves a valid API token from the default token manager.

    :raises VerkadaAuthError: If no API key is configured.
    """
    return get_default_token_manager().get_token()
