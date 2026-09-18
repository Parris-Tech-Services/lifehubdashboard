#!/usr/bin/env python3
"""
Rebuild the LifeHub dashboard stats JSON by counting files inside key areas.
Run from the repo root:

    python3 LifeHub/scripts/update_dashboard_stats.py
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIFEHUB = ROOT

EXCLUDED_DIRS = {
    ".git",
    ".svn",
    "__pycache__",
    "node_modules",
    ".idea",
    ".DS_Store",
    "Library",
}


def count_files(path: Path) -> int:
    total = 0
    if not path.exists():
        return total

    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        total += len(filenames)
    return total


def folder_size(path: Path) -> int:
    total = 0
    if not path.exists():
        return total
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for filename in filenames:
            file_path = Path(dirpath) / filename
            try:
                total += file_path.stat().st_size
            except OSError:
                continue
    return total


def read_json(path: Path, default):
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        return default


def parse_timestamp(value: str):
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def compute_downloads_backlog(feed_path: Path) -> int:
    feed = read_json(feed_path, {})
    files = feed.get("files", [])
    stale = [
        file
        for file in files
        if isinstance(file, dict) and float(file.get("ageHours", 0) or 0) >= 24
    ]
    return len(stale)


def build_weekly_inbox_trend(history: list[dict], weeks: int = 4) -> list[dict]:
    """Return up to `weeks` weekly snapshots with added/cleared deltas."""
    weekly_entries: dict[tuple[int, int], tuple[datetime, int]] = {}
    for entry in history:
        timestamp = parse_timestamp(entry.get("timestamp", ""))
        stats = entry.get("stats") or {}
        if not timestamp:
            continue
        iso_year, iso_week, _ = timestamp.isocalendar()
        key = (iso_year, iso_week)
        inbox_count = int(stats.get("inboxCount") or 0)
        existing = weekly_entries.get(key)
        if not existing or existing[0] < timestamp:
            weekly_entries[key] = (timestamp, inbox_count)
    if not weekly_entries:
        return []
    ordered = sorted(weekly_entries.items(), key=lambda item: item[1][0])
    ordered = ordered[-weeks:]
    trend: list[dict] = []
    prev_count = None
    for (_, (ts, count)) in ordered:
        delta = count - prev_count if prev_count is not None else 0
        added = max(delta, 0)
        cleared = max(-delta, 0)
        trend.append(
            {
                "weekLabel": ts.strftime("%b %d"),
                "count": count,
                "added": added,
                "cleared": cleared,
            }
        )
        prev_count = count
    return trend


def main() -> None:
    downloads_backlog = compute_downloads_backlog(LIFEHUB / "downloads-feed.json")
    stats = {
        "inboxCount": count_files(LIFEHUB / "Inbox"),
        "familyHealthCount": count_files(LIFEHUB / "Family" / "Health"),
        "financeCount": count_files(LIFEHUB / "Finance"),
        "projectsCount": count_files(LIFEHUB / "Projects"),
        "housingCount": count_files(LIFEHUB / "Housing"),
        "mediaCount": count_files(LIFEHUB / "Media"),
        "archiveCount": count_files(LIFEHUB / "Archive"),
        "templatesCount": count_files(LIFEHUB / "Templates"),
    }

    stats["lifehubSizeBytes"] = folder_size(LIFEHUB)
    stats["downloadsBacklog"] = downloads_backlog
    stats["actionItemCount"] = stats["inboxCount"] + downloads_backlog

    history_path = LIFEHUB / "dashboard-stats-history.json"
    history = read_json(history_path, [])
    if not isinstance(history, list):
        history = []
    now = datetime.now(timezone.utc)
    previous_snapshot = None
    cutoff = now - timedelta(days=6)
    for entry in reversed(history):
        timestamp = parse_timestamp(entry.get("timestamp", ""))
        snapshot = entry.get("stats") or {}
        if timestamp and timestamp <= cutoff:
            previous_snapshot = snapshot
            break
    if not previous_snapshot and history:
        previous_snapshot = history[-1].get("stats") or {}
    previous_snapshot = previous_snapshot or {}
    stats["inboxWeeklyChange"] = stats["inboxCount"] - int(previous_snapshot.get("inboxCount", 0))

    history.append({"timestamp": now.isoformat(), "stats": stats})
    history = history[-40:]
    history_path.write_text(json.dumps(history, indent=2))

    stats["inboxTrend"] = build_weekly_inbox_trend(history)
    stats["generatedAt"] = now.isoformat()

    output_path = LIFEHUB / "dashboard-stats.json"
    output_path.write_text(json.dumps(stats, indent=2))
    print(f"Wrote {output_path} with {len(stats)} stats.")


if __name__ == "__main__":
    main()
