"""Offline tests for the native callback developer harness."""

from __future__ import annotations

import io
import json
import os
import plistlib
import socket
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from scripts.native_callback_common import (
    MAX_IPC_PAYLOAD_BYTES,
    HarnessError,
    InvalidIPCSecret,
    IPCSession,
    PayloadTooLarge,
    SessionExpired,
    create_listener,
    delete_session,
    load_session,
    load_tokens,
    merge_refresh_token,
    receive_callback,
    save_tokens,
    write_session,
)
from scripts.test_native_callback import print_status, windows_open_command

from elli_client import TokenResponse

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent


def _session(port: int = 12345, age: timedelta = timedelta()) -> IPCSession:
    return IPCSession(
        port=port,
        secret="s" * 43,
        created_at=datetime.now(timezone.utc) - age,
        pid=os.getpid(),
    )


def _send(port: int, payload: bytes) -> None:
    with socket.create_connection(("127.0.0.1", port), timeout=1.0) as connection:
        connection.sendall(payload)
        connection.shutdown(socket.SHUT_WR)


def test_session_file_is_private_created_and_deleted(tmp_path: Path) -> None:
    path = tmp_path / "private" / "oauth-session.json"
    session = _session()
    write_session(path, session)
    assert load_session(path).port == session.port
    if os.name != "nt":
        assert path.stat().st_mode & 0o777 == 0o600
    delete_session(path)
    assert not path.exists()


def test_expired_session_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "oauth-session.json"
    write_session(path, _session(age=timedelta(minutes=6)))
    with pytest.raises(SessionExpired):
        load_session(path)


def test_wrong_ipc_secret_is_rejected() -> None:
    listener = create_listener()
    port = listener.getsockname()[1]
    payload = json.dumps({"secret": "wrong", "callback_url": "safe-callback"}).encode()
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(receive_callback, listener, "expected", 1.0)
        _send(port, payload)
        with pytest.raises(InvalidIPCSecret):
            future.result()


def test_oversized_payload_is_rejected() -> None:
    listener = create_listener()
    port = listener.getsockname()[1]
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(receive_callback, listener, "expected", 1.0)
        _send(port, b"x" * (MAX_IPC_PAYLOAD_BYTES + 1))
        with pytest.raises(PayloadTooLarge):
            future.result()


def test_listener_accepts_only_one_connection() -> None:
    listener = create_listener()
    port = listener.getsockname()[1]
    payload = json.dumps({"secret": "expected", "callback_url": "safe-callback"}).encode()
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(receive_callback, listener, "expected", 1.0)
        _send(port, payload)
        assert future.result() == "safe-callback"
    assert listener.fileno() == -1


def test_listener_timeout() -> None:
    listener = create_listener()
    with pytest.raises(HarnessError, match="Timed out"):
        receive_callback(listener, "expected", 0.01)
    assert listener.fileno() == -1


def test_tokens_are_written_atomically_and_privately(tmp_path: Path) -> None:
    path = tmp_path / "tokens.json"
    save_tokens(path, TokenResponse(access_token="access-value", refresh_token="refresh-value"))
    loaded = load_tokens(path)
    assert loaded.access_token == "access-value"
    assert loaded.refresh_token == "refresh-value"
    assert list(tmp_path.glob(".*.tmp")) == []
    if os.name != "nt":
        assert path.stat().st_mode & 0o777 == 0o600


def test_refresh_token_rotation_and_preservation() -> None:
    previous = TokenResponse(access_token="old-access", refresh_token="old-refresh")
    rotated = TokenResponse(access_token="new-access", refresh_token="new-refresh")
    omitted = TokenResponse(access_token="newer-access")
    assert merge_refresh_token(previous, rotated).refresh_token == "new-refresh"
    assert merge_refresh_token(previous, omitted).refresh_token == "old-refresh"


def test_status_output_never_contains_token_values(tmp_path: Path) -> None:
    save_tokens(
        tmp_path / "tokens.json",
        TokenResponse(access_token="access-value-never-print", refresh_token="refresh-value-never-print"),
    )
    output = io.StringIO()
    print_status(tmp_path, platform_name="test-platform", output=output)
    rendered = output.getvalue()
    assert "Access token present: yes" in rendered
    assert "Refresh token present: yes" in rendered
    assert "access-value-never-print" not in rendered
    assert "refresh-value-never-print" not in rendered


def test_windows_registry_command_quotes_all_paths() -> None:
    command = windows_open_command(
        r"C:\Program Files\Python\python.exe",
        Path(r"C:\Development Folder\elli-client\scripts\native_callback_handler.py"),
    )
    assert command == (
        '"C:\\Program Files\\Python\\python.exe" '
        '"C:\\Development Folder\\elli-client\\scripts\\native_callback_handler.py" "%1"'
    )


def test_macos_info_plist_registers_callback_scheme() -> None:
    plist_path = REPOSITORY_ROOT / "scripts" / "macos" / "Info.plist"
    with plist_path.open("rb") as plist_file:
        configuration = plistlib.load(plist_file)
    schemes = [scheme for entry in configuration["CFBundleURLTypes"] for scheme in entry["CFBundleURLSchemes"]]
    assert "com.elli.ios.emsp" in schemes
    assert configuration["LSUIElement"] is True
