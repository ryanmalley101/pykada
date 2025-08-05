# File: pykada/verkada_client.py
from pykada.api_tokens import VerkadaTokenManager
from pykada.cameras.cameras import CamerasClient
from pykada.endpoints import GET_TOKEN_ENDPOINT
from pykada.verkada_requests import send_request, get_default_headers

class VerkadaClient(CamerasClient):
    def __init__(self, api_key: str = None):
        """
        Initialize the VerkadaClient with an optional API key.
        If no API key is provided, it will fall back to the default from the .env file.
        """
        self.api_key = api_key
        # Instantiate managers for each token type
        self.api_token_manager = VerkadaTokenManager(
            api_key=api_key,
            token_url=GET_TOKEN_ENDPOINT,
            response_json_key="token",
            token_lifetime_minutes=30
        )


    def get_default_headers(self):
        """
        Build default headers using the client's API key if available.
        """
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-verkada-auth": self.api_token_manager.get_token()
        }
        return headers

    def send_request(self, method, url, **kwargs):
        """
        Wrapper around the centralized send_request function, using the client's headers.
        """
        headers = kwargs.pop("headers", {})
        headers.update(self.get_default_headers())
        return send_request(method, url, headers=headers, **kwargs)