# Elli Client

Python client library for the Elli Wallbox API.

## Installation

```bash
pip install elli-client
```

## Browser-based login with PKCE

Elli's Auth0 login uses Cloudflare Turnstile. Authentication therefore takes place interactively in a normal browser; this library neither opens the browser nor automates the CAPTCHA.

```python
from elli_client import ElliAPIClient

client = ElliAPIClient()

# No network request is made here. Keep this object until the callback arrives.
authorization = client.create_authorization()

# Your application opens this URL in the user's browser.
print(authorization.authorization_url)

# Your application receives the complete custom-scheme callback URL, for example:
# com.elli.ios.emsp://login.elli.eco/ios/com.elli.ios.emsp/callback?code=...&state=...
callback_url = receive_callback_in_your_application()

tokens = client.exchange_callback(
    callback_url=callback_url,
    authorization=authorization,
)
client.set_tokens(tokens)

stations = client.get_stations()
```

The calling application is responsible for opening `authorization_url`, receiving the callback URL, and securely storing the refresh token. Elli Client deliberately contains no browser, GUI, URL-handler registration, Keychain integration, or persistent token storage. It never needs or processes the user's Elli password in the recommended flow.

## Refreshing tokens

At a later application start, load the refresh token from the application's secure storage:

```python
from elli_client import ElliAPIClient, ReauthenticationRequired

client = ElliAPIClient()

try:
    tokens = client.refresh(stored_refresh_token)
except ReauthenticationRequired:
    # Start the interactive browser flow again.
    raise

client.set_tokens(tokens)
store_refresh_token_securely(tokens.refresh_token)
```

Auth0 may rotate refresh tokens. `refresh()` returns the new token when one is supplied; if the response omits it, the returned `TokenResponse.refresh_token` retains the token passed to `refresh()`. Consumers should always persist the refresh token from the returned object.

## Password-login migration

The former call remains temporarily available to avoid an immediate breaking change:

```python
token = client.login(email, password)  # deprecated and unreliable
```

It now emits `DeprecationWarning`. Cloudflare Turnstile makes this direct HTTP login unreliable, and the library does not attempt to bypass it. Migrate to `create_authorization()`, `exchange_callback()`, and `set_tokens()` as shown above.

## API features

- Query charging stations and firmware
- Retrieve active and historical charging sessions
- Retrieve RFID card data
- Retrieve charging records and download charging-report PDFs
- Refresh OAuth tokens with rotation support

See the [quick-start guide](docs/quick-start.md) and [API reference](docs/api.md) for details.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
black --check src tests
isort --check-only src tests
flake8 src tests
```

## Home Assistant Integration

This client is used by the [Elli Charger HACS integration](https://github.com/marcszy91/hacs-elli-charger) for Home Assistant.

## License and disclaimer

MIT License - see LICENSE. This library was created through reverse engineering of the official Elli iPhone app. It is not officially supported by Elli or Volkswagen Group Charging GmbH. Use at your own risk.
