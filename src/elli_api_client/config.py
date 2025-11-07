"""Configuration management for Elli API"""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # User Credentials
    elli_email: Optional[str] = None
    elli_password: Optional[str] = None
    elli_station_id: Optional[str] = None

    # OAuth2 Configuration (optional overrides)
    # If not set in .env, defaults from ElliAPIClient will be used
    elli_auth_base_url: Optional[str] = None
    elli_api_base_url: Optional[str] = None
    elli_client_id: Optional[str] = None
    elli_redirect_uri: Optional[str] = None
    elli_audience: Optional[str] = None
    elli_scope: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
