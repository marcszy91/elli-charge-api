"""Shared local IPC and storage helpers for the native callback test harness."""

from __future__ import annotations

import hmac
import json
import os
import secrets
import socket
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from elli_client import TokenResponse

SESSION_FILENAME = "oauth-session.json"
TOKEN_FILENAME = "tokens.json"
SESSION_MAX_AGE = timedelta(minutes=5)
CALLBACK_TIMEOUT_SECONDS = 300.0
MAX_IPC_PAYLOAD_BYTES = 16 * 1024


class HarnessError(Exception):
    """Safe, user-facing failure from the developer test harness."""


class SessionExpired(HarnessError):
    """The callback session is no longer fresh."""


class InvalidIPCSecret(HarnessError):
    """The callback sender did not know the one-time IPC secret."""


class PayloadTooLarge(HarnessError):
    """The callback IPC payload exceeded its size limit."""


@dataclass(frozen=True)
class IPCSession:
    """Short-lived coordinates used by the callback helper."""

    port: int
    secret: str
    created_at: datetime
    pid: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize the session without logging it."""
        return {
            "port": self.port,
            "secret": self.secret,
            "created_at": self.created_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "pid": self.pid,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "IPCSession":
        """Validate and deserialize a stored session."""
        try:
            timestamp = str(value["created_at"])
            created_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            port = int(value["port"])
            pid = int(value["pid"])
            secret = str(value["secret"])
        except (KeyError, TypeError, ValueError) as exc:
            raise HarnessError("Callback session file is invalid") from exc
        if created_at.tzinfo is None or not 1 <= port <= 65535 or pid <= 0 or len(secret) < 43:
            raise HarnessError("Callback session file is invalid")
        return cls(port=port, secret=secret, created_at=created_at, pid=pid)


def app_data_directory(platform_name: str | None = None, environ: Mapping[str, str] | None = None) -> Path:
    """Return the documented per-user developer-data directory."""
    platform_name = platform_name or os.sys.platform
    environ = environ or os.environ
    if platform_name == "darwin":
        return Path(environ.get("HOME", str(Path.home()))) / "Library" / "Application Support" / "elli-client-dev"
    if platform_name == "win32":
        local_app_data = environ.get("LOCALAPPDATA")
        if not local_app_data:
            raise HarnessError("LOCALAPPDATA is not set")
        return Path(local_app_data) / "elli-client-dev"
    raise HarnessError("Native callback E2E testing is supported only on macOS and Windows")


def session_path(data_directory: Path) -> Path:
    return data_directory / SESSION_FILENAME


def token_path(data_directory: Path) -> Path:
    return data_directory / TOKEN_FILENAME


def atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    """Atomically write private JSON, using mode 0600 on Unix."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name != "nt":
        path.parent.chmod(0o700)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            if os.name != "nt":
                os.chmod(temporary_name, 0o600)
            json.dump(value, temporary, separators=(",", ":"), sort_keys=True)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
        if os.name != "nt":
            path.chmod(0o600)
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)


def write_session(path: Path, session: IPCSession) -> None:
    atomic_write_json(path, session.to_dict())


def load_session(path: Path, now: datetime | None = None) -> IPCSession:
    """Read a fresh callback session, rejecting stale or future timestamps."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HarnessError("No valid callback session is available") from exc
    if not isinstance(value, dict):
        raise HarnessError("Callback session file is invalid")
    session = IPCSession.from_dict(value)
    now = now or datetime.now(timezone.utc)
    age = now - session.created_at.astimezone(timezone.utc)
    if age < timedelta(seconds=-30) or age > SESSION_MAX_AGE:
        raise SessionExpired("Callback session has expired")
    return session


def delete_session(path: Path) -> None:
    path.unlink(missing_ok=True)


def save_tokens(path: Path, tokens: TokenResponse) -> None:
    """Persist a token response atomically for this developer-only harness."""
    atomic_write_json(path, tokens.model_dump(mode="json", exclude_none=True))


def load_tokens(path: Path) -> TokenResponse:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return TokenResponse.model_validate(value)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise HarnessError("No valid developer token file is available") from exc


def merge_refresh_token(previous: TokenResponse, refreshed: TokenResponse) -> TokenResponse:
    """Preserve the previous refresh token when a mocked/provider response omits rotation."""
    if refreshed.refresh_token is None:
        return refreshed.model_copy(update={"refresh_token": previous.refresh_token})
    return refreshed


def create_listener() -> socket.socket:
    """Bind a single-use TCP listener exclusively to IPv4 loopback."""
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    return listener


def create_ipc_session(listener: socket.socket) -> IPCSession:
    host, port = listener.getsockname()
    if host != "127.0.0.1":
        raise HarnessError("IPC listener is not bound to loopback")
    return IPCSession(
        port=port,
        secret=secrets.token_urlsafe(32),
        created_at=datetime.now(timezone.utc),
        pid=os.getpid(),
    )


def _read_limited(connection: socket.socket) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = connection.recv(min(4096, MAX_IPC_PAYLOAD_BYTES + 1 - total))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > MAX_IPC_PAYLOAD_BYTES:
            raise PayloadTooLarge("Callback IPC payload is too large")
    return b"".join(chunks)


def receive_callback(listener: socket.socket, expected_secret: str, timeout: float) -> str:
    """Accept exactly one callback payload and return its URL without logging it."""
    listener.settimeout(timeout)
    try:
        connection, address = listener.accept()
    except TimeoutError as exc:
        raise HarnessError("Timed out waiting for the OAuth callback") from exc
    finally:
        listener.close()
    if address[0] != "127.0.0.1":
        connection.close()
        raise HarnessError("Rejected non-loopback callback connection")
    with connection:
        connection.settimeout(5.0)
        try:
            raw_payload = _read_limited(connection)
        except TimeoutError as exc:
            raise HarnessError("Timed out while reading the callback IPC payload") from exc
    try:
        payload = json.loads(raw_payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HarnessError("Callback IPC payload is invalid") from exc
    if not isinstance(payload, dict):
        raise HarnessError("Callback IPC payload is invalid")
    supplied_secret = payload.get("secret")
    callback_url = payload.get("callback_url")
    if not isinstance(supplied_secret, str) or not hmac.compare_digest(supplied_secret, expected_secret):
        raise InvalidIPCSecret("Callback IPC secret is invalid")
    if not isinstance(callback_url, str) or len(callback_url) > MAX_IPC_PAYLOAD_BYTES:
        raise HarnessError("Callback IPC URL is invalid")
    return callback_url


def forward_callback(callback_url: str, path: Path) -> None:
    """Forward an OS-delivered callback to the waiting loopback listener."""
    session = load_session(path)
    payload = json.dumps({"secret": session.secret, "callback_url": callback_url}, separators=(",", ":")).encode(
        "utf-8"
    )
    if len(payload) > MAX_IPC_PAYLOAD_BYTES:
        raise PayloadTooLarge("Callback IPC payload is too large")
    try:
        with socket.create_connection(("127.0.0.1", session.port), timeout=5.0) as connection:
            connection.sendall(payload)
            connection.shutdown(socket.SHUT_WR)
    except OSError as exc:
        raise HarnessError("Could not deliver callback to the waiting test process") from exc
