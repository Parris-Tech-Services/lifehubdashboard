#!/usr/bin/env python3
"""Generate pretty index.html files for every LifeHub directory."""
from __future__ import annotations

import argparse
import os
import re
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT = SCRIPT_DIR.parent
TARGET_ROOT = DEFAULT_ROOT
CSS_NAME = "directory.css"
CSS_SOURCE = DEFAULT_ROOT / CSS_NAME
TITLE_PREFIX_DEFAULT = "LifeHub"
TITLE_LABEL = TITLE_PREFIX_DEFAULT
SKIP_DIR_NAMES = {".git", "node_modules", "__pycache__"}
SKIP_DIR_SUFFIXES = (".app", ".bundle")
SKIP_FILE_NAMES = {"index.html"}
# Footer text present only in files this script generates; used to avoid
# overwriting a hand-authored index.html (e.g. the root dashboard).
GENERATED_MARKER = "scripts/generate_directory_indexes.py</code> after you add files."
MAX_DEPTH_DEFAULT = 3
MAX_DEPTH = MAX_DEPTH_DEFAULT
DEFAULT_CSS_CONTENT = """
:root {
  font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  color-scheme: light dark;
  --color-bg: #f5f5f7;
  --color-card: #ffffff;
  --color-text: #0f172a;
  --color-muted: #475569;
  --color-border: rgba(15, 23, 42, 0.08);
  --color-accent: #2563eb;
}
body {
  margin: 0;
  padding: 2rem clamp(1rem, 5vw, 4rem);
  background: var(--color-bg);
  color: var(--color-text);
}
"""

TEMPLATE = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{title}</title>
  <link rel=\"stylesheet\" href=\"{css_path}\" />
</head>
<body>
  <header>
    <div>
      <h1>{title}</h1>
      <p>{intro}</p>
    </div>
  </header>
  <nav class=\"breadcrumb\">{breadcrumb}</nav>
  <section class=\"directory-showcase\">
    <h2>Subfolders</h2>
    {gallery}
  </section>
  <section class=\"file-section\">
    <h2>Files</h2>
    {file_table}
  </section>
  <footer>Generated {generated_at} · Run <code>python3 scripts/generate_directory_indexes.py</code> after you add files.</footer>
</body>
</html>
"""

ROW_TEMPLATE = "<tr><td class=\"name\"><a href=\"{href}\">{label}</a></td><td>{size}</td><td>{modified}</td></tr>"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
BREADCRUMB_LINK = "<a href=\"{href}\">{label}</a>"
CARD_TEMPLATE = """
<article class=\"directory-card\" style=\"--accent-hue: {accent}\">
  {hero}
  <header>
    <span class=\"directory-chip\">{label}</span>
    <time datetime=\"{modified_iso}\">{modified}</time>
  </header>
  <h3><a href=\"{href}\">{title}</a></h3>
  <p>{summary}</p>
  <ul class=\"directory-preview\">
    {preview}
  </ul>
