# LifeHub ArchitectureLifeHub architecture (high level)



## Overview- UI: Single-page dashboard built with vanilla JS (`dashboard.html`, `dashboard.js`, `dashboard.css`). The JS file contains renderers, data fetching, and UI wiring.

- Data: JSON feeds in `data/` and top-level files (recent-files.json, downloads-feed.json, etc.).

LifeHub is a **local-first, file-based personal information management system** combining:- Backend automation: Local Python scripts in `scripts/` and an automation runner (`/scripts/automation_runner.py` or similar) which listens on `127.0.0.1:8766`.

- Text games: Python scripts that can run in-node or in-browser via Pyodide (`scripts/fun_text_game_v2.py`).

1. **File Organization Framework** — Folders (Work, Finance, Personal, etc.) with filing rules- Dev/Build: Makefile with convenience targets; local http.server used for serving files during dev.

2. **Web Dashboard** — Single-page app served over HTTP with JSON-powered widgets

3. **Python Automation** — Scripts that crawl folders and generate data feedsNotes

4. **Scheduling** — launchd (macOS) or cron for periodic refreshes

- The JS is intentionally single-file for simplicity, but this favors expedience over testability.

**Not a traditional web app**: No database, no backend server. Everything lives on disk as files.- Pyodide usage is optional; a fallback to server-side Python is supported for heavier tasks.


