# Changelog - Elli API Client

All notable changes to the `elli-api-client` package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of elli-api-client package
- OAuth2 PKCE authentication for Elli Charging API
- Support for charging stations and sessions
- Flexible configuration via parameters, environment, or defaults
- Built-in defaults from official Elli iOS app
- Full type hints with Pydantic models

### Features
- `ElliAPIClient` - Main API client class
- `login()` - OAuth2 PKCE authentication
- `get_stations()` - Get all charging stations
- `get_charging_sessions()` - Get charging sessions
- `get_accumulated_charging()` - Get accumulated charging data
- Automatic token management
- Context manager support (`with` statement)

## [0.1.0] - Unreleased

Initial development version.
