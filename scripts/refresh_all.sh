#!/usr/bin/env bash
# Run every dashboard refresh step (stats, wellbeing, recent files, indexes, text games).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Refreshing LifeHub dashboard data..."
python3 "${ROOT_DIR}/scripts/update_dashboard_stats.py"
python3 "${ROOT_DIR}/scripts/update_welltory_summary.py"
python3 "${ROOT_DIR}/scripts/generate_recent_files.py"
python3 "${ROOT_DIR}/scripts/generate_downloads_feed.py"
python3 "${ROOT_DIR}/scripts/build_search_index.py"
echo "[Agenda] Updating calendar feed (if configured)..."
python3 "${ROOT_DIR}/scripts/fetch_agenda_ics.py" || echo "Agenda fetch skipped/failed — see message above."

bash "${ROOT_DIR}/scripts/refresh_indexes.sh"

echo "[Backups] Updating dashboard backup entries..."
python3 "${ROOT_DIR}/scripts/update_backup_status.py"

echo "[Text Games] Rebuilding embedded Pyodide sources..."
python3 "${ROOT_DIR}/scripts/build_text_game_sources.py"

echo "[Dashboard] Embedding inline data for file:// mode..."
python3 "${ROOT_DIR}/scripts/build_dashboard_inline_data.py"

echo "All dashboard feeds regenerated."
