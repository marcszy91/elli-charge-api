#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
APP_DIR="$SCRIPT_DIR/Elli OAuth Callback.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
HANDLER_PATH="$SCRIPT_DIR/../native_callback_handler.py"
PYTHON_BIN=${PYTHON_BIN:-$(command -v python3)}
SWIFT_CACHE_DIR=$(mktemp -d "${TMPDIR:-/tmp}/elli-oauth-swift-cache.XXXXXX")
trap 'rm -r "$SWIFT_CACHE_DIR"' EXIT HUP INT TERM

if ! command -v swiftc >/dev/null 2>&1; then
    echo "swiftc was not found. Install the Xcode Command Line Tools." >&2
    exit 1
fi

mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"
cp "$SCRIPT_DIR/Info.plist" "$CONTENTS_DIR/Info.plist"
swiftc "$SCRIPT_DIR/ElliOAuthCallback.swift" -o "$MACOS_DIR/ElliOAuthCallback" -framework AppKit -module-cache-path "$SWIFT_CACHE_DIR"
"$PYTHON_BIN" -c 'import json, pathlib, sys; pathlib.Path(sys.argv[3]).write_text(json.dumps({"python": sys.argv[1], "handler": sys.argv[2]}), encoding="utf-8")' "$PYTHON_BIN" "$HANDLER_PATH" "$RESOURCES_DIR/helper-config.json"

if [ "${ADHOC_SIGN:-0}" = "1" ]; then
    codesign --force --deep --sign - "$APP_DIR"
fi

"$SCRIPT_DIR/register_callback_helper.sh"
echo "Built: $APP_DIR"
