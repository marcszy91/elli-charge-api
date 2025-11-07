"""
Test client for Elli Charging API

This script demonstrates how to:
1. Login to the API
2. Get charging status
3. Display the results
"""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv  # noqa: E402

from elli_api_client import ElliAPIClient  # noqa: E402


def main():
    # Load credentials from .env file
    load_dotenv()

    email = os.getenv("ELLI_EMAIL")
    password = os.getenv("ELLI_PASSWORD")

    if not email or not password:
        print("Error: ELLI_EMAIL and ELLI_PASSWORD must be set in .env file")
        print("Please copy .env.example to .env and fill in your credentials")
        return

    print("=" * 60)
    print("Elli Charging API Test Client")
    print("=" * 60)
    print()

    # Create client
    with ElliAPIClient() as client:
        # Step 1: Login
        print("[1/4] Logging in...")
        try:
            token = client.login(email, password)
            print("[OK] Login successful!")
            print(f"  - Token type: {token.token_type}")
            print(f"  - Expires in: {token.expires_in} seconds")
            print(f"  - Access token: {token.access_token[:50]}...")
            print()
        except Exception as e:
            print(f"[ERROR] Login failed: {e}")
            return

        # Step 2: Get stations
        print("[2/4] Fetching charging stations...")
        try:
            stations = client.get_stations()
            print(f"[OK] Found {len(stations)} station(s)")
            for i, station in enumerate(stations, 1):
                print(f"\n  Station {i}:")
                print(f"    - Name: {station.name}")
                print(f"    - ID: {station.id}")
                print(f"    - Model: {station.model}")
                print(f"    - Serial: {station.serial_number}")
                print(f"    - Firmware: {station.firmware_version}")
            print()
        except Exception as e:
            print(f"[ERROR] Failed to get stations: {e}")
            return

        # Step 3: Get charging sessions
        print("[3/4] Fetching charging sessions...")
        try:
            sessions = client.get_charging_sessions(include_momentary_speed=True)
            print(f"[OK] Found {len(sessions)} charging session(s)")

            active_sessions = [s for s in sessions if s.end_date_time is None]
            completed_sessions = [s for s in sessions if s.end_date_time is not None]

            print(f"  - Active: {len(active_sessions)}")
            print(f"  - Completed: {len(completed_sessions)}")

            if active_sessions:
                print("\n  Active Sessions:")
                for session in active_sessions:
                    print(f"\n    Session ID: {session.id}")
                    print(f"    - Station ID: {session.station_id}")
                    print(f"    - Started: {session.start_date_time}")
                    if session.accumulated_energy_wh is not None:
                        print(f"    - Energy: {session.accumulated_energy_wh / 1000:.2f} kWh")
                    if session.momentary_charging_speed_watts:
                        print(f"    - Current Power: {session.momentary_charging_speed_watts / 1000:.2f} kW")
                    if session.status:
                        print(f"    - Status: {session.status}")
            print()
        except Exception as e:
            print(f"[ERROR] Failed to get charging sessions: {e}")
            return

        # Step 4: Get accumulated charging for each station
        if stations:
            print("[4/4] Fetching accumulated charging data...")
            try:
                for station in stations:
                    accumulated = client.get_accumulated_charging(station.id)
                    print(f"\n  Station: {station.name}")
                    if "accumulated_energy_wh" in accumulated:
                        energy_kwh = accumulated["accumulated_energy_wh"] / 1000
                        print(f"    - Total Energy: {energy_kwh:.2f} kWh")

                        if (
                            "momentary_charging_speed_watts" in accumulated
                            and accumulated["momentary_charging_speed_watts"]
                        ):
                            power_kw = accumulated["momentary_charging_speed_watts"] / 1000
                            print(f"    - Current Power: {power_kw:.2f} kW")

                        if "start_date_time" in accumulated:
                            print(f"    - Session Start: {accumulated['start_date_time']}")
                    else:
                        print("    - No active charging session")
            except Exception as e:
                print(f"[ERROR] Failed to get accumulated charging: {e}")

    print()
    print("=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
