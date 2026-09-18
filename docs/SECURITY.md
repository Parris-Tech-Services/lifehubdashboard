Security audit summary — LifeHub dashboard

Date: 2025-12-31

Summary of findings

- Multiple uses of `innerHTML` with data loaded from local files or remote endpoints. This is an XSS risk if any upstream source becomes untrusted.
- Some client-side functions build shell-like strings and POST them to a local automation runner (`http://127.0.0.1:8766/run`). If the runner executes those strings via a shell, this is a command injection/local RCE vector.
- Pyodide loader functions exist in two variants and may be instantiated more than once leading to confusing state or memory overhead.
- No explicit storage schema versioning; changes to localStorage formats could silently break upgrades.

Immediate mitigations

- Replace `innerHTML` usages with `textContent` or safe DOM insertion helpers.
- Add `escapeHtml` and `safeInsertList` helpers (see `docs/PATCHES.md`).
- On the Python automation runner side, require a token/secret, validate arguments against a whitelist, and use subprocess `args` lists instead of shell invocation.

Longer-term

- Refactor `dashboard.js` into modules, add comprehensive unit tests, and adopt a CI workflow.
- Use DOMPurify or an allowlist for any areas that must accept HTML.
