#!/usr/bin/env python3
"""Move a file out of ~/Downloads directly into a LifeHub area."""
from __future__ import annotations

import argparse
import base64
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS_ROOT = Path.home() / "Downloads"
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
    destination = dest_root / name
    if not destination.exists():
        return destination
    stem = destination.stem
    suffix = destination.suffix
    counter = 2
    while True:
        candidate = dest_root / f"{stem}-{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def move_download_item(source_rel: str, destination: str) -> Path:
    dest_root = DESTINATION_MAP.get(destination)
    if not dest_root:
        raise ValueError(f"Unknown destination: {destination}")
    source_path = (DOWNLOADS_ROOT / source_rel).expanduser().resolve()
    ensure_within(source_path, DOWNLOADS_ROOT.resolve())
    if not source_path.exists():
        raise FileNotFoundError(f"Download not found: {source_path}")
    dest_root.mkdir(parents=True, exist_ok=True)
    dest_root = dest_root.resolve()
    ensure_within(dest_root, ROOT)
    target_path = unique_target(dest_root, source_path.name)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source_path), str(target_path))
    return target_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Move a Downloads file into LifeHub.")
    parser.add_argument("--source", help="Relative path inside ~/Downloads (e.g., Contract.pdf)")
    parser.add_argument("--source-b64", help="Base64-encoded relative path")
    parser.add_argument("--destination", required=True, help="Destination root folder (Work, Family, etc.)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        source = decode_argument(args.source, args.source_b64)
        moved_to = move_download_item(source, args.destination)
        print(f"Moved {source} → {moved_to.relative_to(ROOT)}")
    except Exception as error:  # noqa: BLE001
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
