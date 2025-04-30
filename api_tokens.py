import os
import time
import requests

def get_api_token():
    """
    Retrieves the temporary Verkada API token.

    Checks for a cached token in the environment and refreshes it if either:
      - There is no cached token.
      - The cached token is older than 25 minutes. This is to ensure that
      if the script takes longer than a few minutes between fetching the
      token and making the call, it will still have a valid token

    Returns:
        str: The valid API token.

    Raises:
        RuntimeError: If the API key is missing or token retrieval fails.
    """
    api_key = os.getenv("VERKADA_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing VERKADA_API_KEY. Please set it as an environment "
            "variable or in a .env file."
        )

    api_token = os.getenv("VERKADA_API_TOKEN")
    token_timestamp = int(os.getenv("TOKEN_TIMESTAMP", "0"))

    # Check if token is missing or expired (25 minutes = 1500 seconds)
    if api_token and token_timestamp and time.time() - token_timestamp > 1500:
        return api_token

    headers = {"accept": "application/json",
               "x-api-key": api_key}

    url = "https://api.verkada.com/token"
    # Depending on API requirements, you might need to include your api_key in the request.
    response = requests.post(url, headers=headers)

    if response.status_code != 200:
        raise RuntimeError(
            "Error retrieving API token. Check whether your API "
            "key is valid in the .env file."
        )

    try:
        api_token = response.json()["token"]
    except (KeyError, ValueError) as e:
        raise RuntimeError(
            "Unexpected response structure: missing 'token'.") from e

    # Update the environment for caching
    os.environ["VERKADA_API_TOKEN"] = api_token
    os.environ["TOKEN_TIMESTAMP"] = str(int(time.time()))
    return api_token


