from typing import Optional

from pykada.api_tokens import VerkadaTokenManager
from pykada.verkada_requests import VerkadaRequestManager, \
    get_default_request_manager


class BaseClient:
    def __init__(self,
                 api_key: Optional[str] = None,
                 token_manager: Optional[VerkadaTokenManager] = None,
                 request_manager: Optional[VerkadaRequestManager] = None):
        """
        Initialize the client with either an API key or a token manager.
        If not key is provided, a default token manager will be used based
        on the environment configuration (VERKADA_API_KEY in a .env file).

        :param api_key: Optional API key for authentication.
        :param token_manager: Optional token manager for handling tokens.
        """
        # If a request_manager is provided and neither api_key or
        # token_manager are provided, use it directly.
        if request_manager and not (api_key or token_manager):
            self._request_manager = request_manager

        # If both request_manager and api_key/token_manager are provided,
        elif request_manager and (api_key or token_manager):
            raise ValueError(
                "Cannot provide both request_manager and "
                "api_key/token_manager. Use one or the other.")

        # If both api_key and token_manager are provided, raise an error
        if token_manager and api_key:
            raise ValueError(
                "Cannot provide both api_key and token_manager. "
                "Use one or the other.")

        # Validate token_manager if provided
        if token_manager:
            if not isinstance(token_manager, VerkadaTokenManager):
                raise TypeError(
                    "token_manager must be an instance of VerkadaTokenManager.")

            # If a token manager is provided, use it directly
            self._request_manager = VerkadaRequestManager(
                token_manager=token_manager
            )
            return

        # Validate api_key if provided
        if api_key and not api_key.strip():
            raise ValueError("api_key must be a non-empty string.")

        # If an api_key is provided, create a new token manager
        if api_key:
            self._request_manager = VerkadaRequestManager(
                token_manager=VerkadaTokenManager(
                    api_key=api_key
                ))
            return

        # If no api_key, token_manager, or request manager is provided,
        # use the default token manager
        try:
            self._request_manager = get_default_request_manager()
        except RuntimeError as e:
            raise RuntimeError(
                "Default request manager is not initialized. "
                "Ensure that VERKADA_API_KEY is set in your environment"
                "if using the default request manager."
            ) from e

    @property
    def request_manager(self) -> VerkadaRequestManager:
        """
        Returns the request manager used by this client.
        """
        return self._request_manager

    @request_manager.setter
    def request_manager(self, request_manager: VerkadaRequestManager):
        if not isinstance(request_manager, VerkadaRequestManager):
            raise TypeError(
                "request_manager must be an instance of VerkadaRequestManager.")
        self._request_manager = request_manager