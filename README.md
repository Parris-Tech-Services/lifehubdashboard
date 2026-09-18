# LifeHub Structure

This folder is the single hub for everything outside of system-managed folders (Desktop, Downloads, etc.). Use the numbered areas below as the only places to look when you need to file or find something:

- **Inbox** – temporary landing zone for anything you have not categorised yet. Empty weekly.
- **Work** – employment history, contracts, job search materials, professional development certificates.
- **Family** – medical, school, therapy and support information for the family.
- **Finance** – insurance policies, bank statements, invoices and tax items.
- **Housing** – rentals, property paperwork, moving checklists.
- **Personal** – admin IDs, planning docs, wellbeing/fitness tracking.
- **Projects** – active build/code/design work. Tools for projects live under `Projects/Software/Tools`.
- **Hobbies** – games, tabletop campaigns, modding tools.
- **Media** – photos, screenshots, creative assets.
- **Templates** – boilerplate files you want to reuse.
- **Resources** – general reference docs that do not belong to a single project or year.
- **Archive/YYYY** – material that is done/closed out but needs to be kept. Store per year so the active areas stay lean.

## Filing rules
1. Start every week by sweeping `~/Downloads` into `LifeHub/Inbox`, then file from there.
2. If a file belongs to more than one area, store it once and add macOS tags (e.g. "Finance", "Health") for cross-cutting topics.
3. Move finished work to the relevant `Archive/<year>` folder at the end of each quarter.
4. Keep a short `README.md` or `index.md` inside big subfolders (Housing, Projects, etc.) so you remember the conventions for that area.
5. Back up the entire `LifeHub` folder with Time Machine or your sync service so this structure stays intact across devices.

## Dashboard widgets & refresh guide

The `dashboard.html` UI expects a few JSON feeds so each widget stays current:

- **Stats & wellbeing:** `python3 scripts/update_dashboard_stats.py` and `python3 scripts/update_welltory_summary.py`. The stats script also records folder size, Inbox trend, and backlog counts (it maintains `dashboard-stats-history.json`) so the dashboard can surface richer KPIs.
- **Agenda / reminders:** Either keep `Resources/calendar.ics` fresh (export from Calendar/Google) or let `python3 scripts/fetch_agenda_ics.py` pull a feed defined in `automation/agenda/source.json` (an example lives beside it). The dashboard also has an upload card for ad-hoc `.ics` files; reminders still come from `agenda-reminders.json`.
- **Recent files, resurface, triage seeds:** `python3 scripts/generate_recent_files.py`
- **Downloads watcher:** `python3 scripts/generate_downloads_feed.py` writes `downloads-feed.json`
- **Directory indexes:** `python3 scripts/generate_directory_indexes.py` (also run with `--path ~/Downloads --max-depth 1` for Downloads)
- **Backup status widget:** Update the timestamps in `automation/backups/status.json` (each automation run can drop a new ISO8601 value there) and run `python3 scripts/update_backup_status.py` to rewrite the `window.LIFEHUB_DATA.backups` block with real ages/notes. This script is part of `scripts/refresh_all.sh`.
- **Pyodide text games:** `python3 scripts/build_text_game_sources.py`
- **Copilot search index:** `python3 scripts/build_search_index.py` crawls the text-heavy areas so Copilot can match snippets/tags (this runs inside `scripts/refresh_all.sh`). It indexes text files with a prose snippet, plus documents (PDF, Office, images) by filename only. Generated directory listings are skipped, and HTML is stripped to text so snippets are readable.
- **Inline dashboard data:** `python3 scripts/build_dashboard_inline_data.py` snapshots the JSON/text feeds into `dashboard-inline-data.js` so `dashboard.html` works over `file://` without tripping Chrome’s CORS rules (this runs automatically via `scripts/refresh_all.sh`).

Run `scripts/refresh_all.sh` (described below) to regenerate everything in one command. See `todo.md` for long-term improvements such as wiring automations directly into the dashboard.

## Serving the dashboard locally

Several widgets (Pyodide text adventures, Downloads watcher) need the page to be served over HTTP/HTTPS. From the repo root, start a lightweight server:

```sh
cd ~/LifeHub
python3 -m http.server 8765
```

Then open `http://localhost:8765/dashboard.html`. Stop the server with `Ctrl+C`. You can wrap that command inside a shell script/Automator action for one-click launches.

## Helper scripts & automation

- `scripts/refresh_indexes.sh` – rebuilds every `index.html` under LifeHub plus `~/Downloads`, and syncs `directory.css` into each root.
- `scripts/refresh_all.sh` – runs all data builders (stats, Welltory, recent-files, downloads feed, indexes, text-game sources). `make refresh-all` is a shorthand.
- `python3 scripts/fetch_agenda_ics.py` – reads `automation/agenda/source.json` and refreshes `Resources/calendar.ics` from a remote/local feed (runs automatically inside `scripts/refresh_all.sh` when configured).
- `python3 scripts/build_search_index.py` – scans text-friendly files and produces `search-index.json` so Copilot/command palette can match snippets and file contents. Non-text documents are added by name so PDFs and scans stay findable. The dashboard loads this file lazily on first search; until then it uses the smaller inline index in `dashboard-inline-data.js`.
- `python3 scripts/update_backup_status.py` – merges `automation/backups/targets.json` with the actual timestamps in `automation/backups/status.json`, computes whether each backup is overdue, and rewrites the dashboard widget.
- `python3 scripts/setup_pyodide.py` – downloads the Pyodide runtime (`Resources/pyodide/`) so the embedded text adventures work offline; run this once, then refresh the dashboard.
- `make downloads` – regenerates `downloads-feed.json` for the Downloads watcher.
- `make refresh-text-games` – rebuilds the embedded Pyodide sources only (helpful after editing `scripts/fun_text_game_*.py`).
- `python3 automation/automation_server.py` – launches an HTTP runner on `http://127.0.0.1:8766/run`; start it before clicking “Run queue” so dashboard automations execute automatically.
- `python3 scripts/check_dashboard_links.py` – sanity-check that every link referenced in `dashboard-data.js` points at an existing file/folder.

### Scheduling

Sample files live under `automation/`:

- `automation/launchd/com.lifehub.refresh.plist` – copy to `~/Library/LaunchAgents/`, update the `USERNAME` placeholders, then load it via `launchctl load ~/Library/LaunchAgents/com.lifehub.refresh.plist`.
- `automation/cron/refresh_all.cron` – import with `crontab automation/cron/refresh_all.cron` after updating the path placeholders.
- `automation/launchd/com.lifehub.welltory.plist` – optional helper that runs `update_welltory_summary.py` every hour so the wellbeing widget stays current between full refreshes.
- `automation/cron/welltory.cron` – cron alternative that triggers the Welltory summary every two hours and logs to `~/Library/Logs/lifehub-welltory.log`.

Use the refresh-all samples when you want the entire dashboard rebuilt automatically, and add the Welltory-specific jobs if you’d like the wellbeing widget to update more frequently on its own.

> Tip: Most widgets (stats, wellbeing, agenda, downloads, recent files, Pyodide games) expect you to serve the dashboard via `python3 -m http.server 8765`. When opening directly via `file://`, the JSON fetches fall back to XMLHttpRequest. Run `python3 scripts/setup_pyodide.py` once to cache the Pyodide runtime locally so the games keep working offline; otherwise they’ll reach out to jsDelivr.
