# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.1.0 (2025-11-07)


### Features

* initial implementation of Elli API client and FastAPI server ([a28787c](https://github.com/marcszy91/elli-charge-api/commit/a28787c29137ce1c90640ce3ad372a08365cde5d))


### Bug Fixes

* disable GitHub Actions cache and release-client auto-trigger ([8fd517b](https://github.com/marcszy91/elli-charge-api/commit/8fd517b28070e1308ea597530fb6831d042dedc4))
* resolve GitHub Actions workflow issues and linting errors ([227866a](https://github.com/marcszy91/elli-charge-api/commit/227866ac4f3da8575d7956a3d03478ff69961cb4))

## [Unreleased]

### Added
- Initial implementation of Elli Charging API
- OAuth2 PKCE authentication
- FastAPI endpoints for charging stations and sessions
- Docker support with multi-stage builds
- CI/CD pipeline with GitHub Actions
- Conventional commits enforcement
- Automatic changelog generation
- Pre-commit hooks for code quality
