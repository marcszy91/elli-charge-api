"""FastAPI application for Elli Charging API"""

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

from elli_api_client import ChargingSession, ElliAPIClient, Station

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Elli Charging API",
    description="Reverse-engineered API for Elli Wallbox charging data",
    version="0.1.0",
)


# Request/Response Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class ChargingStatusResponse(BaseModel):
    stations: list[Station]
    active_sessions: list[ChargingSession]
    total_active_sessions: int


# Global client instance (in production, use proper session management)
_elli_clients: dict[str, ElliAPIClient] = {}


def get_client(token: str) -> ElliAPIClient:
    """Get or create an Elli client for a given token"""
    if token not in _elli_clients:
        client = ElliAPIClient()
        client.access_token = token
        _elli_clients[token] = client
    return _elli_clients[token]


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Elli Charging API",
        "version": "0.1.0",
        "endpoints": {
            "login": "/login",
            "charging_status": "/charging-status",
            "stations": "/stations",
            "sessions": "/charging-sessions",
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}


@app.post("/login", response_model=LoginResponse)
async def login(login_request: LoginRequest):
    """
    Login to Elli API using email and password.
    Returns access token and refresh token.
    """
    try:
        client = ElliAPIClient()
        token_response = client.login(login_request.email, login_request.password)

        # Store client with token
        _elli_clients[token_response.access_token] = client

        return LoginResponse(
            access_token=token_response.access_token,
            refresh_token=token_response.refresh_token,
            token_type=token_response.token_type,
            expires_in=token_response.expires_in,
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Login failed: {str(e)}")


@app.get("/charging-status", response_model=ChargingStatusResponse)
async def get_charging_status(token: str):
    """
    Get current charging status including stations and active sessions.

    Args:
        token: Access token from login endpoint
    """
    try:
        client = get_client(token)

        # Get stations
        stations = client.get_stations()

        # Get charging sessions
        sessions = client.get_charging_sessions(include_momentary_speed=True)

        # Filter active sessions (those without end_date_time)
        active_sessions = [s for s in sessions if s.end_date_time is None]

        return ChargingStatusResponse(
            stations=stations, active_sessions=active_sessions, total_active_sessions=len(active_sessions)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get charging status: {str(e)}")


@app.get("/stations")
async def get_stations(token: str):
    """
    Get all charging stations.

    Args:
        token: Access token from login endpoint
    """
    try:
        client = get_client(token)
        stations = client.get_stations()
        return {"stations": stations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stations: {str(e)}")


@app.get("/charging-sessions")
async def get_charging_sessions(token: str, include_momentary_speed: bool = True):
    """
    Get all charging sessions.

    Args:
        token: Access token from login endpoint
        include_momentary_speed: Include current charging speed in watts
    """
    try:
        client = get_client(token)
        sessions = client.get_charging_sessions(include_momentary_speed)
        return {"charging_sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get charging sessions: {str(e)}")


@app.get("/charging-sessions/accumulated/{station_id}")
async def get_accumulated_charging(token: str, station_id: str):
    """
    Get accumulated charging data for a specific station.

    Args:
        token: Access token from login endpoint
        station_id: Station ID (UUID)
    """
    try:
        client = get_client(token)
        data = client.get_accumulated_charging(station_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get accumulated charging: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
