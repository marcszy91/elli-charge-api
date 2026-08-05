#!/usr/bin/env python3
"""Short-lived OS URL handler that forwards one callback over loopback IPC."""

from __future__ import annotations

import sys

try:
    from .native_callback_common import HarnessError, app_data_directory, forward_callback, session_path
except ImportError:  # Direct execution by the operating-system URL handler.
    from native_callback_common import HarnessError, app_data_directory, forward_callback, session_path


def main() -> int:
    if len(sys.argv) != 2:
        print("Callback handler expected one URL.", file=sys.stderr)
        return 2
    try:
        forward_callback(sys.argv[1], session_path(app_data_directory()))
    except HarnessError as exc:
        print(f"Callback delivery failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
