# AGENTS.md - Pykada Development Guide

## Project Overview

Pykada is a Python library for interacting with Verkada's physical security APIs (cameras, access control, events, sensors, alarms, workplace). Since 2.0 it targets Verkada API v2; `specs/openapi.json` is the reference spec. See CLAUDE.md for the full v2 method conventions. It provides both a **client-based API** (recommended) and a **functional API**.

## Build & Test Commands

- **Run tests**: `pytest` (from project root)
- **Install package**: `pip install -e .`
- **Build package**: `pip install build` then `python -m build`
- **Python version**: Requires Python 3.10+

## Architecture

### Client Pattern
Each Verkada product line has its own client class inheriting from `BaseClient`:
- `CamerasClient` → cameras
- `StreamingClient` → HLS footage streaming URLs
- `AccessControlClient` → access control
- `EventsClient` → unified camera/access/sensor/intercom event feed
- `SensorsClient` → environmental sensors
- `CoreCommandClient` → users and audit logs
- `HelixClient` → Helix video tagging
- `ClassicAlarmsClient` → alarms
- `WorkplaceClient` → guest/mailroom

### Key Components
- **[verkada_client.py](pykada/verkada_client.py)**: `BaseClient` - base class for all clients
- **[verkada_requests.py](pykada/verkada_requests.py)**: `VerkadaRequestManager` - handles HTTP requests, retries, token management
- **[api_tokens.py](pykada/api_tokens.py)**: `VerkadaTokenManager` - manages API token refresh
- **[endpoints.py](pykada/endpoints.py)**: API endpoint constants
- **[enums.py](pykada/enums.py)**: Valid enum values for API parameters
- **[helpers.py](pykada/helpers.py)**: Utility functions (remove_null_fields, verify_csv_columns, etc.)

### Authentication
Clients accept either an `api_key` directly or a `token_manager`. If no key is provided, they look for `VERKADA_API_KEY` in the environment, then in a `.env` file found from the current working directory (loaded lazily, never overriding variables already set). `region=`/`base_url=` (or `VERKADA_REGION`/`VERKADA_BASE_URL`) select a non-US API host.

## Conventions

### Type Safety
The project uses **typeguard** for runtime type checking. All public methods use `@typechecked` decorator. Tests verify type errors using `pytest.raises(TypeCheckError)`.

### Client Implementation Pattern
```python
class SomeClient(BaseClient):
    def __init__(self,
                 api_key: Optional[str] = None,
                 token_manager: Optional[VerkadaTokenManager] = None,
                 request_manager: Optional[VerkadaRequestManager] = None,
                 api_version: Optional[str] = None):
        super().__init__(api_key, token_manager, request_manager, api_version)

    @typechecked
    def get_things(self, start_time: Optional[Timestamp] = None,
                   limit: Optional[int] = None,
                   cursor: Optional[str] = None) -> Dict[str, Any]:
        check_limit(limit, 200)
        params = remove_null_fields({"start_time": to_iso8601(start_time, "start_time"),
                                     "limit": limit, "cursor": cursor})
        return self.request_manager.get(V2_THINGS_ENDPOINT, params=params)

    @typechecked
    def get_all_things(self, start_time: Optional[Timestamp] = None):
        return VerkadaRequestManager.iterate_cursor_results(
            lambda **kwargs: self.get_things(**kwargs),
            initial_params={"start_time": start_time})
```

### Testing
- Tests are in `*_tests/` directories (or plain `<module>/` directories) alongside the modules they test
- Test files follow naming: `test_<module>.py`
- Testbeds in `testbed/` subdirectories are live smoke scripts that call the real API
- Use `@patch` decorators for mocking HTTP requests, and assert the exact URL/params/payload
- Test type errors using `pytest.raises(TypeCheckError)`

## Potential Pitfalls

1. **Token refresh**: The library automatically refreshes short-lived tokens. Don't manually handle tokens unless needed.
2. **typeguard**: Adding new parameters requires proper type annotations or tests will fail.
3. **API key**: Without a valid API key or `.env` file, clients will raise exceptions.
4. **Python version**: Requires Python 3.10+
5. **Timestamps**: public methods take timezone-aware `datetime` or ISO 8601 strings, never epoch ints (Helix `time_ms` is the one v1 exception).

## Key Files for Reference

- [cameras.py](pykada/cameras.py) - Example client implementation
- [verkada_client.py](pykada/verkada_client.py) - Base client class
- [cameras_tests/test_cameras.py](pykada/cameras_tests/test_cameras.py) - Test patterns
- [access_control_tests/test_access_doors.py](pykada/access_control_tests/test_access_doors.py) - More test examples