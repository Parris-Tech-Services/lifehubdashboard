#!/usr/bin/env python3
"""Scan LifeHub areas and produce recent-files.json for dashboard widgets."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "recent-files.json"
AREAS = [
    "Inbox",
    "Work",
    "Family",
    "Finance",
    "Housing",
    "Personal",
    "Projects",
    "Hobbies",
    "Media",
    "Templates",
    "Resources",
    "Archive",
]
MAX_ITEMS = 12
SKIP_NAMES = {".DS_Store", "index.html"}


def list_recent(area: str) -> list[dict]:
    base = ROOT / area
    if not base.exists():
        return []
    entries: list[tuple[float, Path]] = []
    for file_path in base.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.name in SKIP_NAMES:
            continue
        try:
            mtime = file_path.stat().st_mtime
        except OSError:
            continue
        entries.append((mtime, file_path))
    entries.sort(reverse=True)
    now = datetime.now(timezone.utc)
    recent = []
    for mtime, file_path in entries[:MAX_ITEMS]:
        modified = datetime.fromtimestamp(mtime, tz=timezone.utc)
        recent.append(
            {
                "path": str(file_path.relative_to(ROOT)),
                "modified": modified.isoformat(),
                "ageDays": round((now - modified).total_seconds() / 86400, 1),
            }
        )
    return recent


def main() -> None:
    payload = {area: list_recent(area) for area in AREAS}
    payload["generatedAt"] = datetime.now(timezone.utc).isoformat()
    OUTPUT.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
