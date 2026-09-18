#!/usr/bin/env python3
"""
Summarise the latest Welltory export into JSON for the dashboard widget.

Run from the repo root:

    python3 LifeHub/scripts/update_welltory_summary.py
"""

from __future__ import annotations

import csv
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WELLTORY_DIR = ROOT / "Personal" / "Health" / "Welltory"
OUTPUT_FILE = ROOT / "welltory-summary.json"
HISTORY_FILE = ROOT / "welltory-history.json"
HISTORY_LIMIT = 50


def load_latest_csv() -> Path | None:
    candidates = sorted(
        WELLTORY_DIR.glob("WELLTORY_MEASUREMENT_DATA_EXPORT_*.csv"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def summarise_csv(path: Path) -> dict[str, object]:
    if not path:
        return {}

    measurements = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            # Normalize keys (remove spaces, parentheses and lower-case) so the
            # script is tolerant to minor header differences between exports.
            norm_row = { (k or "").replace(" ", "").replace("(", "").replace(")", "").replace("-", "").lower(): v for k, v in row.items() }
            measurements.append(norm_row)

    if not measurements:
        return {}

    # Helper: look up by either original field name or normalized form
    def _normalized(name: str) -> str:
        return name.replace(" ", "").replace("(", "").replace(")", "").replace("-", "").lower()

    def average(field: str) -> float:
        key = _normalized(field)
        values = [
            float(entry[key])
            for entry in measurements
            if entry.get(key) not in (None, "", "null")
        ]
        return round(sum(values) / len(values), 1) if values else 0.0

    # Try to get latest Date/Time from normalized keys; fall back to raw if needed
    latest_date = None
    if measurements:
        first = measurements[0]
        # possible normalized keys
        for k in ("date", "time"):
            if first.get(k):
                latest_date = first.get(k)
                break

    return {
        "sourceFile": path.name,
        "latestMeasurement": latest_date,
        "measurementCount": len(measurements),
        "stressAverage": average("Stress (HRV)"),
        "energyAverage": average("Energy (HRV)"),
        "focusAverage": average("Focus"),
    }


def load_history():
    try:
        return json.loads(HISTORY_FILE.read_text())
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def write_history(entries):
    HISTORY_FILE.write_text(json.dumps(entries[-HISTORY_LIMIT:], indent=2))


def compute_deltas(current: dict, previous: dict | None) -> dict:
    if not previous:
        return {}

    def diff(key: str, precision: int = 1):
        cur_val = current.get(key)
        prev_val = previous.get(key)
        if cur_val is None or prev_val is None:
            return None
        try:
            value = float(cur_val) - float(prev_val)
            return round(value, precision)
        except (TypeError, ValueError):
            return None

    return {
        "stress": diff("stressAverage"),
        "energy": diff("energyAverage"),
        "focus": diff("focusAverage"),
        "measurementCount": diff("measurementCount", precision=0),
    }


def main() -> None:
    latest_csv = load_latest_csv()
    summary = summarise_csv(latest_csv)
    if not summary:
        print("No Welltory export found to summarise.")
        return

    history = load_history()
    previous_summary = history[-1]["summary"] if history else None
    prev_snapshot = previous_summary if isinstance(previous_summary, dict) else None
    summary["previousMeasurement"] = prev_snapshot.get("latestMeasurement") if prev_snapshot else None
    summary["deltas"] = compute_deltas(summary, prev_snapshot)
    summary["updatedAt"] = datetime.now(timezone.utc).isoformat()

    OUTPUT_FILE.write_text(json.dumps(summary, indent=2))

    history.append({"timestamp": summary["updatedAt"], "summary": deepcopy(summary)})
    write_history(history)

    print(f"Wrote {OUTPUT_FILE} with {summary.get('measurementCount', 0)} measurements.")


if __name__ == "__main__":
    main()
