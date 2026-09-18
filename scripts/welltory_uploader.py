#!/usr/bin/env python3
"""Small local uploader for Welltory CSV exports.

Run this from the repo root (LifeHub) and open http://127.0.0.1:8008/ to upload a CSV.

The uploader saves files into Personal/Health/Welltory and runs
`scripts/update_welltory_summary.py` and `scripts/build_dashboard_inline_data.py`
so the dashboard snapshot updates immediately.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple

from flask import Flask, request, redirect, url_for, send_from_directory, render_template_string

ROOT = Path(__file__).resolve().parents[1]
WELLTORY_DIR = ROOT / "Personal" / "Health" / "Welltory"
WELLTORY_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)


def save_upload(file_storage) -> Tuple[Path, str]:
    """Save uploaded file into WELLTORY_DIR and return (path, filename)."""
    now = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    original = Path(file_storage.filename or "upload.csv").name
    # Make a safe filename: prefix with timestamp to avoid clobbering
    dest_name = f"WELLTORY_MEASUREMENT_DATA_EXPORT_{now}_{original}"
    dest = WELLTORY_DIR / dest_name
    file_storage.save(dest)
    return dest, dest_name


@app.route("/", methods=["GET"])
def index():
    # Serve a minimal upload page that posts to /upload
    html = (Path(__file__).resolve().parents[1] / "Resources" / "welltory_import.html").read_text(encoding="utf-8")
    return render_template_string(html)


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return ("No file part", 400)
    f = request.files["file"]
    if f.filename == "":
        return ("No selected file", 400)

    dest, name = save_upload(f)

    # Run the existing summarise script(s)
    try:
        subprocess.check_call([sys.executable, str(ROOT / "scripts" / "update_welltory_summary.py")])
    except subprocess.CalledProcessError as e:
        return (f"Saved {name} but failed to update summary: {e}", 500)

    try:
        subprocess.check_call([sys.executable, str(ROOT / "scripts" / "build_dashboard_inline_data.py")])
    except subprocess.CalledProcessError:
        # Non-fatal; summary is the important bit
        pass

    return redirect(url_for("result", filename=name))


@app.route("/result/<path:filename>")
def result(filename: str):
    # Show a tiny result page with links to the saved file and the summary
    saved_path = WELLTORY_DIR / filename
    summary = ROOT / "welltory-summary.json"
    html = f"""
    <!doctype html>
    <html>
      <head><meta charset="utf-8"><title>Welltory upload result</title></head>
      <body>
        <h2>Upload complete</h2>
        <p>Saved as: <a href="/files/{filename}">{filename}</a></p>
        <p>Summary: <a href="/welltory-summary.json">welltory-summary.json</a></p>
        <p><a href="/">Upload another file</a></p>
      </body>
    </html>
    """
    return html


@app.route("/files/<path:filename>")
def files(filename: str):
    return send_from_directory(WELLTORY_DIR, filename, as_attachment=False)


def main() -> None:
    # Default host/port chosen to avoid needing sudo
    print("Starting Welltory uploader at http://127.0.0.1:8008/")
    app.run(host="127.0.0.1", port=8008)


if __name__ == "__main__":
    main()