</article>
""".strip()


def human_size(size: int) -> str:
    if size <= 0:
        return "—"
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    idx = 0
    while value >= 1024 and idx < len(units) - 1:
        value /= 1024
        idx += 1
    return f"{value:.1f} {units[idx]}"


def format_mtime(path: Path) -> str:
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return "—"
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")


def format_mtime_iso(path: Path) -> str:
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return ""
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%dT%H:%M:%S")


def compute_css_path(directory: Path) -> str:
    css_path = TARGET_ROOT / CSS_NAME
    rel = os.path.relpath(css_path, directory)
    return Path(rel).as_posix()


def build_breadcrumb(directory: Path) -> str:
    parts = []
    current = directory
    while True:
        parts.append((current.name or TITLE_LABEL, current))
        if current == TARGET_ROOT:
            break
        current = current.parent
    parts = list(reversed(parts))
    links = []
    for name, path in parts:
        rel = os.path.relpath(path, directory)
        href = Path(rel).as_posix() or "."
        links.append(BREADCRUMB_LINK.format(href=href, label=name or TITLE_LABEL))
    return " / ".join(links)


def build_directory_gallery(directory: Path) -> str:
    cards = []
    for idx, child in enumerate(sorted(directory.iterdir(), key=lambda p: p.name.lower())):
        if not child.is_dir():
            continue
        if child.name in SKIP_DIR_NAMES or child.suffix in SKIP_DIR_SUFFIXES:
            continue
        cards.append(render_directory_card(child, idx, directory))
    if not cards:
        return "<p class=\"empty\">No subfolders yet.</p>"
    return "<div class=\"directory-grid\">" + "\n".join(cards) + "</div>"


def render_directory_card(child: Path, index: int, parent: Path) -> str:
    href = f"{child.name}/"
    summary = summarize_directory(child)
    preview = "\n    ".join(f"<li>{item}</li>" for item in preview_items(child) or ["Empty folder"])
    modified = format_mtime(child)
    modified_iso = format_mtime_iso(child)
    hero = build_directory_hero(child, parent)
    return CARD_TEMPLATE.format(
        accent=accent_from_name(child.name),
        label=f"{summary['count']} items",
        modified=modified,
        modified_iso=modified_iso,
        href=href,
        title=child.name,
        summary=summary["label"],
        preview=preview,
        hero=hero,
    )


def preview_items(child: Path) -> list[str]:
    previews: list[str] = []
    try:
        for entry in sorted(child.iterdir(), key=lambda p: p.name.lower()):
            if entry.name in SKIP_FILE_NAMES:
                continue
            suffix = "/" if entry.is_dir() else ""
            previews.append(entry.name + suffix)
            if len(previews) >= 3:
                break
    except OSError:
        return []
    return previews


def find_preview_image(directory: Path, depth: int = 0, max_depth: int = 2) -> Path | None:
    try:
        entries = sorted(directory.iterdir(), key=lambda p: p.name.lower())
    except OSError:
        return None
    for entry in entries:
        if entry.is_file() and entry.suffix.lower() in IMAGE_EXTENSIONS:
            return entry
    if depth >= max_depth:
        return None
    for entry in entries:
        if entry.is_dir():
            candidate = find_preview_image(entry, depth + 1, max_depth)
            if candidate:
                return candidate
    return None


def build_directory_hero(child: Path, parent: Path) -> str:
    image = find_preview_image(child)
    if not image:
        return "<div class=\"directory-hero placeholder\"></div>"
    rel = os.path.relpath(image, parent)
    rel_path = Path(rel).as_posix()
    return f'<div class="directory-hero" style="background-image:url(\'{rel_path}\');"></div>'


def summarize_directory(child: Path) -> dict[str, str]:
    try:
        entries = [entry for entry in child.iterdir() if entry.name not in SKIP_FILE_NAMES]
    except OSError:
        entries = []
    count = len(entries)
    label = f"{count} item{'s' if count != 1 else ''}"
    if entries:
        latest = max(entries, key=lambda entry: entry.stat().st_mtime)
        label += f" · Updated {format_mtime(latest)}"
    else:
        label += " · Start filling it!"
    return {"count": count, "label": label}


def accent_from_name(name: str) -> int:
    value = sum(ord(char) for char in name)
    return value % 360


def build_file_table(directory: Path) -> str:
    rows = []
    parent = directory.parent if directory != TARGET_ROOT else None
    if parent is not None:
        href = Path(os.path.relpath(parent, directory) + "/").as_posix()
        rows.append(ROW_TEMPLATE.format(href=href, label="← Parent directory", size="—", modified=""))
    for child in sorted(directory.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_file():
            continue
        if child.name in SKIP_FILE_NAMES:
            continue
        try:
            stat = child.stat()
        except OSError:
            stat = None
        size = "—" if stat is None else human_size(stat.st_size)
        modified = format_mtime(child)
        iso = format_mtime_iso(child)
        modified_cell = f"<time datetime=\"{iso}\">{modified}</time>" if iso else modified
        rows.append(ROW_TEMPLATE.format(href=child.name, label=child.name, size=size, modified=modified_cell))
    if not rows:
        return "<p class=\"empty\">No files yet.</p>"
    table = """
    <table>
      <thead>
        <tr><th>Name</th><th>Size</th><th>Modified</th></tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
    """.strip()
    return table.format(rows="\n        ".join(rows))


def is_nested_repo(directory: Path) -> bool:
    """True for a directory that is its own git repo (and not TARGET_ROOT).

    Without this the walker writes LifeHub-titled listings into nested
    projects such as Projects/Software/WhirringWilderness, where they were
    committed to that project's history and clobbered its Vite entry point.
    """
    current = directory
    while current != TARGET_ROOT and TARGET_ROOT in current.parents:
        if (current / ".git").exists():
            return True
        current = current.parent
    return False


def should_skip(directory: Path) -> bool:
    if is_nested_repo(directory):
        return True
    parts = directory.parts
    if any(part in SKIP_DIR_NAMES for part in parts):
        return True
    if any(part.endswith(suffix) for suffix in SKIP_DIR_SUFFIXES for part in parts):
        return True
    return False


def ensure_css(root: Path) -> None:
    target = root / CSS_NAME
    if target.exists():
        return
    if CSS_SOURCE.exists():
        target.write_text(CSS_SOURCE.read_text())
    else:
        target.write_text(DEFAULT_CSS_CONTENT.strip())


def parse_args():
    parser = argparse.ArgumentParser(description="Generate pretty index files for directories.")
    parser.add_argument("--path", type=str, help="Root directory to index (defaults to LifeHub)")
    parser.add_argument(
        "--max-depth",
        type=int,
        default=MAX_DEPTH_DEFAULT,
        help="Maximum folder depth (relative to root) to generate indexes for",
    )
    return parser.parse_args()


def is_protected_index(path: Path) -> bool:
    """True if index.html is hand-authored rather than generated by this script.

    The root index.html is the LifeHub dashboard (renamed from dashboard.html).
    Without this guard a generator run replaces it with a directory listing.
    """
    if not path.exists():
        return False
    try:
        return GENERATED_MARKER not in path.read_text(encoding="utf-8")
    except OSError:
        return True


def strip_generated_at(html: str) -> str:
    """Drop the generated-at timestamp so it alone does not count as a change."""
    return re.sub(r"Generated \d{4}-\d{2}-\d{2} \d{2}:\d{2}", "Generated", html)


def content_changed(path: Path, html: str) -> bool:
    """True unless the only difference is the generated-at timestamp.

    Rewriting every listing on every run dirtied a dozen tracked files and
    buried real changes in diff noise.
    """
    if not path.exists():
        return True
    try:
        return strip_generated_at(path.read_text(encoding="utf-8")) != strip_generated_at(html)
    except OSError:
        return True


def main() -> None:
    global TARGET_ROOT, MAX_DEPTH, TITLE_LABEL
    args = parse_args()
    root = Path(args.path).expanduser().resolve() if args.path else DEFAULT_ROOT
    TARGET_ROOT = root
    MAX_DEPTH = max(0, args.max_depth)
    TITLE_LABEL = root.name or TITLE_PREFIX_DEFAULT
    ensure_css(root)

    directories = [root] + [p for p in root.rglob("*") if p.is_dir()]
    for directory in directories:
        if should_skip(directory):
            continue
        relative = directory.relative_to(root)
        if len(relative.parts) > MAX_DEPTH:
            continue
        css_path = compute_css_path(directory)
        title = f"{TITLE_LABEL} / {relative}" if relative.parts else TITLE_LABEL
        intro = f"Pretty index for your {TITLE_LABEL} folder."
        html = TEMPLATE.format(
            title=title,
            intro=intro,
            breadcrumb=build_breadcrumb(directory),
            gallery=build_directory_gallery(directory),
            file_table=build_file_table(directory),
            css_path=css_path,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )
        index_path = directory / "index.html"
        if is_protected_index(index_path):
            print(f"Skipping hand-authored index: {index_path}")
            continue
        if not content_changed(index_path, html):
            continue
        try:
            index_path.write_text(html, encoding="utf-8")
            print(f"Updated {directory}")
        except PermissionError:
            print(f"Skipping unwritable directory: {directory}")


if __name__ == "__main__":
    main()
