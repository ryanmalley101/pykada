from typing import Optional

from typeguard import typechecked

from pykada.api_tokens import VerkadaTokenManager
from pykada.verkada_requests import VerkadaRequestManager


class BaseClient:
    """
    Base class for every pykada product client.

    Clients reuse one :class:`~pykada.verkada_requests.VerkadaRequestManager`
    (token, HTTP connections, retry policy) for all their calls. Use a client
    as a context manager, or call :meth:`close`, to release its connections.
    """

    @typechecked
    def __init__(self,
                 api_key: Optional[str] = None,
                 token_manager: Optional[VerkadaTokenManager] = None,
                 request_manager: Optional[VerkadaRequestManager] = None,
                 api_version: Optional[str] = None,
                 region: Optional[str] = None,
                 base_url: Optional[str] = None):
        """
        Initialize the client with an API key, a token manager, or a request
        manager. If none is given, ``VERKADA_API_KEY`` from the environment or
        a ``.env`` file in the working directory is used.

        :param api_key: Optional API key for authentication.
        :param token_manager: Optional token manager for handling tokens. It
            must already point at the right region.
        :param request_manager: Optional pre-built request manager to reuse
            (for sharing connections and tokens across clients). It carries
            its own region, so it can't be combined with ``region``/``base_url``.
        :param api_version: Optional ``x-verkada-api-version`` header value
            sent with every request from this client.
        :param region: The organization's API region, e.g. ``"eu"``, ``"au"``
            or ``"oh"`` (see :data:`pykada.endpoints.REGION_ENUM`). Defaults to
            ``VERKADA_REGION`` from the environment, else the US host.
        :param base_url: A full API base URL instead of ``region``.
        :raises ValueError: If conflicting options are given.
        """
        if request_manager is not None:
            if api_key or token_manager:
                raise ValueError(
                    "Cannot provide both request_manager and "
                    "api_key/token_manager. Use one or the other.")
            if region or base_url:
                raise ValueError(
                    "Cannot provide region/base_url with request_manager; "
                    "set them on the request manager instead.")
            self._request_manager = request_manager
        else:
            if api_key is not None and not api_key.strip():
                raise ValueError("api_key must be a non-empty string.")
            self._request_manager = VerkadaRequestManager(
                api_key=api_key, token_manager=token_manager,
                region=region, base_url=base_url)

        if api_version is not None:
            self._request_manager.api_version = api_version

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

    def close(self) -> None:
        """Release this client's pooled HTTP connections."""
        self._request_manager.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
