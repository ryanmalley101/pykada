import os
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

import pykada.api_tokens as api_tokens
from pykada.api_tokens import (
    VerkadaTokenManager,
    get_default_streaming_token_manager,
    get_default_token_manager,
    load_env_file as real_load_env_file,
    resolve_base_url,
)
from pykada.endpoints import (
    DEFAULT_BASE_URL,
    GET_TOKEN_ENDPOINT,
    V2_STREAMING_TOKEN_ENDPOINT,
    base_url_for_region,
    rebase_url,
)
from pykada.exceptions import VerkadaAuthError


# ---------- regions ----------

@pytest.mark.parametrize("region, expected", [
    ("api", "https://api.verkada.com"),
    ("eu", "https://api.eu.verkada.com"),
    ("AU", "https://api.au.verkada.com"),
    ("api.oh", "https://api.oh.verkada.com"),
])
def test_base_url_for_region(region, expected):
    assert base_url_for_region(region) == expected


def test_base_url_for_unknown_region_raises():
    with pytest.raises(ValueError, match="region"):
        base_url_for_region("mars")


def test_rebase_url_moves_default_host():
    assert rebase_url(f"{DEFAULT_BASE_URL}/v2/cameras", "https://api.eu.verkada.com") \
        == "https://api.eu.verkada.com/v2/cameras"


def test_rebase_url_leaves_other_hosts_alone():
    assert rebase_url("https://example.com/x", "https://api.eu.verkada.com") \
        == "https://example.com/x"
    assert rebase_url(f"{DEFAULT_BASE_URL}/x", DEFAULT_BASE_URL) == f"{DEFAULT_BASE_URL}/x"


def test_resolve_base_url_defaults_to_us():
    assert resolve_base_url() == DEFAULT_BASE_URL


def test_resolve_base_url_precedence(monkeypatch):
    monkeypatch.setenv("VERKADA_REGION", "au")
    assert resolve_base_url() == "https://api.au.verkada.com"
    monkeypatch.setenv("VERKADA_BASE_URL", "https://proxy.test/")
    assert resolve_base_url() == "https://proxy.test"
    assert resolve_base_url(region="eu") == "https://api.eu.verkada.com"
    assert resolve_base_url(base_url="https://other.test") == "https://other.test"


def test_resolve_base_url_rejects_both():
    with pytest.raises(ValueError, match="not both"):
        resolve_base_url(region="eu", base_url="https://x.test")


# ---------- VerkadaTokenManager ----------

def test_token_manager_regional_token_url():
    tm = VerkadaTokenManager(api_key="k", base_url="https://api.eu.verkada.com")
    assert tm._token_url == "https://api.eu.verkada.com/token"
    assert tm.base_url == "https://api.eu.verkada.com"


def test_token_manager_default_base_url():
    tm = VerkadaTokenManager(api_key="k")
    assert tm._token_url == GET_TOKEN_ENDPOINT
    assert tm.base_url == DEFAULT_BASE_URL


def test_token_fetch_has_timeout():
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"token": "t"}
    with patch("pykada.api_tokens.requests.post", return_value=resp) as post:
        assert VerkadaTokenManager(api_key="k").get_token() == "t"
    assert post.call_args.kwargs["timeout"] == api_tokens.TOKEN_TIMEOUT_SECONDS


def test_token_is_cached():
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"token": "t"}
    tm = VerkadaTokenManager(api_key="k")
    with patch("pykada.api_tokens.requests.post", return_value=resp) as post:
        tm.get_token()
        tm.get_token()
    assert post.call_count == 1


def test_token_manager_requires_key():
    with pytest.raises(VerkadaAuthError):
        VerkadaTokenManager(api_key="")


# ---------- default managers ----------

@pytest.fixture
def no_default_managers(monkeypatch):
    monkeypatch.setattr(api_tokens, "default_token_manager", None)
    monkeypatch.setattr(api_tokens, "default_streaming_token_manager", None)
    monkeypatch.delenv("VERKADA_API_KEY", raising=False)


def test_default_manager_built_lazily_from_env(no_default_managers, monkeypatch):
    monkeypatch.setenv("VERKADA_API_KEY", "env-key")
    monkeypatch.setenv("VERKADA_REGION", "eu")
    tm = get_default_token_manager()
    assert tm.api_key == "env-key"
    assert tm._token_url == "https://api.eu.verkada.com/token"
    assert get_default_token_manager() is tm

    stm = get_default_streaming_token_manager()
    assert stm.api_key == "env-key"
    assert stm._token_url == rebase_url(V2_STREAMING_TOKEN_ENDPOINT,
                                        "https://api.eu.verkada.com")


def test_default_manager_without_key_raises(no_default_managers):
    with pytest.raises(VerkadaAuthError, match="VERKADA_API_KEY"):
        get_default_token_manager()
    with pytest.raises(VerkadaAuthError, match="VERKADA_API_KEY"):
        get_default_streaming_token_manager()


# ---------- .env loading ----------

def test_env_file_found_from_cwd_and_does_not_override(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("PYKADA_TEST_A=from-file\nPYKADA_TEST_B=from-file\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PYKADA_TEST_A", "from-shell")
    monkeypatch.delenv("PYKADA_TEST_B", raising=False)
    try:
        real_load_env_file()
        assert api_tokens.os.environ["PYKADA_TEST_A"] == "from-shell"
        assert api_tokens.os.environ["PYKADA_TEST_B"] == "from-file"
    finally:
        monkeypatch.delenv("PYKADA_TEST_B", raising=False)


def test_env_file_missing_is_fine(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch("pykada.api_tokens.find_dotenv", return_value="") as find, \
         patch("pykada.api_tokens.load_dotenv") as load:
        real_load_env_file()
    find.assert_called_once_with(usecwd=True)
    load.assert_not_called()


def test_import_has_no_side_effects(tmp_path):
    # Importing pykada must not read .env, build token managers, or configure
    # logging for the host application.
    (tmp_path / ".env").write_text("VERKADA_API_KEY=from-file\n")
    code = (
        "import logging, os, pykada, pykada.api_tokens as t\n"
        "assert t.default_token_manager is None\n"
        "assert 'VERKADA_API_KEY' not in os.environ\n"
        "assert logging.getLogger().handlers == []\n"
        "assert any(isinstance(h, logging.NullHandler)\n"
        "           for h in logging.getLogger('pykada').handlers)\n"
    )
    env = {k: v for k, v in os.environ.items() if k != "VERKADA_API_KEY"}
    subprocess.run([sys.executable, "-c", code], cwd=tmp_path, env=env, check=True)
