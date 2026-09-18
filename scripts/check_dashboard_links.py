#!/usr/bin/env python3
"""Verify that all dashboard-data.js links resolve to local files."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "dashboard-data.js"
ALLOWED_PROTOCOLS = ("http://", "https://", "mailto:", "tel:")


def iter_paths() -> list[tuple[str, Path]]:
    text = DATA_FILE.read_text()
    matches = re.findall(r'(?:href|path|entry)\s*:\s*"([^"]+)"', text)
    results: list[tuple[str, Path]] = []
    for value in matches:
        if value.startswith(ALLOWED_PROTOCOLS):
            continue
        target = (ROOT / value).resolve()
        results.append((value, target))
    return results


def main() -> None:
    missing = [(value, path) for value, path in iter_paths() if not path.exists()]
    if not missing:
        print("All dashboard-data.js links resolve.")
        return
    print("Missing files referenced in dashboard-data.js:", file=sys.stderr)
    for value, path in missing:
        print(f" - {value} -> {path}", file=sys.stderr)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
