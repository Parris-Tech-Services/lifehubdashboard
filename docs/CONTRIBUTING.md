Contributing guide (quick)

- Run linters and tests before opening PRs.
- Keep changes small and focused; prefer to open follow-up PRs for larger refactors.
- When editing `dashboard.js`, run the local smoke test (start http.server and open `dashboard.html`).
- Security-sensitive changes should include unit tests demonstrating the fix and a short rationale in the PR description.

Branching

- Use feature branches. PRs should target `main`.

Commit messages

- Use concise, present-tense messages (e.g., "Add escapeHtml helper and replace innerHTML usage in recent files list").
