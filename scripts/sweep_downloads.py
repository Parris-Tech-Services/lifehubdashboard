#!/usr/bin/env python3
"""Move files from ~/Downloads into LifeHub/Inbox, skipping installer artifacts."""
from __future__ import annotations

import shutil
from pathlib import Path

DOWNLOADS = Path.home() / "Downloads"
LIFEHUB = Path.home() / "LifeHub"
DEST = LIFEHUB / "Inbox"
SKIP_EXT = {".dmg", ".pkg", ".iso", ".app", ".exe"}


def should_skip(path: Path) -> bool:
    if path.name.startswith("."):
        return True
    if path.suffix.lower() in SKIP_EXT:
        return True
    return False


def move_item(path: Path) -> None:
    target = DEST / path.name
    counter = 1
    while target.exists():
        target = DEST / f"{path.stem} ({counter}){path.suffix}"
        counter += 1
    if path.is_dir():
        shutil.move(str(path), target)
    else:
        target.write_bytes(path.read_bytes())
        path.unlink()
    print(f"Moved {path} -> {target}")


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    if not DOWNLOADS.exists():
        print("Downloads folder missing; nothing to do.")
        return
    moved = 0
    for item in DOWNLOADS.iterdir():
        if should_skip(item):
            continue
        move_item(item)
        moved += 1
    print(f"Swept {moved} item(s) into {DEST}")


if __name__ == "__main__":
    main()
