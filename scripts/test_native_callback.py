#!/usr/bin/env python3
"""Manual macOS/Windows native OAuth callback E2E test harness."""

from __future__ import annotations

import argparse
import subprocess
import sys
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, TextIO

from elli_client import ElliAPIClient, ReauthenticationRequired, TokenResponse

try:
    from .native_callback_common import (
        CALLBACK_TIMEOUT_SECONDS,
        HarnessError,
        app_data_directory,
        create_ipc_session,
        create_listener,
        delete_session,
        load_tokens,
        merge_refresh_token,
        receive_callback,
        save_tokens,
        session_path,
        token_path,
        write_session,
    )
except ImportError:  # Direct execution: python scripts/test_native_callback.py
    from native_callback_common import (
        CALLBACK_TIMEOUT_SECONDS,
        HarnessError,
        app_data_directory,
        create_ipc_session,
        create_listener,
        delete_session,
        load_tokens,
        merge_refresh_token,
        receive_callback,
        save_tokens,
        session_path,
        token_path,
        write_session,
    )

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
WINDOWS_HANDLER = Path(__file__).resolve().parent / "native_callback_handler.py"
MACOS_BUILD_SCRIPT = Path(__file__).resolve().parent / "macos" / "build_callback_helper.sh"
MACOS_APP = Path(__file__).resolve().parent / "macos" / "Elli OAuth Callback.app"
REGISTRY_KEY = r"Software\Classes\com.elli.ios.emsp"


def windows_open_command(python_executable: str, handler_script: Path) -> str:
    """Create the correctly quoted HKCU URL-handler command."""

    def quote(value: str) -> str:
        if '"' in value:
            raise HarnessError("Windows handler paths cannot contain a quote")
        return f'"{value}"'

    return f'{quote(python_executable)} {quote(str(handler_script))} "%1"'


def _read_windows_handler() -> str | None:
    if sys.platform != "win32":
        return None
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY + r"\shell\open\command") as key:
            value, _ = winreg.QueryValueEx(key, None)
            return str(value)
    except FileNotFoundError:
        return None


def install_windows_handler(force: bool = False, input_fn: Callable[[str], str] = input) -> None:
    """Register the current interpreter and handler for the current Windows user."""
    if sys.platform != "win32":
        raise HarnessError("install-handler is available only on Windows")
    import winreg

    desired = windows_open_command(sys.executable, WINDOWS_HANDLER)
    current = _read_windows_handler()
    if current == desired:
        print("Windows URL handler is already installed for this interpreter.")
        return
    if current is not None:
        print(f"Existing registration: {current}")
        if not force and input_fn("Replace this current-user registration? [y/N] ").strip().lower() != "y":
            raise HarnessError("Existing URL handler was not changed")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY) as key:
        winreg.SetValueEx(key, None, 0, winreg.REG_SZ, "URL:elli-client developer OAuth callback")
        winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY + r"\DefaultIcon") as key:
        winreg.SetValueEx(key, None, 0, winreg.REG_SZ, sys.executable)
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY + r"\shell\open\command") as key:
        winreg.SetValueEx(key, None, 0, winreg.REG_SZ, desired)
    print("Installed current-user URL handler for com.elli.ios.emsp.")


def uninstall_windows_handler(force: bool = False, input_fn: Callable[[str], str] = input) -> None:
    """Remove only this harness's current-user registration unless explicitly forced."""
    if sys.platform != "win32":
        raise HarnessError("uninstall-handler is available only on Windows")
    import winreg

    current = _read_windows_handler()
    if current is None:
        print("No current-user URL handler is installed.")
        return
    desired = windows_open_command(sys.executable, WINDOWS_HANDLER)
    print(f"Current registration: {current}")
    if current != desired and not force:
        raise HarnessError("Registration belongs to another handler; use --force to remove it")
    if not force and input_fn("Remove this current-user registration? [y/N] ").strip().lower() != "y":
        raise HarnessError("URL handler was not removed")
    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY + r"\shell\open\command")
    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY + r"\shell\open")
    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY + r"\shell")
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY + r"\DefaultIcon")
    except FileNotFoundError:
        pass
    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY)
    print("Removed current-user URL handler.")


def handler_installed(platform_name: str | None = None) -> bool:
    platform_name = platform_name or sys.platform
    if platform_name == "darwin":
        return MACOS_APP.exists()
    if platform_name == "win32":
        return _read_windows_handler() is not None
    return False


def print_status(
    data_directory: Path,
    platform_name: str | None = None,
    output: TextIO = sys.stdout,
) -> None:
    """Print boolean-only state; never print stored credential values."""
    platform_name = platform_name or sys.platform
    stored_tokens: TokenResponse | None = None
    tokens_file = token_path(data_directory)
    if tokens_file.exists():
        try:
            stored_tokens = load_tokens(tokens_file)
        except HarnessError:
            pass
    values = {
        "Platform": platform_name,
        "Handler installed": handler_installed(platform_name),
        "Session file present": session_path(data_directory).exists(),
        "Token file present": tokens_file.exists(),
        "Access token present": bool(stored_tokens and stored_tokens.access_token),
        "Refresh token present": bool(stored_tokens and stored_tokens.refresh_token),
    }
    for label, value in values.items():
        rendered = value if isinstance(value, str) else ("yes" if value else "no")
        print(f"{label}: {rendered}", file=output)


