#!/usr/bin/env python3
"""Refresh the dashboard backup widget data."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from lib.backup_targets import (
    compute_backup_status,
    format_backups_js,
    load_backup_logs,
    load_backup_targets,
    replace_backups_block,
)

ROOT = Path(__file__).resolve().parent.parent
TARGETS_PATH = ROOT / "automation/backups/targets.json"
STATUS_PATH = ROOT / "automation/backups/status.json"
DASHBOARD_DATA_PATH = ROOT / "dashboard-data.js"


def main() -> None:
    targets = load_backup_targets(TARGETS_PATH)
    logs = load_backup_logs(STATUS_PATH)
    backups = compute_backup_status(targets, logs, now=datetime.now().astimezone())
    replacement = format_backups_js(backups)
    original = DASHBOARD_DATA_PATH.read_text(encoding="utf-8")
    updated = replace_backups_block(original, replacement)
    DASHBOARD_DATA_PATH.write_text(updated, encoding="utf-8")
    print(f"Updated backup entries for {len(backups)} targets in dashboard-data.js")


if __name__ == "__main__":
    main()
