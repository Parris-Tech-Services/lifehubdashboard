#!/usr/bin/env bash
# Installs and loads the LifeHub launchd service for automatic background updates.
set -euo pipefail

USER_HOME="${HOME}"
LAUNCH_AGENTS_DIR="${USER_HOME}/Library/LaunchAgents"
TARGET_PLIST="${LAUNCH_AGENTS_DIR}/com.lifehub.refresh.plist"
LOG_DIR="${USER_HOME}/Library/Logs"

mkdir -p "${LAUNCH_AGENTS_DIR}" "${LOG_DIR}"

cat <<EOF > "${TARGET_PLIST}"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.lifehub.refresh</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>${USER_HOME}/LifeHub/scripts/refresh_all.sh</string>
  </array>
  <key>StartInterval</key>
  <integer>3600</integer>
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${LOG_DIR}/lifehub-refresh.log</string>
  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/lifehub-refresh.log</string>
</dict>
</plist>
EOF

echo "[LifeHub launchd] Wrote service file to ${TARGET_PLIST}"

# Unload previous instance if loaded
launchctl unload "${TARGET_PLIST}" 2>/dev/null || true

# Load service
if launchctl load "${TARGET_PLIST}"; then
  echo "[LifeHub launchd] Successfully loaded com.lifehub.refresh into launchd (runs every hour + on load)."
else
  echo "[LifeHub launchd] Warning: launchctl load returned code $?. Check permissions."
fi
