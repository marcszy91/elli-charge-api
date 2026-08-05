#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
APP_DIR="$SCRIPT_DIR/Elli OAuth Callback.app"
LSREGISTER="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"

if [ ! -d "$APP_DIR" ]; then
    echo "Callback app is missing. Run build_callback_helper.sh first." >&2
    exit 1
fi

"$LSREGISTER" -f "$APP_DIR"
if "$LSREGISTER" -dump | grep -F -q "dev.elli-client.oauth-callback"; then
    echo "Launch Services registration verified."
else
    echo "Launch Services registration could not be verified." >&2
    exit 1
fi
