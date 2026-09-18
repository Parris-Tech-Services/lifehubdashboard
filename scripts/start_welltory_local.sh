#!/usr/bin/env bash
# Start the Welltory uploader and serve the LifeHub folder over HTTP so the
# dashboard (served via http://) can POST to the local uploader without CORS
# issues. This is macOS-friendly and uses the project's virtualenv.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)/.."
VENV_PY="$HOME/.venv/bin/python"
PORT_SERVER=8080
PORT_UPLOADER=8008

echo "Starting Welltory uploader (http://127.0.0.1:${PORT_UPLOADER}/)..."
nohup "$VENV_PY" "$REPO_ROOT/scripts/welltory_uploader.py" >/dev/null 2>&1 &

sleep 0.6
echo "Starting static server for LifeHub (http://127.0.0.1:${PORT_SERVER}/dashboard.html)..."
cd "$REPO_ROOT"
nohup python3 -m http.server ${PORT_SERVER} >/dev/null 2>&1 &

sleep 0.4
echo "Opening dashboard in default browser..."
open "http://127.0.0.1:${PORT_SERVER}/dashboard.html"

echo "Done. If the browser doesn't load, open http://127.0.0.1:${PORT_SERVER}/dashboard.html and then use the Welltory import control in the Wellbeing panel."
