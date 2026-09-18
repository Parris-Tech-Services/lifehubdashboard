#!/usr/bin/env python3
"""Build a lightweight search index for Copilot/command palette."""

from __future__ import annotations

import json
import os
import re
from html import unescape
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "search-index.json"
TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".rtf",
    ".csv",
    ".tsv",
    ".json",
    ".yaml",
    ".yml",
    ".ini",
    ".cfg",
    ".conf",
    ".log",
    ".tex",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".html",
    ".css",
    ".scss",
    ".sh",
    ".zsh",
    ".fish",
    ".bat",
    ".ps1",
    ".sql",
    ".rst",
}
MAX_SNIPPET_CHARS = 400
MAX_FILE_SIZE = 512 * 1024  # 512 KB
SKIP_DIRS = {"Library", "node_modules", ".git", "__pycache__", ".idea", "automation/logs"}
# Footer text that only appears in files written by generate_directory_indexes.py.
# Those pages are navigation chrome, not content, and were ~half of all entries.
GENERATED_INDEX_MARKER = "scripts/generate_directory_indexes.py</code> after you add files."
HTML_SUFFIXES = {".html", ".htm"}
# Non-text files worth finding by name. Deliberately excludes build and game
# asset caches (.bin, .scache, .jar, .glsl, ...) which are not documents.
DOCUMENT_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".odt", ".rtf", ".pages",
    ".xls", ".xlsx", ".ods", ".numbers", ".csv",
    ".ppt", ".pptx", ".odp", ".key",
    ".png", ".jpg", ".jpeg", ".gif", ".heic", ".webp", ".svg",
    ".mp3", ".m4a", ".wav", ".mp4", ".mov", ".zip",
}
INDEX_ROOTS = [
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


def iter_all_files(base: Path) -> Iterable[Path]:
    """Every file under base, regardless of extension."""
    if not base.exists():
        return
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        for filename in filenames:
            if filename.startswith("."):
                continue
            path = Path(dirpath) / filename
            if path.suffix.lower() not in DOCUMENT_EXTENSIONS:
                continue
            yield path


def build_name_entry(path: Path) -> dict | None:
    """Path-only entry so non-text files (PDFs, images) stay findable by name."""
    segments = path.relative_to(ROOT).parts
    if not segments:
        return None
    try:
        modified = datetime.fromtimestamp(
            path.stat().st_mtime, tz=timezone.utc
        ).isoformat()
    except OSError:
        modified = None
    return {
        "path": "/".join(segments),
        "area": segments[0],
        "snippet": "",
        "modified": modified,
    }


def iter_text_files(base: Path) -> Iterable[Path]:
    if not base.exists():
        return
    for dirpath, dirnames, filenames in os.walk(base):
        rel_dir = Path(dirpath).relative_to(ROOT)
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        for filename in filenames:
            path = Path(dirpath) / filename
            if path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            try:
                if path.stat().st_size > MAX_FILE_SIZE:
                    continue
            except OSError:
                continue
            yield path


def is_generated_index(path: Path, text: str) -> bool:
    """True for directory listings emitted by generate_directory_indexes.py."""
    return path.name == "index.html" and GENERATED_INDEX_MARKER in text


def text_from_html(markup: str) -> str:
    """Drop scripts, styles and tags so snippets hold prose, not markup."""
    cleaned = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", markup)
    cleaned = re.sub(r"(?s)<!--.*?-->", " ", cleaned)
    cleaned = re.sub(r"(?s)<[^>]+>", " ", cleaned)
    return unescape(cleaned)


def build_entry(path: Path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    if is_generated_index(path, text):
        return None
    if path.suffix.lower() in HTML_SUFFIXES:
        text = text_from_html(text)
    snippet = " ".join(text.split())[:MAX_SNIPPET_CHARS]
    segments = path.relative_to(ROOT).parts
    area = segments[0] if segments else ""
    try:
        mtime = path.stat().st_mtime
        modified = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
    except OSError:
        modified = None
    return {
        "path": "/".join(segments),
        "area": area,
        "snippet": snippet,
        "modified": modified,
    }


def main() -> None:
    entries: list[dict] = []
    seen: set[str] = set()
    for root in INDEX_ROOTS:
        for path in iter_text_files(ROOT / root):
            entry = build_entry(path)
            if entry:
                entries.append(entry)
                seen.add(entry["path"])
    # Second pass: name-only entries so non-text files (PDFs, images, docs)
    # remain findable. Previously they were reachable only because the
    # generated directory listings happened to contain their filenames.
    for root in INDEX_ROOTS:
        for path in iter_all_files(ROOT / root):
            entry = build_name_entry(path)
            if entry and entry["path"] not in seen:
                entries.append(entry)
                seen.add(entry["path"])
    OUTPUT_PATH.write_text(json.dumps(entries, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote search index with {len(entries)} entries -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
