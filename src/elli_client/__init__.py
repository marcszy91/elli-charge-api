"""Elli Client - Python client for Elli Wallbox API"""

from .client import ElliAPIClient
from .exceptions import (
    AuthenticationError,
    ElliClientError,
    InvalidOAuthCallback,
    InvalidOAuthState,
    ReauthenticationRequired,
    TokenExchangeError,
    TokenRefreshError,
)
from .models import (
    AuthorizationSession,
    ChargingRecord,
    ChargingRecordsResponse,
    ChargingSession,
    FirmwareInfo,
    Location,
    RFIDCard,
    Station,
    TokenResponse,
)

__version__ = "1.5.0"

__all__ = [
    "AuthenticationError",
    "AuthorizationSession",
    "ChargingRecord",
    "ChargingRecordsResponse",
    "ChargingSession",
    "ElliAPIClient",
    "ElliClientError",
    "FirmwareInfo",
    "InvalidOAuthCallback",
    "InvalidOAuthState",
    "Location",
    "ReauthenticationRequired",
    "RFIDCard",
    "Station",
    "TokenExchangeError",
    "TokenRefreshError",
    "TokenResponse",
]
