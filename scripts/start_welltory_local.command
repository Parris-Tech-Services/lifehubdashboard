#!/bin/bash
# Double-click this file in Finder (or run from Terminal) to start the Welltory
# uploader and a local HTTP server and open the dashboard. Make executable first:
# chmod +x start_welltory_local.command

DIR="$(cd "$(dirname "$0")" && pwd)/.."
VENV_PY="$HOME/.venv/bin/python"

echo "Starting Welltory uploader and static server..."
nohup "$VENV_PY" "$DIR/scripts/welltory_uploader.py" >/dev/null 2>&1 &
sleep 0.5
cd "$DIR"
nohup python3 -m http.server 8080 >/dev/null 2>&1 &
sleep 0.2
open "http://127.0.0.1:8080/dashboard.html"
echo "Launched. If the dashboard doesn't open, open http://127.0.0.1:8080/dashboard.html in your browser."
