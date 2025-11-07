# Elli API Client

[![PyPI version](https://badge.fury.io/py/elli-api-client.svg)](https://badge.fury.io/py/elli-api-client)
[![Python versions](https://img.shields.io/pypi/pyversions/elli-api-client.svg)](https://pypi.org/project/elli-api-client/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python client library for the Elli Charging API with OAuth2 PKCE authentication.

## Installation

```bash
pip install elli-api-client
```

## Usage

```python
from elli_api_client import ElliAPIClient

# Create client (loads config from .env)
with ElliAPIClient() as client:
    # Login
    token = client.login("your.email@example.com", "your_password")

    # Get stations
    stations = client.get_stations()
    for station in stations:
        print(f"Station: {station.name} ({station.id})")

    # Get charging sessions
    sessions = client.get_charging_sessions(include_momentary_speed=True)
    for session in sessions:
        if session.end_date_time is None:  # Active session
            print(f"Currently charging: {session.accumulated_energy_wh / 1000:.2f} kWh")
            if session.momentary_charging_speed_watts:
                print(f"Power: {session.momentary_charging_speed_watts / 1000:.2f} kW")

    # Get accumulated data for a station
    data = client.get_accumulated_charging(station_id="your-station-id")
    print(f"Total energy: {data['accumulated_energy_wh'] / 1000:.2f} kWh")
```

## Configuration

Configuration is loaded from environment variables (`.env` file):

```env
# Required
ELLI_EMAIL=your.email@example.com
ELLI_PASSWORD=your_password

# Optional OAuth2 settings (defaults work for official Elli app)
ELLI_AUTH_BASE_URL=https://login.elli.eco
ELLI_API_BASE_URL=https://api.elli.eco
ELLI_CLIENT_ID=vFGCyS5GUbctkPk1FfcNH6TrDtyfUCwX
ELLI_REDIRECT_URI=com.elli.ios.emsp://login.elli.eco/ios/com.elli.ios.emsp/callback
ELLI_AUDIENCE=https://api.elli.eco/
ELLI_SCOPE=offline_access openid profile
```

## Models

### TokenResponse
- `access_token: str`
- `refresh_token: str`
- `id_token: str`
- `token_type: str`
- `expires_in: int`
- `scope: str`

### Station
- `id: str`
- `name: str`
- `serial_number: Optional[str]`
- `model: Optional[str]`
- `firmware_version: Optional[str]`

### ChargingSession
- `id: str`
- `station_id: str`
- `user_id: Optional[str]`
- `start_date_time: str`
- `end_date_time: Optional[str]`
- `accumulated_energy_wh: Optional[int]`
- `momentary_charging_speed_watts: Optional[int]`
- `status: Optional[str]`
