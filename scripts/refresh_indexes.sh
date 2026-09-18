#!/usr/bin/env bash
# Refresh LifeHub + Downloads directory indexes and sync directory.css into each root.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOWNLOADS_DIR="${HOME}/Downloads"

echo "[LifeHub] Updating local directory indexes..."
python3 "${ROOT_DIR}/scripts/generate_directory_indexes.py"

echo "[Downloads] Updating pretty index..."
python3 "${ROOT_DIR}/scripts/generate_directory_indexes.py" --path "${DOWNLOADS_DIR}" --max-depth 1

if [[ -f "${ROOT_DIR}/directory.css" ]]; then
  cp "${ROOT_DIR}/directory.css" "${DOWNLOADS_DIR}/directory.css"
fi

mkdir -p "${ROOT_DIR}/Downloads"
if [[ -f "${DOWNLOADS_DIR}/index.html" ]]; then
  cp "${DOWNLOADS_DIR}/index.html" "${ROOT_DIR}/Downloads/index.html"
fi
if [[ -f "${DOWNLOADS_DIR}/directory.css" ]]; then
  cp "${DOWNLOADS_DIR}/directory.css" "${ROOT_DIR}/Downloads/directory.css"
fi

echo "Directory indexes refreshed for LifeHub and ${DOWNLOADS_DIR}"
