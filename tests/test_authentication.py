"""Unit tests for browser-based OAuth authentication."""

import base64
import hashlib
import json
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
import pytest

from elli_client import (
    ElliAPIClient,
    InvalidOAuthCallback,
    InvalidOAuthState,
    ReauthenticationRequired,
    TokenExchangeError,
    TokenResponse,
)


def _callback(client: ElliAPIClient, state: str, code: str = "authorization-code") -> str:
    return f"{client.redirect_uri}?{urlencode({'code': code, 'state': state})}"


def _set_transport(client: ElliAPIClient, handler) -> None:
    client.client.close()
    client.client = httpx.Client(transport=httpx.MockTransport(handler), timeout=30.0)


def test_pkce_verifier_and_s256_challenge_are_valid() -> None:
    client = ElliAPIClient()
    authorization = client.create_authorization()
    query = parse_qs(urlparse(authorization.authorization_url).query)

    expected = (
        base64.urlsafe_b64encode(hashlib.sha256(authorization.code_verifier.encode()).digest()).decode().rstrip("=")
    )
    assert 43 <= len(authorization.code_verifier) <= 128
    assert query["code_challenge"] == [expected]
    assert query["code_challenge_method"] == ["S256"]
    client.close()


def test_authorization_url_contains_expected_parameters_and_offline_access() -> None:
    client = ElliAPIClient(scope="openid profile")
    authorization = client.create_authorization()
    parsed = urlparse(authorization.authorization_url)
    query = parse_qs(parsed.query)

    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == f"{client.auth_base_url}/authorize"
    assert query["client_id"] == [client.client_id]
    assert query["audience"] == [client.audience]
    assert query["redirect_uri"] == [client.redirect_uri]
    assert query["response_type"] == ["code"]
    assert query["state"] == [authorization.state]
    assert "offline_access" in query["scope"][0].split()
    client.close()


def test_authorization_state_is_unique() -> None:
    client = ElliAPIClient()
    assert client.create_authorization().state != client.create_authorization().state
    client.close()


def test_valid_callback_exchanges_code() -> None:
    client = ElliAPIClient()
    authorization = client.create_authorization()

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert request.url.path == "/oauth/token"
        assert payload == {
            "code": "authorization-code",
            "client_id": client.client_id,
            "redirect_uri": client.redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": authorization.code_verifier,
        }
        return httpx.Response(
            200,
            json={
                "access_token": "access-secret",
                "refresh_token": "refresh-secret",
                "id_token": "id-secret",
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": "openid profile offline_access",
            },
        )

    _set_transport(client, handler)
    tokens = client.exchange_callback(_callback(client, authorization.state), authorization)

    assert tokens.access_token == "access-secret"
    assert tokens.expires_at is not None
    assert client.access_token is None
    client.close()


def test_wrong_state_is_rejected_without_network_request() -> None:
    client = ElliAPIClient()
    authorization = client.create_authorization()
    with pytest.raises(InvalidOAuthState):
        client.exchange_callback(_callback(client, "wrong-state"), authorization)
    client.close()


def test_duplicate_state_is_rejected() -> None:
    client = ElliAPIClient()
    authorization = client.create_authorization()
    callback = f"{client.redirect_uri}?code=x&state={authorization.state}&state={authorization.state}"
    with pytest.raises(InvalidOAuthState):
        client.exchange_callback(callback, authorization)
    client.close()


def test_missing_code_is_rejected() -> None:
    client = ElliAPIClient()
    authorization = client.create_authorization()
    with pytest.raises(InvalidOAuthCallback, match="authorization code"):
        client.exchange_callback(f"{client.redirect_uri}?state={authorization.state}", authorization)
    client.close()


def test_oauth_callback_error_is_handled_without_description_secret() -> None:
    client = ElliAPIClient()
    authorization = client.create_authorization()
    callback = f"{client.redirect_uri}?" + urlencode(
        {"error": "access_denied", "error_description": "do not reveal secret-token"}
    )
    with pytest.raises(InvalidOAuthCallback) as raised:
        client.exchange_callback(callback, authorization)
    assert "access_denied" in str(raised.value)
    assert "secret-token" not in str(raised.value)
    client.close()


@pytest.mark.parametrize(
    "callback_url",
    [
        "wrong.scheme://login.elli.eco/ios/com.elli.ios.emsp/callback",
        "com.elli.ios.emsp://evil.example/ios/com.elli.ios.emsp/callback",
        "com.elli.ios.emsp://login.elli.eco/wrong/callback",
    ],
)
def test_wrong_callback_origin_or_path_is_rejected(callback_url: str) -> None:
    client = ElliAPIClient()
    authorization = client.create_authorization()
    with pytest.raises(InvalidOAuthCallback, match="redirect URI"):
        client.exchange_callback(f"{callback_url}?code=x&state={authorization.state}", authorization)
    client.close()


@pytest.mark.parametrize("rotated", [True, False])
def test_refresh_handles_rotation_and_preserves_existing_token(rotated: bool) -> None:
    client = ElliAPIClient()

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload == {
            "grant_type": "refresh_token",
            "client_id": client.client_id,
            "refresh_token": "old-refresh-secret",
        }
        response = {"access_token": "new-access-secret", "expires_in": 3600}
        if rotated:
            response["refresh_token"] = "rotated-refresh-secret"
        return httpx.Response(200, json=response)

    _set_transport(client, handler)
    tokens = client.refresh("old-refresh-secret")
    expected = "rotated-refresh-secret" if rotated else "old-refresh-secret"
    assert tokens.refresh_token == expected
    client.close()


def test_invalid_grant_requires_reauthentication_and_redacts_response() -> None:
    client = ElliAPIClient()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={"error": "invalid_grant", "error_description": "revoked refresh-secret"},
        )

    _set_transport(client, handler)
    with pytest.raises(ReauthenticationRequired) as raised:
        client.refresh("refresh-secret")
    assert "refresh-secret" not in str(raised.value)
    client.close()


def test_token_exchange_error_and_model_repr_do_not_expose_tokens() -> None:
    client = ElliAPIClient()
    authorization = client.create_authorization()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text="access-secret refresh-secret authorization-code")

    _set_transport(client, handler)
    with pytest.raises(TokenExchangeError) as raised:
        client.exchange_callback(_callback(client, authorization.state), authorization)
    message = str(raised.value)
    assert "access-secret" not in message
    assert "refresh-secret" not in message
    assert "authorization-code" not in message

    tokens = TokenResponse(
        access_token="access-secret",
        refresh_token="refresh-secret",
        id_token="id-secret",
    )
    rendered = repr(tokens)
    assert "access-secret" not in rendered
    assert "refresh-secret" not in rendered
    assert "id-secret" not in rendered
    client.close()


def test_invalid_token_response_does_not_leak_through_exception_chain() -> None:
    client = ElliAPIClient()
    authorization = client.create_authorization()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"access_token": {"secret": "nested-access-secret"}})

    _set_transport(client, handler)
    with pytest.raises(TokenExchangeError) as raised:
        client.exchange_callback(_callback(client, authorization.state), authorization)
    assert "nested-access-secret" not in str(raised.value)
    assert raised.value.__cause__ is None
    client.close()


def test_set_tokens_and_set_access_token_update_existing_client_state() -> None:
    client = ElliAPIClient()
    tokens = TokenResponse(access_token="first", refresh_token="refresh")
    client.set_tokens(tokens)
    assert client.access_token == "first"
    assert client.refresh_token == "refresh"
    client.set_access_token("second")
    assert client.access_token == "second"
    client.close()
