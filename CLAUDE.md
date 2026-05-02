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

`docs/_build/` is gitignored. To deploy, copy `docs/_build/html/` to your static host.

## Architecture

Pykada is a Python SDK wrapper for the [Verkada API](https://apidocs.verkada.com) — a cloud physical security platform with cameras, access control, sensors, alarms, workplace (guest/mailroom), intercoms, and gateways.

### Core Infrastructure

- **[pykada/verkada_requests.py](pykada/verkada_requests.py)** — `VerkadaRequestManager`: central HTTP client with retry/backoff logic (retries on 429/5xx), token injection, and a `iterate_paginated_results()` generator for paginated API responses.
- **[pykada/api_tokens.py](pykada/api_tokens.py)** — `VerkadaTokenManager`: manages 30-min token lifecycle; auto-refreshes with a 25-min safety buffer. Reads `VERKADA_API_KEY` from `.env` by default.
- **[pykada/verkada_client.py](pykada/verkada_client.py)** — `BaseClient`: abstract base all product clients inherit from. Initializes a shared `VerkadaTokenManager` and `VerkadaRequestManager`.
- **[pykada/endpoints.py](pykada/endpoints.py)** — all API endpoint URL constants.
- **[pykada/enums.py](pykada/enums.py)** — valid enum values for API parameters.
- **[pykada/helpers.py](pykada/helpers.py)** — `remove_null_fields()`, CSV/date/string validators.

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

Tests live in `*_tests/` directories alongside each module (e.g., `cameras_tests/test_cameras.py`).

### Key Patterns

**Client method pattern** — every public method on a client follows this structure:
1. Decorate with `@typechecked` for runtime type enforcement.
2. Build a params/body dict, then call `remove_null_fields()` to strip `None` values.
3. Delegate to `self.request_manager.get/post/put/patch/delete(ENDPOINT, ...)`.
4. Return `dict` (raw JSON response).

**Authentication** — clients accept an optional `api_key` argument; if omitted, `VerkadaTokenManager` falls back to `VERKADA_API_KEY` in a `.env` file.

**Pagination** — use `VerkadaRequestManager.iterate_paginated_results()` (a generator) when consuming endpoints that page results.

**Validation helpers** — prefer `require_non_empty_str()`, `check_user_external_id()`, `verify_csv_columns()` from `helpers.py` over ad-hoc checks.

**Error conventions** — raise `ValueError` for invalid input; raise typed exceptions from `pykada/exceptions.py` (`VerkadaAuthError`, `VerkadaRateLimitError`, etc.) for API/token failures. All exceptions inherit from `VerkadaError`.

**Testing pattern** — tests mock HTTP calls with `unittest.mock.patch`, assert return types are `dict`, and use `pytest.raises(TypeCheckError)` to verify `@typechecked` enforcement.
