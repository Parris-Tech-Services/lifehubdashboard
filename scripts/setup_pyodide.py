#!/usr/bin/env python3
"""Download the Pyodide runtime locally for offline text-game support."""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

PYODIDE_VERSION = "0.26.4"
FILES = [
    "pyodide.js",
    "pyodide.asm.wasm",
    "pyodide.asm.data",
    "python_stdlib.zip",
    "pyodide_py.tar",
    "packages.json",
]
BASE_URL = f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE_VERSION}/full/"

ROOT = Path(__file__).resolve().parents[1]
TARGET_DIR = ROOT / "Resources" / "pyodide"


def download_file(filename: str, force: bool = False) -> None:
    url = BASE_URL + filename
    destination = TARGET_DIR / filename
    if destination.exists() and not force:
        print(f"Skipping {filename} (already exists)")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {filename}…")
    try:
        with urllib.request.urlopen(url) as response:  # noqa: S310 (official Pyodide CDN)
            destination.write_bytes(response.read())
    except OSError as error:
        print(f"Failed to download {filename}: {error}", file=sys.stderr)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Re-download files even if they already exist.")
    args = parser.parse_args()
    for filename in FILES:
        download_file(filename, force=args.force)
    manifest_path = TARGET_DIR / "VERSION"
    manifest_path.write_text(PYODIDE_VERSION, encoding="utf-8")
    print(f"Pyodide runtime stored in {TARGET_DIR}")


if __name__ == "__main__":
    main()