def setup_handler(force: bool = False) -> None:
    if sys.platform == "darwin":
        subprocess.run([str(MACOS_BUILD_SCRIPT)], cwd=REPOSITORY_ROOT, check=True)
        print("Built and registered the macOS callback helper.")
    elif sys.platform == "win32":
        install_windows_handler(force=force)
    else:
        raise HarnessError("This harness supports only macOS and Windows")


def _parse_timestamp(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def run_read_only_test(client: ElliAPIClient) -> None:
    """Exercise only existing public read-only Elli API methods."""
    stations = client.get_stations()
    print(f"Stations returned: {len(stations)}")
    for station in stations:
        connection = next(
            (
                str(getattr(station, attribute))
                for attribute in ("connection_status", "connectivity_status", "status")
                if getattr(station, attribute, None) is not None
            ),
            "unknown",
        )
        print(f"Station: {station.name}; connection status: {connection}")

    sessions = client.get_charging_sessions(include_momentary_speed=False)
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    recent_sessions = [
        session
        for session in sessions
        if (timestamp := _parse_timestamp(session.start_date_time)) is not None and timestamp >= cutoff
    ]
    print(f"Charging sessions in the last 30 days: {len(recent_sessions)}")


def login(data_directory: Path, timeout: float = CALLBACK_TIMEOUT_SECONDS) -> None:
    listener = create_listener()
    ipc_session = create_ipc_session(listener)
    current_session_path = session_path(data_directory)
    write_session(current_session_path, ipc_session)
    try:
        with ElliAPIClient() as client:
            authorization = client.create_authorization()
            print("Opening Elli authorization in the system browser...")
            if not webbrowser.open(authorization.authorization_url):
                raise HarnessError("The system browser could not be opened")
            callback_url = receive_callback(listener, ipc_session.secret, timeout)
            print("OAuth callback received.")
            tokens = client.exchange_callback(callback_url, authorization)
            save_tokens(token_path(data_directory), tokens)
            client.set_tokens(tokens)
            print("Login successful.")
            run_read_only_test(client)
    finally:
        listener.close()
        delete_session(current_session_path)


def refresh(data_directory: Path) -> None:
    path = token_path(data_directory)
    previous = load_tokens(path)
    if not previous.refresh_token:
        raise ReauthenticationRequired("Stored tokens do not contain a refresh token")
    with ElliAPIClient() as client:
        refreshed = merge_refresh_token(previous, client.refresh(previous.refresh_token))
        save_tokens(path, refreshed)
        client.set_tokens(refreshed)
        print("Token refresh successful.")
        run_read_only_test(client)


def test_existing_tokens(data_directory: Path) -> None:
    path = token_path(data_directory)
    tokens = load_tokens(path)
    now = datetime.now(timezone.utc)
    if tokens.expires_at is not None and tokens.expires_at.astimezone(timezone.utc) <= now + timedelta(seconds=60):
        if not tokens.refresh_token:
            raise ReauthenticationRequired("Stored access token expired and no refresh token is available")
        with ElliAPIClient() as refresh_client:
            tokens = merge_refresh_token(tokens, refresh_client.refresh(tokens.refresh_token))
            save_tokens(path, tokens)
            print("Expired access token refreshed.")
    with ElliAPIClient() as client:
        client.set_tokens(tokens)
        run_read_only_test(client)


def cleanup(data_directory: Path, delete_tokens: bool = False) -> None:
    delete_session(session_path(data_directory))
    if data_directory.exists():
        for temporary in data_directory.glob(".*.tmp"):
            temporary.unlink(missing_ok=True)
    if delete_tokens:
        token_path(data_directory).unlink(missing_ok=True)
        print("Removed session, temporary files, and developer tokens.")
    else:
        print("Removed session and temporary files; developer tokens were retained.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    setup = commands.add_parser("setup", help="build/register the platform callback handler")
    setup.add_argument("--force", action="store_true", help="replace an existing Windows registration")
    commands.add_parser("login", help="run interactive browser login and read-only API checks")
    commands.add_parser("refresh", help="refresh stored tokens and run read-only API checks")
    commands.add_parser("test", help="run read-only API checks with stored tokens")
    commands.add_parser("status", help="show handler/session/token presence without values")
    cleanup_parser = commands.add_parser("cleanup", help="remove transient harness state")
    cleanup_parser.add_argument("--tokens", action="store_true", help="also remove stored developer tokens")
    install = commands.add_parser("install-handler", help="install the Windows current-user handler")
    install.add_argument("--force", action="store_true", help="replace an existing registration")
    uninstall = commands.add_parser("uninstall-handler", help="remove the Windows current-user handler")
    uninstall.add_argument("--force", action="store_true", help="remove even if it belongs to another command")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        data_directory = app_data_directory()
        if arguments.command == "setup":
            setup_handler(force=arguments.force)
        elif arguments.command == "install-handler":
            install_windows_handler(force=arguments.force)
        elif arguments.command == "uninstall-handler":
            uninstall_windows_handler(force=arguments.force)
        elif arguments.command == "login":
            login(data_directory)
        elif arguments.command == "refresh":
            refresh(data_directory)
        elif arguments.command == "test":
            test_existing_tokens(data_directory)
        elif arguments.command == "status":
            print_status(data_directory)
        elif arguments.command == "cleanup":
            cleanup(data_directory, delete_tokens=arguments.tokens)
    except (HarnessError, ReauthenticationRequired, subprocess.CalledProcessError) as exc:
        print(f"Harness failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
