#!/usr/bin/env python3
"""Move an Inbox file into one of the LifeHub root areas."""
from __future__ import annotations

import argparse
import base64
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INBOX_ROOT = ROOT / "Inbox"
DESTINATION_MAP = {
    "Work": ROOT / "Work",
    "Family": ROOT / "Family",
    "Finance": ROOT / "Finance",
    "Housing": ROOT / "Housing",
    "Personal": ROOT / "Personal",
    "Projects": ROOT / "Projects",
    "Hobbies": ROOT / "Hobbies",
    "Media": ROOT / "Media",
    "Archive": ROOT / "Archive",
}


def decode_argument(value: str | None, encoded: str | None) -> str:
    if encoded:
        try:
            raw = base64.b64decode(encoded).decode("utf-8")
        except Exception as error:  # noqa: BLE001
            raise ValueError(f"Failed to decode base64 argument: {error}") from error
        return raw
    if value:
        return value
    raise ValueError("Source path is required.")


def ensure_within(path: Path, parent: Path) -> None:
    try:
        path.relative_to(parent)
    except ValueError as error:
        raise ValueError(f"{path} is outside {parent}") from error


def unique_target(dest_root: Path, name: str) -> Path:
    target = dest_root / name
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    counter = 2
    while True:
        candidate = dest_root / f"{stem}-{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def move_item(source_rel: str, destination: str) -> Path:
    destination_root = DESTINATION_MAP.get(destination)
    if not destination_root:
        raise ValueError(f"Unknown destination: {destination}")
    source_path = (ROOT / source_rel).resolve()
    ensure_within(source_path, INBOX_ROOT.resolve())
    if not source_path.exists():
        raise FileNotFoundError(f"Source file does not exist: {source_path}")
    destination_root.mkdir(parents=True, exist_ok=True)
    destination_root = destination_root.resolve()
    ensure_within(destination_root, ROOT)
    target_path = unique_target(destination_root, source_path.name)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source_path), str(target_path))
    return target_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Move an Inbox file into a LifeHub destination.")
    parser.add_argument("--source", help="Relative path (e.g., Inbox/2025-07-Unsorted/file.pdf)")
    parser.add_argument("--source-b64", help="Base64-encoded relative path")
    parser.add_argument("--destination", required=True, help="Destination root folder (Work, Family, etc.)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        source = decode_argument(args.source, args.source_b64)
        target_path = move_item(source, args.destination)
        print(f"Moved {source} → {target_path.relative_to(ROOT)}")
    except Exception as error:  # noqa: BLE001
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
