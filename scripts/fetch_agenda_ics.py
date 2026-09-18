#!/usr/bin/env python3
"""Fetch the agenda ICS feed defined in automation/agenda/source.json."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "automation/agenda/source.json"
DEST_PATH = ROOT / "Resources/calendar.ics"


def load_config():
    if not CONFIG_PATH.exists():
        print("No automation/agenda/source.json found; skipping ICS refresh.", file=sys.stderr)
        return None
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def fetch_from_url(url: str, headers: dict | None = None) -> str:
    request = urllib.request.Request(url)
    for header, value in (headers or {}).items():
        request.add_header(header, value)
    with urllib.request.urlopen(request) as response:  # noqa: S310 (user-provided URL via config)
        encoding = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(encoding)


def fetch_from_local(path: str) -> str:
    source = Path(path).expanduser()
    if not source.exists():
        raise FileNotFoundError(f"Local ICS path not found: {source}")
    return source.read_text(encoding="utf-8")


def main() -> None:
    config = load_config()
    if not config:
        return
    text = ""
    source_label = ""
    if config.get("local_path"):
        source_label = config["local_path"]
        text = fetch_from_local(config["local_path"])
    elif config.get("ics_url"):
        source_label = config["ics_url"]
        text = fetch_from_url(config["ics_url"], config.get("headers"))
    else:
        print("Config must define either 'ics_url' or 'local_path'.", file=sys.stderr)
        return
    DEST_PATH.write_text(text, encoding="utf-8")
    print(f"Updated {DEST_PATH} from {source_label}")


if __name__ == "__main__":
    main()
