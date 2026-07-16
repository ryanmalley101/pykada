# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install in development mode
pip install -e .

# Run all tests
pytest

# Run a specific test file
pytest pykada/cameras_tests/test_cameras.py

# Run a single test
pytest pykada/cameras_tests/test_cameras.py::test_type_errors

# Build distribution
python -m build
```

No linting config is present. Runtime type enforcement is handled by `@typechecked` decorators (via `typeguard`), not a static linter.

```bash
# Install with docs dependencies
pip install -e ".[docs]"

# Build HTML docs
sphinx-build -b html docs/ docs/_build/html

# Serve docs locally (open in browser)
python -m http.server -d docs/_build/html
```

`docs/_build/` is gitignored — deploying it locally is only for previewing. In CI, `.github/workflows/deploy-docs.yml` rebuilds the docs and pushes `docs/_build/html/` to the `rmalleydotcom` site repo on every push to `master` that touches `pykada/**` or `docs/**`. No manual deploy step needed.

## Releasing to PyPI

Version is single-sourced from `__version__` in [pykada/__init__.py](pykada/__init__.py) — `pyproject.toml` reads it dynamically (`dynamic = ["version"]` + `[tool.hatch.version] path = "pykada/__init__.py"`). Do not hardcode a version in `pyproject.toml`; edit only `__init__.py`.

To cut a release: bump `__version__` in `pykada/__init__.py` and push to `master`. `.github/workflows/auto-release.yml` diffs the version against existing git tags on every push to `master`; if it's new, it builds, publishes to PyPI via trusted publishing (no stored token — `pypa/gh-action-pypi-publish` + the `pypi` environment's OIDC trust configured on PyPI's side), then tags `vX.Y.Z` and creates a matching GitHub Release. A push that doesn't change the version is a no-op — no build, no publish. `.github/workflows/python-publish.yml` holds the actual build/publish steps as a reusable (`workflow_call`) workflow that `auto-release.yml` invokes; it's also still directly usable by manually publishing a GitHub Release if you ever need to force a rebuild without a version bump.

## Architecture

Pykada is a Python SDK wrapper for the [Verkada API](https://apidocs.verkada.com) — a cloud physical security platform with cameras, access control, sensors, alarms, workplace (guest/mailroom), intercoms, and gateways. It is an independent, unofficial project (not affiliated with Verkada Inc.).

### Core Infrastructure

- **[pykada/verkada_requests.py](pykada/verkada_requests.py)** — `VerkadaRequestManager`: central HTTP client with retry/backoff logic (retries on 429/5xx via a `urllib3.Retry`-backed `requests.Session`), token injection, `_raise_for_status()` mapping HTTP status codes to typed exceptions, and an `iterate_paginated_results()` generator for paginated API responses.
- **[pykada/api_tokens.py](pykada/api_tokens.py)** — `VerkadaTokenManager`: manages 30-min token lifecycle; auto-refreshes with a 25-min safety buffer. Reads `VERKADA_API_KEY` from `.env` by default.
- **[pykada/verkada_client.py](pykada/verkada_client.py)** — `BaseClient`: abstract base all product clients inherit from. Initializes a shared `VerkadaTokenManager` and `VerkadaRequestManager`.
- **[pykada/endpoints.py](pykada/endpoints.py)** — all API endpoint URL constants.
- **[pykada/enums.py](pykada/enums.py)** — valid enum values for API parameters.
- **[pykada/helpers.py](pykada/helpers.py)** — `remove_null_fields()`, CSV/date/string validators.
- **[pykada/exceptions.py](pykada/exceptions.py)** — `VerkadaError` base class plus `VerkadaAuthError` (401), `VerkadaForbiddenError` (403), `VerkadaNotFoundError` (404), `VerkadaRateLimitError` (429, carries `retry_after`), `VerkadaServerError` (5xx), `VerkadaAPIError` (fallback). All carry `status_code`, `response_body`, `endpoint`.
- **[pykada/__init__.py](pykada/__init__.py)** — re-exports every client and exception at the top level (e.g. `from pykada import CamerasClient, VerkadaAuthError`).

### Product Clients

Each product area is a client class that extends `BaseClient`:

| File | Client |
|---|---|
| `cameras.py` | `CamerasClient` |
| `access_control.py` | `AccessControlClient` |
| `sensors.py` | `SensorsClient` |
| `classic_alarms.py` | `ClassicAlarmsClient` |
| `core_command.py` | `CoreCommandClient` |
| `helix.py` | `HelixClient` |
| `workplace.py` | `WorkplaceClient` |
| `camera_stream.py` | `StreamingClient` — constructs signed HLS (`.m3u8`) URLs locally rather than calling `request_manager.get/post/...`; requires a dedicated Streaming API key. |

Each client file's `docs/api/*.rst` counterpart (Sphinx autodoc) mirrors it 1:1.

Test directory naming is **not consistent** across modules — check before assuming a pattern:
- `cameras_tests/`, `access_control_tests/` — suffixed `<module>_tests/` directories.
- `sensors/`, `classic_alarms/`, `helix/`, `core_command/`, `workplace/` — plain directories that happen to share the module's basename (co-located with `sensors.py`, `classic_alarms.py`, etc.), not Python packages (no `__init__.py`).

Both hold `test_<module>.py` and a `testbed/` subdirectory of mock fixtures/scripts.

### Two calling conventions

Every product module exposes the same operations twice — pick per call site:

1. **OOP (recommended for multiple calls)** — instantiate `CamerasClient(api_key=...)` and call methods on it; the token and HTTP session are reused across calls.
2. **Functional (convenience for one-off scripts)** — module-level functions with the same name/signature as the client method (e.g. `pykada.cameras.get_camera_data()`). Each lazily creates and caches a module-level singleton client via a `_get_default_client()` helper (backed by a `_default_<module>_client` global) and delegates to it. The API key must come from `VERKADA_API_KEY` in `.env` since there's no client object to pass a key to.

When adding a new client method, add both: the method on the class, and a thin wrapper function at the bottom of the module that calls `_get_default_client().<method>(...)`, documented with a docstring note that it's a functional wrapper.

### Key Patterns

**Client method pattern** — every public method on a client follows this structure:
1. Decorate with `@typechecked` for runtime type enforcement.
2. Build a params/body dict, then call `remove_null_fields()` to strip `None` values.
3. Delegate to `self.request_manager.get/post/put/patch/delete(ENDPOINT, ...)`.
4. Return `dict` (raw JSON response).

**Authentication** — clients accept an optional `api_key` argument; if omitted, `VerkadaTokenManager` falls back to `VERKADA_API_KEY` in a `.env` file.

**Pagination** — use `VerkadaRequestManager.iterate_paginated_results()` (a generator) when consuming endpoints that page results.

**Validation helpers** — prefer `require_non_empty_str()`, `check_user_external_id()`, `verify_csv_columns()` from `helpers.py` over ad-hoc checks.

**Error conventions** — raise `ValueError` for invalid input; raise typed exceptions from `pykada/exceptions.py` for API/token failures (see status-code mapping above), via `_raise_for_status()` in `verkada_requests.py`.

**Testing pattern** — tests mock HTTP calls with `unittest.mock.patch`, assert return types are `dict`, and use `pytest.raises(TypeCheckError)` to verify `@typechecked` enforcement. [pykada/conftest.py](pykada/conftest.py) has a root-level `autouse` fixture that patches `pykada.api_tokens.default_token_manager` with a mock (so no real `VERKADA_API_KEY` is needed) and resets every module's `_default_<module>_client` singleton to `None` before and after each test — required because the functional API's singleton would otherwise leak a stale/mocked client across tests.
