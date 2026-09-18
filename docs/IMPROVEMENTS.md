# LifeHub Dashboard — Improvement Backlog

Ranked by value. Every item below was observed in the codebase, not guessed.
Measurements were taken in-browser against `python3 -m http.server`.

## 1. Split `dashboard.js` (362KB, ~9,000 lines)

One file holds the dashboard, a text adventure, a D&D toolkit, a mini
adventure engine and Groq chat. All of it parses on every load even though
most panels are never opened. Splitting the game engines into modules loaded
on panel open is the single biggest remaining win. This monolith is also why
the missing-markup bug (handlers driving elements that no longer existed)
went unnoticed for so long.

## 2. Shrink `search-index.json` further (now ~1MB)

Already cut from 1.8MB. `MAX_SNIPPET_CHARS = 400` still dominates the file.
A prebuilt inverted index (token -> paths), or dropping snippets to ~120
chars, would likely halve it again. Matching is currently a linear
`includes()` scan across every entry on each keystroke.

## 3. Lazy-load `dashboard-inline-data.js` (369KB)

Now the largest asset fetched on every load. It exists to seed search before
`search-index.json` arrives and to support `file://` mode. Over HTTP most of
it is redundant with the lazily-loaded index.

## 4. Fix `tests/test_text_game_ai_validation.js` fragility — DONE

Path now resolves via `__dirname`, and a failed regex match throws a
message explaining the scraping approach instead of a bare `TypeError`.
Exporting `maybeGroqNpcChat` properly is still the real fix.

## 5. Stop the generator escaping into nested repositories

`generate_directory_indexes.py` walks into
`Projects/Software/WhirringWilderness/` and writes LifeHub-titled
`index.html` files into that separate git repo, where seven of them are now
committed. It should skip any directory containing `.git`.

## 6. Untrack regenerable data files — PARTLY DONE

The directory listings no longer churn: `content_changed()` compares
ignoring the generated-at timestamp, so a run that changes nothing writes
nothing and leaves a clean tree. The four regenerable JSON files
(`dashboard-stats`, `recent-files`, `downloads-feed`, `welltory-summary`)
are still tracked and still churn.

<details><summary>original entry</summary>

`dashboard-stats.json`, `recent-files.json`, `downloads-feed.json` and
`welltory-summary.json` are build output but tracked, so every refresh run
dirties the tree and buries real changes in diff noise.
</details>

## 7. Investigate the skipped Jest suite — DONE

The bigger problem turned out to be three suites jest never matched at all
(`testMatch` is `tests/**/*.test.js`; they are named `test_*.js` / `test_*.py`).
One of them was failing. `npm test` now runs every suite via
`scripts/run_all_tests.sh` and fails if any one fails.

## 8. Add CI

No workflow exists. `lint`, `test`, and a search-index rebuild should run on
push. Two of the bugs fixed this week (the clobbered dashboard, dead
handlers) would have been caught by a smoke test asserting the dashboard
renders its panels.

## 9. Document and harden the Welltory dependency

The dashboard probes `http://127.0.0.1:8008/upload` on load. When the daemon
is down this logs a CORS error and previously cost ~400ms per load (now
bounded by `AbortSignal.timeout`). The daemon requirement is undocumented.

## 10. Extract the inline `<script>` blocks from `index.html`

`index.html` is 90KB and carries three inline script blocks, including the
Welltory uploader logic. They are unlintable, untestable and uncacheable.
Move them into files covered by `npm run lint`.
