from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional

FrequencyHours = {
    "hourly": 2,
    "daily": 36,
    "weekly": 24 * 10,
    "monthly": 24 * 40,
}


def load_backup_targets(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_backup_logs(path: Path) -> Dict[str, dict]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_iso(timestamp: str) -> Optional[datetime]:
    if not timestamp:
        return None
    ts = timestamp.strip()
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def compute_backup_status(
    targets: Iterable[Mapping[str, object]],
    logs: Mapping[str, Mapping[str, object]],
    *,
    now: Optional[datetime] = None,
) -> List[dict]:
    now = (now or datetime.now().astimezone()).astimezone()
    compiled: List[dict] = []
    for target in targets:
        target_id = str(target.get("id", "")).strip()
        if not target_id:
            continue
        log_entry = logs.get(target_id, {})
        last_backup = log_entry.get("last_backup") or target.get("lastBackup")
        parsed_time = parse_iso(str(last_backup)) if last_backup else None
        max_age_hours = target.get("max_age_hours") or FrequencyHours.get(str(target.get("frequency", "")).lower())
        if not isinstance(max_age_hours, (int, float)) or math.isnan(max_age_hours):
            max_age_hours = 24
        status = "danger"
        if parsed_time:
            age_hours = (now - parsed_time).total_seconds() / 3600
            if age_hours <= max_age_hours:
                status = "ok"
            elif age_hours <= max_age_hours * 2:
                status = "warning"
            else:
                status = "danger"
        entry = {
            "id": target_id,
            "label": target.get("label"),
            "frequency": target.get("frequency"),
            "location": target.get("location"),
            "command": target.get("command"),
            "lastBackup": parsed_time.isoformat() if parsed_time else None,
            "status": log_entry.get("status") or status,
        }
        if log_entry.get("notes"):
            entry["notes"] = log_entry["notes"]
        compiled.append(entry)
    return compiled


def format_backups_js(backups: List[dict]) -> str:
    lines = ["window.LIFEHUB_DATA.backups = ["]
    for backup in backups:
        lines.append("  {")
        lines.append(f'    id: {json.dumps(backup.get("id"))},')
        lines.append(f'    label: {json.dumps(backup.get("label"))},')
        if backup.get("status"):
            lines.append(f'    status: {json.dumps(backup.get("status"))},')
        if backup.get("lastBackup"):
            lines.append(f'    lastBackup: {json.dumps(backup.get("lastBackup"))},')
        lines.append(f'    frequency: {json.dumps(backup.get("frequency"))},')
        lines.append(f'    location: {json.dumps(backup.get("location"))},')
        lines.append(f'    command: {json.dumps(backup.get("command"))},')
        if backup.get("notes"):
            lines.append(f'    notes: {json.dumps(backup.get("notes"))},')
        lines.append("  },")
    lines.append("];")
    return "\n".join(lines)


def replace_backups_block(source: str, replacement: str) -> str:
    pattern = re.compile(r"window\.LIFEHUB_DATA\.backups\s*=\s*\[(?:.|\n)*?\];", re.MULTILINE)
    if not pattern.search(source):
        raise RuntimeError("Could not locate LIFEHUB_DATA.backups block in dashboard-data.js")
    return pattern.sub(replacement, source, count=1)
