#!/usr/bin/env bash
# Lightweight helper to launch the Welltory uploader in the background.
# This is used by the automation runner so the dashboard can auto-start the service.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PORT_UPLOADER=8008
LOG_DIR="${ROOT_DIR}/automation/logs"
LOG_FILE="${LOG_DIR}/welltory_uploader.log"

mkdir -p "${LOG_DIR}"

# Exit early if the uploader already listens on the expected port.
if lsof -iTCP:${PORT_UPLOADER} -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Welltory uploader already running on port ${PORT_UPLOADER}."
  exit 0
fi

cd "${ROOT_DIR}"
echo "[$(date -Iseconds)] Starting Welltory uploader via start_welltory_daemon.sh" >> "${LOG_FILE}"
nohup python3 "${ROOT_DIR}/scripts/welltory_uploader.py" >> "${LOG_FILE}" 2>&1 &
UP_PID=$!
disown || true
echo "${UP_PID}" > "${LOG_DIR}/welltory_uploader.pid"

sleep 1
if lsof -iTCP:${PORT_UPLOADER} -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Started Welltory uploader (PID ${UP_PID}) on port ${PORT_UPLOADER}."
  exit 0
fi

echo "Failed to confirm Welltory uploader startup. Check ${LOG_FILE} for details."
exit 1
