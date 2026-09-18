#!/bin/bash
#!/bin/bash
set -euo pipefail

echo "Installing Welltory uploader launchd job for user: $USER"

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_PLIST="$REPO_DIR/org.lifehub.welltory_uploader.plist"
DEST_PLIST="$HOME/Library/LaunchAgents/org.lifehub.welltory_uploader.plist"
VENV_HINT_FILE="$REPO_DIR/venv_detected.txt"

# Accept optional --venv /path/to/python or /path/to/venv
USER_VENV=""
if [ "$#" -ge 1 ]; then
  # allow either --venv /path or direct path
  if [ "$1" = "--venv" ] && [ -n "${2-}" ]; then
    USER_VENV="$2"
  else
    USER_VENV="$1"
  fi
fi

if [ ! -f "$SRC_PLIST" ]; then
  echo "ERROR: plist not found at $SRC_PLIST"
  exit 1
fi

# Try to detect a virtualenv python if not provided
PY_BIN=""
if [ -n "$USER_VENV" ]; then
  # if user passed a venv or python path, use it
  if [ -x "$USER_VENV" ]; then
    PY_BIN="$USER_VENV"
  elif [ -x "$USER_VENV/bin/python3" ]; then
    PY_BIN="$USER_VENV/bin/python3"
  fi
fi

if [ -z "$PY_BIN" ]; then
  # common places inside the repo
  for p in "$REPO_DIR/.venv/bin/python3" "$REPO_DIR/venv/bin/python3" "$REPO_DIR/env/bin/python3" "$HOME/.venv/bin/python3"; do
    if [ -x "$p" ]; then PY_BIN="$p"; break; fi
  done
fi

# Fallback to env python3
if [ -z "$PY_BIN" ]; then
  PY_BIN="/usr/bin/env python3"
fi

echo "Using python: $PY_BIN"

# Write a venv hint file so the dashboard can show the detected venv (non-sensitive path)
echo "$PY_BIN" > "$REPO_DIR/venv_detected.txt"

# Build a plist that uses the chosen python
TMP_PLIST="$(mktemp -t welltory_plist.XXXX).plist"
cat > "$TMP_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>org.lifehub.welltory_uploader</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PY_BIN</string>
    <string>$REPO_DIR/welltory_uploader.py</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>WorkingDirectory</key>
  <string>$REPO_DIR</string>
  <key>StandardOutPath</key>
  <string>$HOME/Library/Logs/welltory_uploader.log</string>
  <key>StandardErrorPath</key>
  <string>$HOME/Library/Logs/welltory_uploader.err.log</string>
</dict>
</plist>
EOF

mkdir -p "$HOME/Library/LaunchAgents"
cp "$TMP_PLIST" "$DEST_PLIST"
chmod 644 "$DEST_PLIST"

echo "Loading launchd job..."
# Unload first (ignore errors)
launchctl unload "$DEST_PLIST" 2>/dev/null || true
launchctl load "$DEST_PLIST"

echo "Done. The uploader should now be running on 127.0.0.1:8008 (if the script runs successfully)."
echo "Logs: $HOME/Library/Logs/welltory_uploader.log"

rm -f "$TMP_PLIST"

exit 0
