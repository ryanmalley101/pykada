"""Pykada - A Python client for the Verkada API."""

__version__ = "1.0.2"

from pykada.cameras import CamerasClient
from pykada.access_control import AccessControlClient
from pykada.sensors import SensorsClient
from pykada.classic_alarms import ClassicAlarmsClient
from pykada.core_command import CoreCommandClient
from pykada.helix import HelixClient
from pykada.workplace import WorkplaceClient
from pykada.camera_stream import StreamingClient
from pykada.exceptions import (
    VerkadaError,
    VerkadaAuthError,
    VerkadaForbiddenError,
    VerkadaNotFoundError,
    VerkadaRateLimitError,
    VerkadaServerError,
    VerkadaAPIError,
)

__all__ = [
    # Clients
    "CamerasClient",
    "AccessControlClient",
    "SensorsClient",
    "ClassicAlarmsClient",
    "CoreCommandClient",
    "HelixClient",
    "WorkplaceClient",
    "StreamingClient",
    # Exceptions
    "VerkadaError",
    "VerkadaAuthError",
    "VerkadaForbiddenError",
    "VerkadaNotFoundError",
    "VerkadaRateLimitError",
    "VerkadaServerError",
    "VerkadaAPIError",
]