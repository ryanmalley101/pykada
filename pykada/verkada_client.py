# File: pykada/verkada_client.py
from typing import Optional

from pykada.api_tokens import VerkadaTokenManager, get_default_token_manager


class BaseClient:
    def __init__(self, api_key: Optional[str] = None,
                 token_manager: Optional[VerkadaTokenManager] = None):
        """
        Initialize the client with either an API key or a token manager.
        :param api_key: Optional API key for authentication.
        :param token_manager: Optional token manager for handling tokens.
        """
        if token_manager and api_key:
            raise ValueError(
                "Cannot provide both api_key and token_manager. Use one or the other.")

        if token_manager:
            if not isinstance(token_manager, VerkadaTokenManager):
                raise TypeError(
                    "token_manager must be an instance of VerkadaTokenManager.")
            self.token_manager = token_manager
        else:
            if api_key and not api_key.strip():
                raise ValueError("api_key must be a non-empty string.")
            self.token_manager = VerkadaTokenManager(
                api_key=api_key) if api_key else get_default_token_manager()