---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    File System                              │
│  (Personal/, Work/, Finance/, Inbox/, Resources/, etc.)    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            Python Automation Scripts (scripts/)              │
│  • update_dashboard_stats.py → dashboard-stats.json         │
│  • update_welltory_summary.py → welltory-summary.json       │
│  • generate_recent_files.py → recent-files.json             │
│  • generate_downloads_feed.py → downloads-feed.json         │
│  • build_search_index.py → search-index.json                │
│  • build_text_game_sources.py → text-game-sources.js        │
│  • build_dashboard_inline_data.py → dashboard-inline-data.js│
│  • fetch_agenda_ics.py → Resources/calendar.ics             │
│  • generate_directory_indexes.py → index.html per folder    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│        JSON Feeds (*.json) + Static Files (*.ics, etc.)     │
│  (Read by dashboard.js, persisted on disk for offline mode) │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           Web Dashboard (dashboard.html)                     │
│  • Vanilla JS (no React/Vue)                                │
│  • Fetches JSON feeds dynamically                           │
│  • Renders 20+ widgets (stats, agenda, games, etc.)        │
│  • Handles offline mode (file:// protocol)                  │
│  • Calls local HTTP automation runner (127.0.0.1:8766)      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│        Scheduling (automation/launchd + cron)               │
│  • Runs refresh_all.sh every 4 hours                        │
│  • Triggers Python scripts to update JSON feeds             │
│  • Logs results for monitoring                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. **File System Layer** (`Personal/`, `Work/`, etc.)

**Responsibility**: User's organized file storage following LifeHub filing rules.

**Key directories scanned by scripts**:
- `Inbox/` — temporary landing zone (swept weekly)
- `Work/`, `Finance/`, `Family/`, `Housing/`, `Personal/`, `Projects/`, `Hobbies/`, `Media/`
- `Resources/` — shared references (calendar.ics, Pyodide runtime, NPC portraits)
- `Archive/YYYY/` — closed-out items by year
- `Downloads/` — system Downloads folder (optional scanning)

**Excluded from walks**: `.git`, `__pycache__`, `node_modules`, `.DS_Store`, `.idea`

---

### 2. **Python Automation** (`scripts/`)

**Responsibility**: Crawl folders, parse metadata, generate JSON feeds.

**Key Scripts**:

| Script | Output | Purpose |
|--------|--------|---------|
| `update_dashboard_stats.py` | `dashboard-stats.json` | Folder sizes, inbox count, trends |
| `update_welltory_summary.py` | `welltory-summary.json` | HRV/heart rate data |
| `generate_recent_files.py` | `recent-files.json` | Recently modified files |
| `generate_downloads_feed.py` | `downloads-feed.json` | Downloads folder snapshot |
| `build_search_index.py` | `search-index.json` | Full-text snippets for search |
| `fetch_agenda_ics.py` | `Resources/calendar.ics` | Calendar feed (from remote or local) |
| `generate_directory_indexes.py` | `*/index.html` | Browsable folder indexes |
| `build_text_game_sources.py` | `text-game-sources.js` | Embedded Pyodide games |
| `build_dashboard_inline_data.py` | `dashboard-inline-data.js` | Snapshot all JSON for offline mode |
| `update_backup_status.py` | Updates backup widget | Checks backup freshness |

**Pattern**:
```python
#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json

ROOT = Path(__file__).resolve().parents[1]

def _helper():
    # Logic here
    pass

def main() -> None:
    data = _helper()
    output = ROOT / "output.json"
    with output.open("w") as f:
        json.dump({"timestamp": datetime.now(timezone.utc).isoformat(), "data": data}, f)
    print(f"✓ Wrote {output}")

if __name__ == "__main__":
    main()
```

**Key Properties**:
- Idempotent (safe to run multiple times)
- Cross-platform paths (`pathlib.Path`)
- ISO 8601 timestamps in all output
- Exclude system folders automatically
- Fail gracefully (skip errors, continue)

---

### 3. **Data Feeds** (JSON + ICS files)

**Responsibility**: Intermediate format between scripts and dashboard.

**Standard JSON Schema**:
```json
{
  "timestamp": "2025-04-16T14:30:00+00:00",
  "data": { ... },
  "notes": "optional metadata"
}
```

**Examples**:
- `dashboard-stats.json`: `{ "inbox_count": 12, "folder_sizes": {...} }`
- `recent-files.json`: `{ "files": [{"path": "...", "modified": "...", ...}] }`
- `search-index.json`: `{ "index": [{"file": "...", "snippet": "..."}, ...] }`
- `Resources/calendar.ics`: Standard iCalendar format
- `text-game-sources.js`: Embedded base64-encoded Python code for Pyodide

**Offline Snapshots**:
- `dashboard-inline-data.js` — All JSON feeds concatenated (for `file://` mode)
- Generated by `build_dashboard_inline_data.py`
- Allows dashboard to work without HTTP when JSON files can't be fetched

---

### 4. **Web Dashboard** (`dashboard.html`, `dashboard.js`, `dashboard.css`)

**Responsibility**: Render widgets, fetch data, handle user interactions.

**Key Features**:
- **Vanilla JS** — No frameworks (simplicity, offline resilience)
- **20+ Widgets** — Stats, agenda, recent files, downloads, search, games, triage, backups, etc.
- **Responsive Design** — CSS grid/flexbox, theme system (Modern, Classic, Contrast, Halloween, etc.)
- **Offline Mode** — Auto-detects `file://` protocol, stubs `fetch()`, uses inline data
- **Keyboard Shortcuts** — Cmd+K search, Cmd+S save (text games), etc.
- **Local Storage** — Persistent state (focus mode, theme, text game saves)
- **Automation Runner Integration** — POSTs to `http://127.0.0.1:8766/run` for async jobs

**Files**:
- `dashboard.html` — 1993 lines, 20+ panel sections
- `dashboard.js` — 8941 lines, widget renderers + data fetching
- `dashboard.css` — Theme system + responsive layout
- `dashboard-data.js` — Hardcoded widget paths (updated by scripts)

**Widget Fetch Pattern**:
```javascript
async function renderMyWidget() {
  const data = await fetchJSON('my-widget.json');
  if (data.error) {
    document.getElementById('my-widget').textContent = 'Error';
    return;
  }
  // Render data safely with escapeHtml()
  document.getElementById('my-widget').textContent = data.data.item;
}
document.addEventListener('DOMContentLoaded', renderMyWidget);
```

**Offline Handling** (in `dashboard.js` top-level):
```javascript
if (window.location.protocol === 'file:') {
  window.LIFEHUB_OFFLINE_MODE = true;
  // Stub fetch() to return empty JSON
  // Falls back to dashboard-inline-data.js
}
```

---

### 5. **Scheduling** (`automation/`)

**Responsibility**: Run scripts periodically and log results.

**macOS (launchd)**:
- `automation/launchd/com.lifehub.refresh.plist` — Runs `scripts/refresh_all.sh` every 4 hours
- User copies to `~/Library/LaunchAgents/`, loads with `launchctl`
- Logs to `~/Library/Logs/lifehub.log`

**Linux/macOS (cron)**:
- `automation/cron/refresh_all.cron` — Runs `scripts/refresh_all.sh` via cron
- Import with `crontab automation/cron/refresh_all.cron`
- Logs to `~/Library/Logs/lifehub-cron.log`

**Local HTTP Runner** (Optional):
- `automation/automation_server.py` — Listens on `127.0.0.1:8766`
- Dashboard POSTs job requests to `/run` endpoint
- Executes whitelisted scripts and returns exit code + output

**Execution Flow**:
```
cron/launchd trigger → scripts/refresh_all.sh
  → update_dashboard_stats.py
  → update_welltory_summary.py
  → generate_recent_files.py
  → ... (10 scripts total)
  → ✓ All feeds updated
  → Dashboard auto-refreshes on next page load
```

---

## Data Flow Examples

### Example 1: Dashboard Stats Widget Refresh

1. User clicks "Refresh" or automation runs `make stats`
2. `update_dashboard_stats.py` walks `Personal/`, `Work/`, `Finance/` folders
3. Counts files, calculates sizes, records inbox age
4. Writes `dashboard-stats.json` with timestamp
5. Dashboard's `renderStatsWidget()` fetches the JSON and renders
6. If offline (`file://`), uses `dashboard-inline-data.js` instead

### Example 2: Text Game Save/Load

1. User plays `text-game-v2` in Pyodide sandbox (browser)
2. Clicks "Save" → game serializes state to JSON
3. `localStorage['textGameV2_slot1']` persists the JSON
4. On refresh, `build_dashboard_inline_data.py` snapshots the saved game
5. Game re-loads from localStorage on next play session
6. (Future: save to disk file instead of browser storage)

### Example 3: Downloads Watcher

1. User moves files into `~/Downloads`
2. `generate_downloads_feed.py` scans `~/Downloads` and indexes filenames
3. Writes `downloads-feed.json` with recent additions
4. Dashboard's `renderDownloadsWidget()` fetches JSON, shows file list with "Move to..." buttons
5. Clicking a button POSTs to `/run` on automation server
6. Server executes `scripts/move_download_item.py` (shell-safe invocation)
7. File moves to target folder (e.g., `Finance/Invoices/`)

---

## Security Model

### Input Validation

**Client-side (dashboard.js)**:
- All user input → `escapeHtml()` before DOM insertion
- JSON feeds validated for required keys (timestamp, data)
- File paths checked against whitelist in `dashboard-data.js`

**Server-side (automation_runner.py)**:
- All shell commands invoked via subprocess `args` lists (not shell=True)
- Whitelisted commands in `automation/allowed_commands.json`
- Token/API key required for runner endpoints (future enhancement)

### Data Flow Safety

1. **File reads**: Scripts use `pathlib.Path`, avoid symlink traversal
2. **JSON serialization**: All output JSON-dumped (no shell injection)
3. **HTML rendering**: `textContent` for text-only, `escapeHtml()` for HTML-safe output
4. **Offline mode**: Inline data is static, cannot be modified by network
5. **Automation runner**: Requires local HTTP + optional token validation

---

## Deployment Checklist

- [ ] Update `automation/launchd/*.plist` paths if LifeHub moved
- [ ] Run `python3 scripts/setup_pyodide.py` once to cache Pyodide runtime
- [ ] Run `make refresh-all` to generate initial JSON feeds
- [ ] Start HTTP server: `python3 -m http.server 8765`
- [ ] Load launchd plist or import cron job
- [ ] Verify first refresh runs: check logs in `~/Library/Logs/lifehub.log`
- [ ] Test offline mode: open `file:///Users/.../LifeHub/dashboard.html`

---

## Notes for Developers

- **Single-file JS**: `dashboard.js` is intentionally monolithic for simplicity; future refactor into modules for testability
- **No database**: Simplifies deployment (no migrations, no server dependencies)
- **Pyodide sandbox**: Games run in browser (no server-side Python execution)
- **Offline-first**: Prioritize `file://` mode support alongside HTTP
- **File-based state**: Easier to version control, backup, and reason about

## Root `index.html` is hand-authored

`index.html` is the dashboard itself (renamed from `dashboard.html`), not a
generated page. Two guards keep it that way:

- `scripts/generate_directory_indexes.py` writes an `index.html` into every
  directory it walks. `is_protected_index()` makes it skip any `index.html`
  that lacks the generated-footer marker, so the dashboard is never
  overwritten. Subdirectory listings still regenerate normally.
- `.gitignore` is an allowlist (`*` then `!` exceptions). It must contain
  `!index.html`; without it the dashboard is untracked and can silently
  disappear from the repo.

## Search index loading

`search-index.json` (~1MB) is not fetched at startup. `searchIndex` is seeded
from `dashboard-inline-data.js`, and the full index is fetched on first
focus/input of `#search`, then replaces the inline data.
