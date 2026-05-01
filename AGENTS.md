# AGENTS.md - Pykada Development Guide

## Project Overview

Pykada is a Python library for interacting with Verkada's physical security APIs (cameras, access control, sensors, alarms, workplace). It provides both a **client-based API** (recommended) and a **functional API**.

## Build & Test Commands

- **Run tests**: `pytest` (from project root)
- **Install package**: `pip install -e .`
- **Build package**: `pip install build` then `python -m build`
- **Python version**: Requires Python 3.10+

## Architecture

### Client Pattern
Each Verkada product line has its own client class inheriting from `BaseClient`:
- `CamerasClient` → cameras
- `AccessControlClient` → access control
- `SensorsClient` → environmental sensors
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
Clients accept either an `api_key` directly or a `token_manager`. If no key is provided, they look for `VERKADA_API_KEY` in a `.env` file.

## Conventions

### Type Safety
The project uses **typeguard** for runtime type checking. All public methods use `@typechecked` decorator. Tests verify type errors using `pytest.raises(TypeCheckError)`.

### Client Implementation Pattern
```python
class SomeClient(BaseClient):
    def __init__(self,
                 api_key: Optional[str] = None,
                 token_manager: Optional[VerkadaTokenManager] = None):
        super().__init__(api_key, token_manager)
    
    @typechecked
    def some_method(self, param: Optional[str] = None) -> dict:
        # Implementation
        return self._request_manager.get(...)
```

### Testing
- Tests are in `*_tests/` directories alongside the modules they test
- Test files follow naming: `test_<module>.py`
- Testbeds (mock data) are in `testbed/` subdirectories
- Use `@patch` decorators for mocking HTTP requests
- Test type errors using `pytest.raises(TypeCheckError)`

## Potential Pitfalls

1. **Token refresh**: The library automatically refreshes short-lived tokens. Don't manually handle tokens unless needed.
2. **typeguard**: Adding new parameters requires proper type annotations or tests will fail.
3. **API key**: Without a valid API key or `.env` file, clients will raise exceptions.
4. **Python version**: Requires Python 3.10+

## Key Files for Reference

- [cameras.py](pykada/cameras.py) - Example client implementation
- [verkada_client.py](pykada/verkada_client.py) - Base client class
- [cameras_tests/test_cameras.py](pykada/cameras_tests/test_cameras.py) - Test patterns
- [access_control_tests/test_access_doors.py](pykada/access_control_tests/test_access_doors.py) - More test examples