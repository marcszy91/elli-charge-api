# Quick Start Guide

## Interactive authentication

```python
from elli_client import ElliAPIClient

with ElliAPIClient() as client:
    authorization = client.create_authorization()

    # Implement these two platform-specific operations in your application.
    open_in_normal_browser(authorization.authorization_url)
    callback_url = receive_custom_scheme_callback()

    tokens = client.exchange_callback(callback_url, authorization)
    client.set_tokens(tokens)

    for station in client.get_stations():
        print(station.name, station.id)

    # Store this securely in the calling application, not in Elli Client.
    persist_refresh_token(tokens.refresh_token)
```

`create_authorization()` only constructs the URL and PKCE state. Elli Client intentionally does not open a browser, register a URL handler, automate Turnstile, or persist tokens.

## Later starts

```python
from elli_client import ElliAPIClient, ReauthenticationRequired

with ElliAPIClient() as client:
    try:
        tokens = client.refresh(load_refresh_token())
    except ReauthenticationRequired:
        # Repeat the interactive flow above.
        raise

    client.set_tokens(tokens)
    persist_refresh_token(tokens.refresh_token)
    sessions = client.get_charging_sessions(include_momentary_speed=True)
```

Always store the returned refresh token: it may be newly rotated, or it will contain the original token when the server omitted a replacement.

## Error handling

OAuth-specific failures derive from `ElliClientError`:

```python
from elli_client import InvalidOAuthCallback, InvalidOAuthState, TokenExchangeError

try:
    tokens = client.exchange_callback(callback_url, authorization)
except InvalidOAuthState:
    # Reject callbacks that do not belong to this authorization attempt.
    raise
except (InvalidOAuthCallback, TokenExchangeError):
    # Show a generic authentication failure; exceptions do not contain tokens.
    raise
```

See the [API reference](api.md) for all authentication methods and data APIs.
