# LifeHub Development Guide

## Quick Start

### Prerequisites
- macOS 10.15+ or Linux
- Python 3.8+
- Node.js 18+ (for linting/testing only)

### First-time Setup

```bash
cd ~/LifeHub

# 1. Install development dependencies
npm install

# 2. Run all tests and linters
npm test
npm run lint
npm run format

# 3. Generate all dashboard data feeds
make refresh-all

# 4. Start the dev server
python3 -m http.server 8765
# Open http://localhost:8765/dashboard.html
```

---

## Workflow by Component

### Adding a New Dashboard Widget

1. **Create the data generator** (`scripts/my_widget.py`):
   ```python
   #!/usr/bin/env python3
   """Generate my widget data."""
   
   from __future__ import annotations
   import json
   from pathlib import Path
   from datetime import datetime, timezone
   
   ROOT = Path(__file__).resolve().parents[1]
   
   def main() -> None:
       output = ROOT / "my-widget.json"
       with output.open("w", encoding="utf-8") as f:
           json.dump({
               "timestamp": datetime.now(timezone.utc).isoformat(),
               "data": {"items": []}
           }, f, indent=2)
       print(f"✓ Wrote {output}")
   
   if __name__ == "__main__":
       main()
   ```

2. **Update the Makefile**:
   ```makefile
   my-widget:
       @python3 scripts/my_widget.py
   ```

3. **Add to refresh-all.sh**:
   ```bash
   python3 "${ROOT_DIR}/scripts/my_widget.py"
   ```

4. **Add HTML element** to `dashboard.html`:
   ```html
   <section id="my-widget-panel" class="widget-panel">
     <h2>My Widget</h2>
     <div id="my-widget-content">Loading...</div>
   </section>
   ```

5. **Add fetcher in dashboard.js**:
   ```javascript
   async function renderMyWidget() {
     const data = await fetchJSON('my-widget.json');
     const container = document.getElementById('my-widget-content');
     if (data.error) {
       container.textContent = 'Error loading data';
       return;
     }
     container.innerHTML = data.data.items.map(item => 
       `<div>${escapeHtml(item.name)}</div>`
     ).join('');
   }
   
   // Add to init
   document.addEventListener('DOMContentLoaded', renderMyWidget);
   ```

---

### Editing Python Scripts

**Always follow these patterns**:
- Use `pathlib.Path` (not `os.path`)
- Exclude `.DS_Store`, `__pycache__`, `node_modules`, `.git`
- Write ISO 8601 timestamps to all JSON
- Print `✓ Wrote {file}` on success
- Use type hints with `from __future__ import annotations`

**Example refactor**:
```python
# ✗ OLD (don't do this)
import os
HOME = os.path.expanduser("~")
path = os.path.join(HOME, "LifeHub", "Inbox")

# ✓ NEW (do this)
from pathlib import Path
HOME = Path.home()
path = HOME / "LifeHub" / "Inbox"
```

---

### Editing the Dashboard UI

1. **Vanilla JS only** — no React/Vue
2. **Use `escapeHtml()` for user-controlled content**:
   ```javascript
   // ✗ UNSAFE
   container.innerHTML = `<p>${filename}</p>`;
   
   // ✓ SAFE
   container.textContent = filename;
   // OR for HTML content with sanitization:
   container.innerHTML = escapeHtml(filename);
   ```

3. **Fetch JSON data safely**:
   ```javascript
   const data = await fetchJSON('my-feed.json');
   if (data.error || !data.timestamp) {
     console.warn('Invalid feed:', data);
     return;
   }
   ```

4. **Test both online and offline modes**:
   ```bash
   # Online mode (HTTP)
   python3 -m http.server 8765
   # Open http://localhost:8765/dashboard.html
   
   # Offline mode (file://)
   # Open file:///Users/REPLACE_ME/LifeHub/dashboard.html
   ```

---

### Running Tests

```bash
# Run all tests
npm test

# Run specific test file
npm test dashboard.test.js

# Run with coverage
npm test -- --coverage

# Run linter
npm run lint

# Fix formatting
npm run format
```

---

### Debugging

#### Widget not showing data?
```bash
# 1. Check JSON file exists and is valid
cat dashboard-stats.json | python3 -m json.tool

# 2. Check fetch in browser console
curl http://localhost:8765/dashboard-stats.json

# 3. Rebuild all data
make refresh-all
```

#### Text games not loading?
```bash
# Setup Pyodide runtime once
python3 scripts/setup_pyodide.py

# Rebuild game sources
make refresh-text-games

# Serve over HTTP (not file://)
python3 -m http.server 8765
```

#### Automation never runs?
```bash
# Check if launchd job is loaded
launchctl list | grep lifehub

# View launchd logs
log stream --predicate 'process == "launchd"'

# Check cron (if using cron instead)
crontab -l
```

---

## Testing Strategy

### Unit Tests (JS)
- Helper functions: `escapeHtml()`, `parseIcsDate()`, `guessDownloadDestination()`
- Widget renderers (mocked JSON)
- Storage schema migrations

### Integration Tests
- Start http.server, fetch `dashboard.html`, verify it loads
- Verify all JSON feeds are valid and have timestamps
- Verify all widget IDs in HTML have corresponding JS handlers

### Security Tests
- Verify `innerHTML` doesn't receive unsanitized input
- Test XSS payloads in filenames and metadata
- Verify automation runner validates input before execution

---

## Deployment

### GitHub Actions
Tests run on push:
```yaml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install
      - run: npm run lint
      - run: npm test
```

### Production Refresh
```bash
# On the live machine
cd ~/LifeHub
make refresh-all
# Automation (launchd/cron) runs this periodically
```

---

## Common Patterns

### Adding a Command to Makefile
```makefile
.PHONY: new-task

new-task:
	@python3 scripts/new_task.py
```

### Adding Config File
Store in `automation/` folder as JSON:
```json
{
  "setting_name": "value",
  "enabled": true
}
```

### Adding Scheduling
1. For **macOS only**: Use `automation/launchd/com.lifehub.*.plist`
2. For **cross-platform**: Use `automation/cron/*.cron`
3. Update paths and copy to system directories
4. Test with `launchctl load` or `crontab -e`

---

## Code Quality

### Linting
```bash
npm run lint
```

Enforced by ESLint + Prettier. Format before committing:
```bash
npm run format
```

### Python Code
```bash
# Check syntax
python3 -m py_compile scripts/*.py

# Type hints (optional but encouraged)
python3 -m mypy scripts/update_dashboard_stats.py --ignore-missing-imports
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `npm test` fails | Delete `node_modules`, run `npm install` again |
| `make refresh-all` hangs | Check if any script has an infinite loop; Ctrl+C to cancel |
| JSON parse errors in dashboard | Run `python3 -m json.tool <file>` to validate |
| Offline mode doesn't work | Run `python3 scripts/build_dashboard_inline_data.py` to rebuild snapshots |
| Large inline data breaks | Use `--max-size` flag or split into separate JSON files |

---

## Next Steps

1. **Run tests**: `npm test`
2. **Start dev server**: `python3 -m http.server 8765`
3. **Edit code**: Make changes to `dashboard.js`, `dashboard.html`, or `scripts/*.py`
4. **Refresh data**: `make refresh-all`
5. **Verify in browser**: Open `http://localhost:8765/dashboard.html` and check your changes
