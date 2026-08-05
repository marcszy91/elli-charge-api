# Native OAuth callback E2E test

This developer-only harness verifies that macOS or Windows can deliver Elli's fixed custom-scheme callback to a waiting Python process. It opens the normal system browser and does not automate the login, Cloudflare Turnstile, or CAPTCHA.

It is not part of the `elli_client` package and is not a production desktop installer.

## macOS

From the repository root:

```bash
python3 -m pip install -e .
python3 scripts/test_native_callback.py setup
python3 scripts/test_native_callback.py status
python3 scripts/test_native_callback.py login
```

`setup` compiles `scripts/macos/Elli OAuth Callback.app` with `swiftc`, embeds the current Python interpreter and callback-script paths in its resources, and registers it with Launch Services. No Apple certificate is required.

The app is unsigned by default and Gatekeeper may block its first launch. If that happens, allow it once under **System Settings → Privacy & Security → Open Anyway** (German: **Datenschutz & Sicherheit → Dennoch öffnen**) and repeat `login`. This is suitable only for a local feasibility test.

To rebuild with an ad-hoc signature:

```bash
ADHOC_SIGN=1 scripts/macos/build_callback_helper.sh
```

To verify or repeat Launch Services registration independently:

```bash
scripts/macos/register_callback_helper.sh
```

The helper has no window or Dock presence. It receives the URL event, launches the shared short-lived Python forwarder, and exits.

## Windows

Run in PowerShell or Command Prompt from the repository root:

```powershell
python -m pip install -e .
python scripts/test_native_callback.py install-handler
python scripts/test_native_callback.py status
python scripts/test_native_callback.py login
```

`install-handler` writes only below:

```text
HKEY_CURRENT_USER\Software\Classes\com.elli.ios.emsp
```

No administrator rights are needed. If another handler is already registered, its command is displayed and the harness asks before replacing it. For non-interactive replacement, use `install-handler --force` only after checking the displayed registration.

Remove the registration with:

```powershell
python scripts/test_native_callback.py uninstall-handler
```

The command refuses to remove a registration belonging to another command unless `--force` is explicitly supplied.

`python scripts/test_native_callback.py setup` is an alias for platform setup and installs the same Windows handler.

## Commands

```text
python scripts/test_native_callback.py setup
python scripts/test_native_callback.py login
python scripts/test_native_callback.py refresh
python scripts/test_native_callback.py test
python scripts/test_native_callback.py status
python scripts/test_native_callback.py cleanup
```

- `login` starts the loopback listener, writes a short-lived session, opens the browser, waits up to five minutes, exchanges the automatically delivered callback, saves tokens, and executes read-only API checks.
- `refresh` refreshes stored credentials, atomically persists refresh-token rotation, and executes the checks.
- `test` uses stored tokens and refreshes them first when their calculated expiry is near or past.
- `status` reports only boolean presence of handler/session/token fields. It never prints credential values.
- `cleanup` removes session and temporary files but retains tokens. `cleanup --tokens` additionally deletes the developer token file.

## Storage locations

macOS:

```text
~/Library/Application Support/elli-client-dev/oauth-session.json
~/Library/Application Support/elli-client-dev/tokens.json
```

Windows:

```text
%LOCALAPPDATA%\elli-client-dev\oauth-session.json
%LOCALAPPDATA%\elli-client-dev\tokens.json
```

Writes are atomic. On Unix, directories use mode `0700` and files use `0600` as far as the filesystem permits. The token file is still plain JSON intended only for this developer test; do not use it as production credential storage or commit/share it.

## Security model

- The IPC listener binds only to `127.0.0.1` on a random free port.
- Every login uses a random 256-bit one-time IPC secret.
- The session file contains port, secret, UTC creation time, and process ID and expires after five minutes.
- The listener accepts exactly one connection and limits payloads to 16 KiB.
- The callback helper also rejects stale sessions and connects only to loopback.
- Scheme, host, callback path, state, and authorization code are validated by the public `elli-client` OAuth API.
- Callback URLs, authorization codes, and token values are never printed by the harness.
- Session files are removed on success, timeout, or failure.

## Read-only verification

After authentication the harness uses only public `ElliAPIClient` methods:

- `get_stations()` and station count/name output;
- `get_charging_sessions(include_momentary_speed=False)` with a local count restricted to sessions started in the last 30 days.

The current public `Station` model has no connection-status field. The harness checks common optional status attribute names defensively and prints `unknown` when the model exposes none. The charging-sessions endpoint has no public server-side date filter, so the 30-day restriction is applied locally.

## Known limitations

- This test proves local OS callback delivery only on the machine where it is run; no real Elli login runs in automated tests.
- Browser/OS URL-handler selection can be affected by another application registered for the same scheme.
- Moving the repository or changing Python interpreters requires rebuilding the macOS helper or reinstalling the Windows handler.
- The unsigned macOS app may require one-time Gatekeeper approval.
- The harness intentionally provides no production installer, secure credential vault, embedded browser, or CAPTCHA automation.

Successful output should include messages similar to:

```text
OAuth callback received.
Login successful.
Stations returned: 1
```
