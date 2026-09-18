#!/usr/bin/env python3
"""Emit downloads-feed.json for the dashboard watcher."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "downloads-feed.json"
DOWNLOADS = Path.home() / "Downloads"
SKIP_PREFIXES = {".", "._"}


def list_downloads() -> list[dict[str, object]]:
    if not DOWNLOADS.exists():
        return []
    entries = []
    now = datetime.now(timezone.utc)
    try:
        children = list(DOWNLOADS.iterdir())
    except (PermissionError, OSError):
        return []
    for child in children:
        if any(child.name.startswith(prefix) for prefix in SKIP_PREFIXES):
            continue
        try:
            stat = child.stat()
        except OSError:
            continue
        modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        age_hours = (now - modified).total_seconds() / 3600
        entries.append(
            {
                "name": child.name + ("/" if child.is_dir() else ""),
                "isDir": child.is_dir(),
                "size": stat.st_size,
                "modified": modified.isoformat(),
                "ageHours": round(age_hours, 2),
            }
        )
    return sorted(entries, key=lambda entry: entry["modified"], reverse=True)


def main() -> None:
    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "downloadsPath": str(DOWNLOADS),
        "files": list_downloads(),
    }
    OUTPUT.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {OUTPUT} ({len(payload['files'])} entries)")


if __name__ == "__main__":
    main()
