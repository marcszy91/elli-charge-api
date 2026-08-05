# API Documentation

Complete reference for the Elli Client API.

## Table of Contents

- [Authentication](#authentication)
- [Stations](#stations)
- [Charging Sessions](#charging-sessions)
- [Firmware](#firmware)
- [Statistics](#statistics)

---

## Authentication

### `create_authorization()`

Create a cryptographically secure PKCE authorization session without making a network request.

**Returns:** `AuthorizationSession` containing `authorization_url`, `state`, `code_verifier`, and timezone-aware `created_at`.

The calling application must open `authorization_url` in a normal browser and retain the complete session object. Elli Client does not open browsers or receive callbacks itself.

### `exchange_callback(callback_url, authorization)`

Validate the custom-scheme callback's scheme, host, path, OAuth error, and state, then exchange its authorization code with the session's PKCE verifier.

**Returns:** `TokenResponse`. This method does not modify client state; pass its result to `set_tokens()`.

**Raises:**
- `InvalidOAuthCallback`: Callback URI, error response, or authorization code is invalid
- `InvalidOAuthState`: State is missing or does not match
- `TokenExchangeError`: Token endpoint request or response failed

### `refresh(refresh_token)`

Obtain a new access token. If Auth0 rotates the refresh token, the returned model contains the replacement. If no replacement is returned, the input refresh token is preserved in the model.

**Raises:** `ReauthenticationRequired` for `invalid_grant`; `TokenRefreshError` for other failures.

### `set_tokens(tokens)` / `set_access_token(access_token)`

Set credentials used by subsequent API requests. Tokens are held in memory only and are never persisted by the library.

**Example:**
```python
from elli_client import ElliAPIClient

client = ElliAPIClient()
authorization = client.create_authorization()
print(authorization.authorization_url)
callback_url = receive_callback()
tokens = client.exchange_callback(callback_url, authorization)
client.set_tokens(tokens)
```

### Deprecated `login(email, password)`

Retained temporarily for compatibility. It emits `DeprecationWarning` and is unreliable because Cloudflare Turnstile requires interactive browser authentication. It will not bypass or automate the CAPTCHA.

---

## Stations

### `get_stations()`

Get all charging stations associated with your account.

**Parameters:** None

**Returns:**
- `list[Station]`: List of Station objects

**Station Attributes:**
- `id` (str): Unique station identifier
- `name` (str): Station name
- `serial_number` (str): Hardware serial number
- `model` (str): Station model (e.g., "Elli Wallbox Pro")
- `firmware_version` (str): Current firmware version
- `installed_firmware` (FirmwareInfo): Detailed firmware information

**Raises:**
- `ValueError`: If not authenticated or request fails

**Example:**
```python
stations = client.get_stations()
for station in stations:
    print(f"Station: {station.name}")
    print(f"  ID: {station.id}")
    print(f"  Model: {station.model}")
    print(f"  Firmware: {station.firmware_version}")
```

---

## Charging Sessions

### `get_charging_sessions(include_momentary_speed=True)`

Get all charging sessions (active and historical).

**Parameters:**
- `include_momentary_speed` (bool, optional): Include current charging power in watts. Default: True

**Returns:**
- `list[ChargingSession]`: List of ChargingSession objects

**ChargingSession Attributes:**
- `id` (str): Unique session identifier
- `station_id` (str): Associated station ID
- `start_date_time` (str): Session start timestamp (ISO 8601)
- `end_date_time` (str, optional): Session end timestamp
- `energy_consumption_wh` (int): Energy consumed in watt-hours
- `momentary_charging_speed_watts` (int, optional): Current charging power in watts
- `lifecycle_state` (str): Session state (e.g., "ACTIVE", "COMPLETED")
- `charging_state` (str): Charging state (e.g., "CHARGING", "IDLE")
- `rfid_card_id` (str, optional): RFID card identifier
- `rfid_card_serial_number` (str, optional): RFID card serial number
- `authentication_method` (str): How the session was authenticated
- `connector_id` (int): Connector number used

**Raises:**
- `ValueError`: If not authenticated or request fails

**Example:**
```python
# Get all sessions with power data
sessions = client.get_charging_sessions()

# Find active session
active = [s for s in sessions if s.lifecycle_state == "ACTIVE"]
if active:
    session = active[0]
    print(f"Currently charging: {session.energy_consumption_wh / 1000:.2f} kWh")
    print(f"Power: {session.momentary_charging_speed_watts} W")

# Get sessions without power data (faster)
sessions = client.get_charging_sessions(include_momentary_speed=False)
```

---

## Firmware

### `get_firmware_info()`

Get firmware information for all stations.

**Parameters:** None

**Returns:**
- `list[Station]`: List of Station objects with firmware details

**Raises:**
- `ValueError`: If not authenticated or request fails

**Example:**
```python
stations = client.get_firmware_info()
for station in stations:
    if station.installed_firmware:
        print(f"{station.name}:")
        print(f"  Version: {station.installed_firmware.version}")
        if station.installed_firmware.release_notes_link:
            print(f"  Release Notes: {station.installed_firmware.release_notes_link}")
```

---

## Statistics

### `get_accumulated_charging(station_id)`

Get accumulated charging statistics for a specific station.

**Parameters:**
- `station_id` (str): The ID of the charging station

**Returns:**
- `dict`: Dictionary containing accumulated statistics:
  - Total energy charged (kWh)
  - Total number of sessions
  - Time-based statistics

**Raises:**
- `ValueError`: If not authenticated or request fails

**Example:**
```python
# First, get your station ID
stations = client.get_stations()
station_id = stations[0].id

# Get accumulated statistics
stats = client.get_accumulated_charging(station_id)
print(f"Total sessions: {stats.get('total_sessions', 'N/A')}")
print(f"Total energy: {stats.get('total_energy_kwh', 'N/A')} kWh")
```

---

## Advanced Usage

### Using Context Manager

The client supports Python's context manager protocol for automatic cleanup:

```python
from elli_client import ElliAPIClient

with ElliAPIClient() as client:
    client.set_tokens(tokens)
    stations = client.get_stations()
    # Client automatically closes when exiting the 'with' block
```

### Manual Cleanup

If not using a context manager, remember to close the client:

```python
client = ElliAPIClient()
try:
    client.set_tokens(tokens)
    stations = client.get_stations()
finally:
    client.close()
```

### Custom Configuration

You can customize the API endpoints and OAuth2 configuration:

```python
client = ElliAPIClient(
    auth_base_url="https://custom-auth.example.com",
    api_base_url="https://custom-api.example.com",
    client_id="custom_client_id",
    # ... other OAuth2 parameters
)
```

**Note:** The default configuration works with the official Elli API and should not need to be changed for normal usage.

---

## Error Handling

Authentication methods use the exported `ElliClientError` hierarchy. Existing data API methods continue to raise `ValueError` on request failures for compatibility.

```python
from elli_client import ElliAPIClient, ElliClientError

client = ElliAPIClient()

try:
    tokens = client.refresh(stored_refresh_token)
    client.set_tokens(tokens)
    stations = client.get_stations()
except ElliClientError as e:
    print(f"Error: {e}")
```

---

## Data Models

### TokenResponse

```python
class TokenResponse:
    access_token: str       # JWT access token
    refresh_token: Optional[str]
    id_token: Optional[str]
    token_type: Optional[str]
    expires_in: Optional[int]
    scope: Optional[str]
    expires_at: Optional[datetime]  # Calculated UTC expiry
```

Token fields are excluded from the model representation to reduce accidental disclosure. The caller remains responsible for treating the model as sensitive data.

### Station

```python
class Station:
    id: str                              # Unique identifier
    name: str                            # Station name
    serial_number: Optional[str]         # Hardware serial
    model: Optional[str]                 # Model name
    firmware_version: Optional[str]      # Current firmware
    installed_firmware: Optional[FirmwareInfo]  # Firmware details
```

### ChargingSession

```python
class ChargingSession:
    id: str                              # Session ID
    station_id: str                      # Station ID
    start_date_time: str                 # Start time (ISO 8601)
    end_date_time: Optional[str]         # End time
    energy_consumption_wh: Optional[int] # Energy in Wh
    momentary_charging_speed_watts: Optional[int]  # Power in W
    lifecycle_state: Optional[str]       # Session state
    charging_state: Optional[str]        # Charging state
    rfid_card_id: Optional[str]         # RFID card ID
    rfid_card_serial_number: Optional[str]  # RFID serial
    authentication_method: Optional[str] # Auth method
    connector_id: Optional[int]         # Connector number
```

### FirmwareInfo

```python
class FirmwareInfo:
    id: str                          # Firmware ID
    version: str                     # Version string
    release_notes_link: Optional[str]  # URL to release notes
```
