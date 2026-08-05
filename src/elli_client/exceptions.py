"""Exceptions raised by the Elli client."""


class ElliClientError(Exception):
    """Base class for errors raised by this library."""


class AuthenticationError(ElliClientError):
    """Base class for authentication errors."""


class InvalidOAuthCallback(AuthenticationError):
    """The OAuth callback is malformed, unexpected, or reports an error."""


class InvalidOAuthState(InvalidOAuthCallback):
    """The callback state does not match the authorization session."""


class TokenExchangeError(AuthenticationError):
    """An authorization code could not be exchanged for tokens."""


class TokenRefreshError(AuthenticationError):
    """A refresh-token request failed."""


class ReauthenticationRequired(TokenRefreshError):
    """The refresh token is no longer valid and interactive login is required."""
