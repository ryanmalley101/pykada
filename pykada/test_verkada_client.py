from unittest.mock import MagicMock

import pytest

from pykada.api_tokens import VerkadaTokenManager
from pykada.cameras import CamerasClient
from pykada.access_control import AccessControlClient
from pykada.verkada_client import BaseClient
from pykada.verkada_requests import VerkadaRequestManager


def _request_manager():
    return VerkadaRequestManager(token_manager=MagicMock())


def test_explicit_request_manager_is_used():
    rm = _request_manager()
    client = BaseClient(request_manager=rm)
    assert client.request_manager is rm


def test_request_manager_with_api_key_raises():
    with pytest.raises(ValueError, match="Cannot provide both request_manager"):
        BaseClient(api_key="key", request_manager=_request_manager())


def test_api_version_applied_to_request_manager():
    rm = _request_manager()
    BaseClient(request_manager=rm, api_version="2026-10-01")
    assert rm.api_version == "2026-10-01"


def test_api_version_defaults_to_none():
    client = BaseClient(request_manager=_request_manager())
    assert client.request_manager.api_version is None


def test_api_version_with_api_key():
    client = BaseClient(api_key="key", api_version="2026-10-01")
    assert isinstance(client.request_manager.token_manager, VerkadaTokenManager)
    assert client.request_manager.api_version == "2026-10-01"


@pytest.mark.parametrize("client_cls", [CamerasClient, AccessControlClient])
def test_product_clients_forward_request_manager_and_api_version(client_cls):
    rm = _request_manager()
    client = client_cls(request_manager=rm, api_version="2026-10-01")
    assert client.request_manager is rm
    assert rm.api_version == "2026-10-01"
