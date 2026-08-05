## [1.5.0](https://github.com/mawiak/elli-client/compare/v1.4.0...v1.5.0) (2026-08-05)


### Features

* implement Cloudflare CAPTCHA login flow with PKCE and update documentation ([cde89fa](https://github.com/mawiak/elli-client/commit/cde89faa4f0648837c14871bef442b68392620ad))

## [1.4.0](https://github.com/mawiak/elli-client/compare/v1.3.0...v1.4.0) (2026-07-13)


### Features

* add charging records retrieval functionality and update models ([844f7c2](https://github.com/mawiak/elli-client/commit/844f7c224cb4314a970af83391a7c9558dbeefa2))


### Bug Fixes

* reorder imports and update __all__ in __init__.py ([c9f6231](https://github.com/mawiak/elli-client/commit/c9f623176bb25503507b7c713a97fa8d92aa13f6))

## [1.3.0](https://github.com/mawiak/elli-client/compare/v1.2.0...v1.3.0) (2026-05-24)


### Features

* allow export all chargin session without filter (include app) ([e02e0fb](https://github.com/mawiak/elli-client/commit/e02e0fbd66b9a2db08f03e2cba3f5b989016c5bc))

## [1.2.0](https://github.com/marcszy91/elli-client/compare/v1.1.1...v1.2.0) (2025-12-08)


### Features

* add function to get rfid card information ([5fcd1e4](https://github.com/marcszy91/elli-client/commit/5fcd1e410489bebe6713ecf10fe822e110eedc86))

## [1.1.1](https://github.com/marcszy91/elli-client/compare/v1.1.0...v1.1.1) (2025-12-06)


### Bug Fixes

* ignore external env ([11bd148](https://github.com/marcszy91/elli-client/commit/11bd14803e5cf6664d2ed0000c6a9f89f99e7c13))

## [1.1.0](https://github.com/marcszy91/elli-client/compare/v1.0.3...v1.1.0) (2025-12-05)


### Features

* add function to get charging records as pdf ([796d537](https://github.com/marcszy91/elli-client/commit/796d5371b65c265fe3933590c53366b910465a08))

## [1.0.3](https://github.com/marcszy91/elli-client/compare/v1.0.2...v1.0.3) (2025-11-14)


### Bug Fixes

* check tag creation time for PyPI publish ([77e9e3b](https://github.com/marcszy91/elli-client/commit/77e9e3baf1eaec20404c42916b97bd232e73d299))

## [1.0.2](https://github.com/marcszy91/elli-client/compare/v1.0.1...v1.0.2) (2025-11-14)


### Bug Fixes

* improve PyPI publish detection logic ([26ff0b1](https://github.com/marcszy91/elli-client/commit/26ff0b12055294a24508c62e37ff153cb27ca745))

## [1.0.1](https://github.com/marcszy91/elli-client/compare/v1.0.0...v1.0.1) (2025-11-14)


### Bug Fixes

* add flake8 to dev dependencies ([bd5afd3](https://github.com/marcszy91/elli-client/commit/bd5afd30f2abddc3031a8e80bdc507e1afddf745))
* inline CI checks in release workflow ([0dff233](https://github.com/marcszy91/elli-client/commit/0dff233daa2f20c7b0b95a545b660d85e1bc2eb0))

# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-11-14

### Added
- Initial release of Elli Client
- Authentication
- Query charging stations
- Retrieve charging sessions (active and historical)
- Current charging power and energy consumption
