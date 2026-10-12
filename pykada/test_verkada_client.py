from unittest.mock import MagicMock

import pytest

from pykada.api_tokens import VerkadaTokenManager
from pykada.cameras import CamerasClient
from pykada.access_control import AccessControlClient
from pykada.classic_alarms import ClassicAlarmsClient
from pykada.core_command import CoreCommandClient
from pykada.events import EventsClient
from pykada.helix import HelixClient
from pykada.sensors import SensorsClient
from pykada.workplace import WorkplaceClient
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


ALL_CLIENTS = [CamerasClient, AccessControlClient, SensorsClient, CoreCommandClient,
               EventsClient, WorkplaceClient, HelixClient, ClassicAlarmsClient]


@pytest.mark.parametrize("client_cls", ALL_CLIENTS)
def test_every_client_accepts_region(client_cls):
    client = client_cls(api_key="key", region="eu")
    assert client.request_manager.base_url == "https://api.eu.verkada.com"
    assert client.request_manager.token_manager._token_url == \
        "https://api.eu.verkada.com/token"


def test_base_url_with_token_manager():
    tm = VerkadaTokenManager(api_key="key")
    client = BaseClient(token_manager=tm, base_url="https://proxy.test")
    assert client.request_manager.base_url == "https://proxy.test"
    assert client.request_manager.token_manager is tm


def test_region_from_environment(monkeypatch):
    monkeypatch.setenv("VERKADA_REGION", "au")
    assert CamerasClient(api_key="key").request_manager.base_url == \
        "https://api.au.verkada.com"


@pytest.mark.parametrize("kwargs", [{"region": "eu"}, {"base_url": "https://x.test"}])
def test_region_with_request_manager_raises(kwargs):
    with pytest.raises(ValueError, match="region/base_url"):
        BaseClient(request_manager=_request_manager(), **kwargs)


def test_region_and_base_url_together_raise():
    with pytest.raises(ValueError, match="not both"):
        BaseClient(api_key="key", region="eu", base_url="https://x.test")


def test_unknown_region_raises():
    with pytest.raises(ValueError, match="region"):
        BaseClient(api_key="key", region="mars")


def test_client_context_manager_closes_request_manager():
    rm = _request_manager()
    rm.close = MagicMock()
    with BaseClient(request_manager=rm):
        pass
    rm.close.assert_called_once()
