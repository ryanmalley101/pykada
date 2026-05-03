import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def mock_auth_and_reset_singletons():
    """
    Provides a mock token manager so clients can be instantiated without a
    real VERKADA_API_KEY, and resets all module-level client singletons so
    each test starts with a fresh (lazily re-created) client.
    """
    import pykada.cameras
    import pykada.sensors
    import pykada.access_control
    import pykada.core_command
    import pykada.helix
    import pykada.workplace
    import pykada.classic_alarms

    def _reset():
        pykada.cameras._default_cameras_client = None
        pykada.sensors._default_sensors_client = None
        pykada.access_control._default_ac_client = None
        pykada.core_command._default_core_client = None
        pykada.helix._default_helix_client = None
        pykada.workplace._default_workplace_client = None
        pykada.classic_alarms._default_alarms_client = None

    _reset()

    mock_tm = MagicMock()
    mock_tm.get_token.return_value = "test-token-12345"

    with patch("pykada.api_tokens.default_token_manager", mock_tm):
        yield

    _reset()
