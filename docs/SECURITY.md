Security audit summary — LifeHub dashboard

Date: 2025-12-31

Summary of findings

- Multiple uses of `innerHTML` with data loaded from local files or remote endpoints. This is an XSS risk if any upstream source becomes untrusted.
- ~~Some client-side functions build shell-like strings and POST them to a local automation runner (`http://127.0.0.1:8766/run`). If the runner executes those strings via a shell, this is a command injection/local RCE vector.~~
  **FIXED 2026-09-27** (`automation/automation_server.py`). This was a real, exploitable
  vulnerability, not theoretical: the server answered CORS preflight with
  `Access-Control-Allow-Origin: *`, and because the dashboard's requests use
  `Content-Type: application/json` (which forces a browser preflight), any
  website open in a tab while the runner was active could pass that
  preflight and POST to it. Two allowlisted commands accept attacker-shaped
  argument text (`allowArguments: true`), and the handler ran the resulting
  string via `subprocess.run(command, shell=True)` -- so an attacker-supplied
  suffix like `; touch /tmp/pwned` was interpreted by a real shell. Verified
  locally: before the fix, that suffix executed; after the fix, it arrives
  as an inert literal argv token and does nothing, and a cross-origin
  preflight from a disallowed origin now gets no `Access-Control-Allow-Origin`
  header (browser drops the follow-up POST) with a server-side 403 as a
  second layer if it's sent anyway. Fixed by (a) only granting CORS to
  requests with no Origin / `Origin: null` (what file:// pages send) or an
  explicit `http(s)://localhost|127.0.0.1[:port]` origin, and (b) removing
  `shell=True` everywhere -- every command, including the one fixed
  `&&`-joined allowlist entry, now runs as a `shlex`-parsed argv list with
  `shell=False`, so shell metacharacters in any attacker-influenced argument
  are never interpreted.
- Pyodide loader functions exist in two variants and may be instantiated more than once leading to confusing state or memory overhead.
- No explicit storage schema versioning; changes to localStorage formats could silently break upgrades.

Immediate mitigations

- Replace `innerHTML` usages with `textContent` or safe DOM insertion helpers.
- Add `escapeHtml` and `safeInsertList` helpers (see `docs/PATCHES.md`).
- ~~On the Python automation runner side, require a token/secret, validate arguments against a whitelist, and use subprocess `args` lists instead of shell invocation.~~ Done — see FIXED note above (origin restriction achieves the practical effect of a token for the browser-based attack this finding described; a token remains a reasonable defense-in-depth addition if this server is ever exposed beyond localhost).

Longer-term

- Refactor `dashboard.js` into modules, add comprehensive unit tests, and adopt a CI workflow.
- Use DOMPurify or an allowlist for any areas that must accept HTML.
