"""Data models for Elli API"""

from typing import Optional

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    id_token: str
    token_type: str
    expires_in: int
    scope: str


class ChargingSession(BaseModel):
    id: str
    station_id: str
    user_id: Optional[str] = None
    start_date_time: str
    end_date_time: Optional[str] = None
    accumulated_energy_wh: Optional[int] = None
    momentary_charging_speed_watts: Optional[int] = None
    status: Optional[str] = None


class Station(BaseModel):
    id: str
    name: str
    serial_number: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
