"""Elli API Client with OAuth2 PKCE Authentication"""

import base64
import hashlib
import re
import secrets
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urljoin, urlparse

import httpx

from .config import settings
from .models import ChargingSession, RFIDCard, Station, TokenResponse


class ElliAPIClient:
    """Client for Elli Charging API with OAuth2 PKCE authentication"""

    # Default OAuth2 configuration (from official Elli iOS app)
    DEFAULT_AUTH_BASE_URL = "https://login.elli.eco"
    DEFAULT_API_BASE_URL = "https://api.elli.eco"
    DEFAULT_CLIENT_ID = "vFGCyS5GUbctkPk1FfcNH6TrDtyfUCwX"
    DEFAULT_REDIRECT_URI = "com.elli.ios.emsp://login.elli.eco/ios/com.elli.ios.emsp/callback"
    DEFAULT_AUDIENCE = "https://api.elli.eco/"
    DEFAULT_SCOPE = "offline_access openid profile"

    def __init__(
        self,
        auth_base_url: Optional[str] = None,
        api_base_url: Optional[str] = None,
        client_id: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        audience: Optional[str] = None,
        scope: Optional[str] = None,
    ):
        """
        Initialize Elli API Client.

        Args:
            auth_base_url: OAuth2 authorization server URL (default: from env or DEFAULT_AUTH_BASE_URL)
            api_base_url: Elli API base URL (default: from env or DEFAULT_API_BASE_URL)
            client_id: OAuth2 client ID (default: from env or DEFAULT_CLIENT_ID)
            redirect_uri: OAuth2 redirect URI (default: from env or DEFAULT_REDIRECT_URI)
            audience: OAuth2 audience (default: from env or DEFAULT_AUDIENCE)
            scope: OAuth2 scope (default: from env or DEFAULT_SCOPE)
        """
        self.client = httpx.Client(timeout=30.0)
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

        # Load config: parameter > environment > default
        self.auth_base_url = auth_base_url or settings.elli_auth_base_url or self.DEFAULT_AUTH_BASE_URL
        self.api_base_url = api_base_url or settings.elli_api_base_url or self.DEFAULT_API_BASE_URL
        self.client_id = client_id or settings.elli_client_id or self.DEFAULT_CLIENT_ID
        self.redirect_uri = redirect_uri or settings.elli_redirect_uri or self.DEFAULT_REDIRECT_URI
        self.audience = audience or settings.elli_audience or self.DEFAULT_AUDIENCE
        self.scope = scope or settings.elli_scope or self.DEFAULT_SCOPE

    def _generate_pkce_pair(self) -> tuple[str, str]:
        """Generate PKCE code verifier and code challenge"""
        # Generate code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")

        # Generate code challenge (SHA256 hash of verifier)
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode("utf-8")).digest()).decode("utf-8").rstrip("=")
        )

        return code_verifier, code_challenge

    def _generate_state(self) -> str:
        """Generate random state parameter for OAuth2"""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")

    def login(self, email: str, password: str) -> TokenResponse:
        """
        Login to Elli API using username/password with OAuth2 PKCE flow.

        Args:
            email: Elli account email
            password: Elli account password

        Returns:
            TokenResponse with access_token, refresh_token, etc.

        Raises:
            ValueError: If login fails or authorization code cannot be extracted
        """
        # Generate PKCE parameters
        code_verifier, code_challenge = self._generate_pkce_pair()
        state = self._generate_state()

        # Step 1: Initiate authorization with PKCE
        authorize_params = {
            "client_id": self.client_id,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "audience": self.audience,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "response_type": "code",
            "state": state,
            "prompt": "login",
            "connection_scope": "openid profile",
            "ui_locales": "de",
        }

        # Get login page to obtain state and cookies
        auth_response = self.client.get(
            f"{self.auth_base_url}/authorize", params=authorize_params, follow_redirects=True
        )

        # Extract state from the redirected URL
        auth_state = state
        if "state=" in str(auth_response.url):
            parsed = urlparse(str(auth_response.url))
            query_params = parse_qs(parsed.query)
            if "state" in query_params:
                auth_state = query_params["state"][0]

        # Step 2: Submit login credentials
        login_data = {"username": email, "password": password, "action": "default"}

        # The actual login endpoint with state
        login_url = f"{self.auth_base_url}/u/login"
        login_params = {"state": auth_state, "ui_locales": "de"}

        login_response = self.client.post(
            login_url,
            params=login_params,
            data=login_data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": self.auth_base_url,
            },
            follow_redirects=False,
        )

        # Step 3: Follow redirect chain to get authorization code
        max_redirects = 10
        redirect_count = 0
        current_response = login_response
        auth_code = None

        while redirect_count < max_redirects:
            if current_response.status_code not in [302, 303, 307, 308]:
                break

            location = current_response.headers.get("Location", "")
            if not location:
                break

            # Make location absolute if it's relative
            if location.startswith("/"):
                location = urljoin(self.auth_base_url, location)

            # Check if we have the authorization code
            if "code=" in location:
                code_match = re.search(r"code=([^&]+)", location)
                if code_match:
                    auth_code = code_match.group(1)
                    break

            # Follow the redirect
            current_response = self.client.get(
                location, follow_redirects=False, headers={"Referer": self.auth_base_url}
            )
            redirect_count += 1

        if not auth_code:
            # Check final response
            if current_response.status_code == 200:
                # Look for code in the response body or URL
                code_match = re.search(r'code=([^&\'"]+)', str(current_response.text))
                if code_match:
                    auth_code = code_match.group(1)

        if not auth_code:
            raise ValueError(
                f"Could not extract authorization code. Last status: {current_response.status_code}, "
                f"Last URL: {current_response.url}"
            )

        # Step 4: Exchange authorization code for tokens
        token_data = {
            "code": auth_code,
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        }

        token_response = self.client.post(
            f"{self.auth_base_url}/oauth/token",
            json=token_data,
            headers={
                "Content-Type": "application/json",
            },
        )

        if token_response.status_code != 200:
            raise ValueError(f"Token exchange failed: {token_response.status_code} - {token_response.text}")

        token_data_response = token_response.json()
        token = TokenResponse(**token_data_response)

        # Store tokens
        self.access_token = token.access_token
        self.refresh_token = token.refresh_token

        return token

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        if not self.access_token:
            raise ValueError("Not authenticated. Call login() first.")

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Elli-Charging-Prod/10221",
            "platform": "iOS",
        }

    def get_charging_sessions(self, include_momentary_speed: bool = True) -> list[ChargingSession]:
        """
        Get all charging sessions.

        Args:
            include_momentary_speed: Include momentary charging power in watts (default: True)

        Returns:
            List of ChargingSession objects containing session data including:
            - Session ID, station ID, status
            - Start/end times
            - Energy consumption in Wh
            - Momentary power in W (if include_momentary_speed=True)
            - RFID card information

        Raises:
            ValueError: If not authenticated or API request fails
        """
        params = {}
        if include_momentary_speed:
            params["include_momentary_charging_speed_watts"] = "true"

        response = self.client.get(
            f"{self.api_base_url}/chargeathome/v1/charging-sessions", headers=self._get_headers(), params=params
        )

        if response.status_code != 200:
            raise ValueError(f"Failed to get charging sessions: {response.status_code} - {response.text}")

        data = response.json()
        sessions = []
        for session_data in data.get("charging_sessions", []):
            sessions.append(ChargingSession(**session_data))

        return sessions

    def get_stations(self) -> list[Station]:
        """
        Get all charging stations associated with the account.

        Returns:
            List of Station objects containing:
            - Station ID, name, serial number
            - Model information
            - Firmware version
            - Status (e.g., IDLE, CONNECTED, CHARGING)

        Raises:
            ValueError: If not authenticated or API request fails
        """
        response = self.client.get(f"{self.api_base_url}/chargeathome/v1/stations", headers=self._get_headers())

        if response.status_code != 200:
            raise ValueError(f"Failed to get stations: {response.status_code} - {response.text}")

        data = response.json()
        stations = []
        for station_data in data.get("stations", []):
            stations.append(Station(**station_data))

        return stations

    def get_firmware_info(self) -> list[Station]:
        """
        Get firmware information for all stations.

        Returns:
            List of Station objects with firmware details including:
            - Current firmware version
            - Available updates (if any)

        Raises:
            ValueError: If not authenticated or API request fails
        """
        response = self.client.get(f"{self.api_base_url}/chargeathome/v1/firmware/updates", headers=self._get_headers())

        if response.status_code != 200:
            raise ValueError(f"Failed to get firmware info: {response.status_code} - {response.text}")

        data = response.json()
        stations = []
        for station_data in data.get("stations", []):
            stations.append(Station(**station_data))

        return stations

    def get_accumulated_charging(self, station_id: str) -> Dict[str, Any]:
        """
        Get accumulated charging statistics for a specific station.

        Args:
            station_id: The ID of the charging station

        Returns:
            Dictionary containing accumulated statistics:
            - Total energy charged (kWh)
            - Total number of sessions
            - Time-based statistics

        Raises:
            ValueError: If not authenticated or API request fails
        """
        response = self.client.get(
            f"{self.api_base_url}/chargeathome/v1/charging-sessions/accumulated",
            headers=self._get_headers(),
            params={"station_id": station_id},
        )

        if response.status_code != 200:
            raise ValueError(f"Failed to get accumulated charging: {response.status_code} - {response.text}")

        return response.json()

    def get_charging_records(
        self,
        station_id: str,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        sort: str = "created_at",
    ) -> list["ChargingRecord"]:
        """
        Get historical charging records for a specific station.

        This returns completed/historical charging sessions, unlike get_charging_sessions()
        which only returns active/ongoing sessions.

        Args:
            station_id: The ID of the charging station
            created_after: Filter records created after this timestamp (ISO 8601, e.g., "2026-05-31T22:00:00Z")
            created_before: Filter records created before this timestamp (ISO 8601, e.g., "2026-06-30T21:59:00Z")
            limit: Maximum number of records to return (default: 100)
            offset: Pagination offset (default: 0)
            sort: Sort field (default: "created_at")

        Returns:
            List of ChargingRecord objects containing historical session data

        Raises:
            ValueError: If not authenticated or API request fails

        Example:
            >>> from datetime import datetime, timedelta
            >>> client = ElliAPIClient()
            >>> client.login("user@example.com", "password")
            >>> stations = client.get_stations()
            >>> station_id = stations[0].id
            >>>
            >>> # Get last 30 days of charging records
            >>> now = datetime.utcnow()
            >>> after = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
            >>> before = now.strftime("%Y-%m-%dT%H:%M:%SZ")
            >>>
            >>> records = client.get_charging_records(
            ...     station_id=station_id,
            ...     created_after=after,
            ...     created_before=before
            ... )
            >>>
            >>> for record in records:
            ...     kwh = record.total_energy_wh / 1000
            ...     print(f"{record.start_date_time}: {kwh:.2f} kWh")
        """
        from .models import ChargingRecord, ChargingRecordsResponse

        params = {
            "station_id": station_id,
            "limit": limit,
            "offset": offset,
            "sort": sort,
        }

        if created_after:
            params["created_after"] = created_after
        if created_before:
            params["created_before"] = created_before

        response = self.client.get(
            f"{self.api_base_url}/chargeathome/v1/chargingrecords",
            headers=self._get_headers(),
            params=params,
        )

        if response.status_code != 200:
            raise ValueError(f"Failed to get charging records: {response.status_code} - {response.text}")

        data = response.json()
        records_response = ChargingRecordsResponse(**data)

        return records_response.charging_records

    def get_charging_records_pdf(
        self,
        station_id: str,
        rfid_card_id: Optional[str],
        created_at_after: str,
        created_at_before: str,
        pdf_timezone: str = "Europe/Berlin",
    ) -> bytes:
        """
        Get charging records as PDF invoice for a specific time period.

        Args:
            station_id: The ID of the charging station
            rfid_card_id: RFID card ID to filter records (None = all sessions including App)
            created_at_after: Start timestamp in ISO 8601 format (e.g., "2025-10-31T23:00:00Z")
            created_at_before: End timestamp in ISO 8601 format (e.g., "2025-11-30T22:59:00Z")
            pdf_timezone: Timezone for the PDF (default: "Europe/Berlin")

        Returns:
            PDF file content as bytes

        Raises:
            ValueError: If not authenticated or API request fails

        Example:
            >>> client = ElliAPIClient()
            >>> client.login("user@example.com", "password")
            >>> # Get all charging sessions (RFID + App)
            >>> pdf_data = client.get_charging_records_pdf(
            ...     station_id="a1b2c3d4-1234-5678-abcd-1234567890ab",
            ...     rfid_card_id=None,
            ...     created_at_after="2025-10-31T23:00:00Z",
            ...     created_at_before="2025-11-30T22:59:00Z"
            ... )
            >>> # Or filter by specific RFID card
            >>> pdf_data = client.get_charging_records_pdf(
            ...     station_id="a1b2c3d4-1234-5678-abcd-1234567890ab",
            ...     rfid_card_id="e5f6g7h8-5678-9012-efgh-5678901234cd",
            ...     created_at_after="2025-10-31T23:00:00Z",
            ...     created_at_before="2025-11-30T22:59:00Z"
            ... )
            >>> with open("invoice.pdf", "wb") as f:
            ...     f.write(pdf_data)
        """
        params = {
            "station_id": station_id,
            "pdf_timezone": pdf_timezone,
            "created_at_after": created_at_after,
            "created_at_before": created_at_before,
        }

        # Only add rfid_card_id if provided (None = all sessions)
        if rfid_card_id is not None:
            params["rfid_card_id"] = rfid_card_id

        response = self.client.get(
            f"{self.api_base_url}/chargeathome/v1/chargingrecords/pdf",
            headers=self._get_headers(),
            params=params,
        )

        if response.status_code != 200:
            raise ValueError(f"Failed to get charging records PDF: {response.status_code} - {response.text}")

        return response.content

    def get_rfid_cards(self) -> list[RFIDCard]:
        """
        Get all RFID cards associated with the account.

        Returns:
            List of RFIDCard objects containing:
            - Card ID and number
            - Status (e.g., "active")
            - Brand and tenant information
            - Creation and update timestamps

        Raises:
            ValueError: If not authenticated or API request fails
        """
        response = self.client.get(f"{self.api_base_url}/customer/v1/rfidcards", headers=self._get_headers())

        if response.status_code != 200:
            raise ValueError(f"Failed to get RFID cards: {response.status_code} - {response.text}")

        data = response.json()
        cards = []
        for card_data in data:
            cards.append(RFIDCard(**card_data))

        return cards

    def close(self):
        """
        Close the HTTP client and cleanup resources.

        Should be called when done using the client, or use context manager (with statement).
        """
        self.client.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup"""
        self.close()
