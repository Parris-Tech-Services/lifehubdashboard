#!/usr/bin/env python3
"""Regenerate text-game-sources.js from the canonical .py files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Tuple


ROOT = Path(__file__).resolve().parents[1]
SOURCES: Iterable[Tuple[str, Path]] = (
    ("base", ROOT / "scripts" / "fun_text_game_base.py"),
    ("v2", ROOT / "scripts" / "fun_text_game_v2.py"),
)
TARGET = ROOT / "text-game-sources.js"


def main() -> None:
    lines = [
        "// Auto-generated from scripts/fun_text_game_*.py. Update those files then rerun build_text_game_sources.py.",
        "window.LIFEHUB_GAME_SOURCES = window.LIFEHUB_GAME_SOURCES || {};",
    ]
    for key, path in SOURCES:
        text = path.read_text()
        lines.append(f"window.LIFEHUB_GAME_SOURCES.{key} = {json.dumps(text)};")
    TARGET.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
