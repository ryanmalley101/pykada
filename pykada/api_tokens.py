import datetime
import os
import requests
from dotenv import load_dotenv, find_dotenv

from pykada.endpoints import STREAMING_TOKEN_ENDPOINT, GET_TOKEN_ENDPOINT

class VerkadaTokenManager:
    """
    Manages a specific type of Verkada API token, caching it and refreshing it only when needed.
    """

    def __init__(self,
                 api_key: str,
                 token_url: str = GET_TOKEN_ENDPOINT,
                 response_json_key: str = "token",
                 token_lifetime_minutes: int = 30):
        """
        Initializes the token manager for a specific token type.

        Args:
            api_key (str): Your Verkada API key.
            token_url (str): The URL endpoint to fetch this specific token (e.g., "https://api.verkada.com/token").
            response_json_key (str): The key in the JSON response that holds the token value (e.g., "token" or "jwt").
            token_lifetime_minutes (int): The expected lifetime of the token in minutes. Defaults to 30.
        """

        if not api_key:
            raise RuntimeError(
                "Missing API key. Please provide it to the VerkadaTokenManager."
            )
        self._api_key = api_key
        print(api_key)
        self._token_url = token_url
        self._response_json_key = response_json_key
        self._token_lifetime_minutes = token_lifetime_minutes

        self._token = None
        self._token_expiry = None  # datetime object representing when the token expires

        # Define a buffer time before actual expiry to refresh the token.
        # We'll use 25 minutes (1500 seconds) as a safe buffer for a 30-minute token.
        self._refresh_buffer_seconds = 25 * 60

    def _fetch_new_token(self) -> tuple[str, datetime.datetime]:
        """
        Fetches a new token and its expiry from the Verkada API using the specified URL.

        Returns:
            tuple[str, datetime.datetime]: A tuple containing the new token string
                                           and its expiry datetime.

        Raises:
            RuntimeError: If token retrieval fails or the response structure is unexpected.
        """
        print(f"Fetching a new token from {self._token_url}...")
        headers = {
            "accept": "application/json",
            "x-api-key": self._api_key
        }

        print(headers)

        try:
            # Determine if it's a GET or POST based on the endpoint (as per original code)
            if self._response_json_key == "jwt": # Assuming streaming token uses GET
                response = requests.get(self._token_url, headers=headers)
            else: # Assuming regular token uses POST
                response = requests.post(self._token_url, headers=headers)

            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"Error retrieving API token from {self._token_url}. Check API key validity or network."
            ) from e

        try:
            response_data = response.json()
            new_token = response_data[self._response_json_key]
        except (KeyError, ValueError) as e:
            raise RuntimeError(
                f"Unexpected response structure: missing '{self._response_json_key}' in response from {self._token_url}."
            ) from e

        # Calculate expiry based on the specified token lifetime
        new_token_expiry = datetime.datetime.now(datetime.timezone.utc) + \
                           datetime.timedelta(minutes=self._token_lifetime_minutes)
        print(f"New token fetched successfully. Expires at: {new_token_expiry}")
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
                print(f"Using cached token for {self._response_json_key} (still valid).")
                return self._token
            else:
                print(f"Cached token for {self._response_json_key} expiring soon ({int(time_until_expiry)} seconds left). Refreshing...")
        else:
            print(f"No token cached for {self._response_json_key} or token already expired. Fetching a new one.")

        # If we reach here, the token needs to be refreshed or fetched for the first time
        try:
            self._token, self._token_expiry = self._fetch_new_token()
            return self._token
        except RuntimeError as e:
            print(f"Failed to get a valid token: {e}")
            raise # Re-raise the exception after logging

# --- Global Token Manager Instances ---
# Load environment variables once at startup.
load_dotenv(dotenv_path=find_dotenv(), override=True)

# Retrieve the API key once from the environment
verkada_api_key = os.getenv("VERKADA_API_KEY", None)

# Instantiate managers for each token type
default_token_manager = VerkadaTokenManager(
    api_key=verkada_api_key,
    token_url=GET_TOKEN_ENDPOINT,
    response_json_key="token",
    token_lifetime_minutes=30
) if verkada_api_key else None

default_streaming_token_manager = VerkadaTokenManager(
    api_key=verkada_api_key,
    token_url=STREAMING_TOKEN_ENDPOINT,
    response_json_key="jwt",
    token_lifetime_minutes=30
) if verkada_api_key else None

def get_default_token_manager():
    """
    Returns the default token manager instance for API tokens.
    This is useful for cases where you want to use the default token manager
    without explicitly importing it.
    """
    if default_token_manager is None:
        raise RuntimeError(
            "Default token manager is not initialized. "
            "Ensure that VERKADA_API_KEY is set in your environment"
            "if using the default token manager."
        )

    return default_token_manager


# --- Public functions for your library ---
def get_default_api_token() -> str:
    """
    Retrieves the temporary Verkada API token using the cached manager.
    """
    if default_token_manager is None:
        raise RuntimeError(
            "Default token manager is not initialized. "
            "Ensure that VERKADA_API_KEY is set in your environment"
            "if using the default token manager."
        )

    return default_token_manager.get_token()
