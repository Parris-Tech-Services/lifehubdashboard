#!/usr/bin/env python3
"""Run simple repo checks and emit a vitals JSON for the dashboard to consume.
Produces: scripts/vitals.json
Checks:
- last_welltory_import_days
- last_ics_import_days
- downloads_stuck_count (>48h)
"""
import json
import os
import time
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WELLTORY_DIR = os.path.join(ROOT, 'Personal', 'Health', 'Welltory')
VITALS_OUT = os.path.join(os.path.dirname(__file__), 'vitals.json')

def days_since(path):
    try:
        m = os.path.getmtime(path)
        return (time.time() - m) / 86400.0
    except Exception:
        return None

def last_welltory_days():
    if not os.path.isdir(WELLTORY_DIR):
        return None
    files = [os.path.join(WELLTORY_DIR, f) for f in os.listdir(WELLTORY_DIR) if f.lower().endswith('.csv')]
    if not files:
        return None
    latest = max(files, key=os.path.getmtime)
    return days_since(latest)

def main():
    vitals = {}
    vitals['last_welltory_import_days'] = last_welltory_days()
    # naive ICS check: look for Resources/calendar.ics
    cal = os.path.join(ROOT, 'Resources', 'calendar.ics')
    vitals['last_ics_import_days'] = days_since(cal)
    # downloads stuck: count files older than 2 days in Downloads
    dl = os.path.expanduser('~/Downloads')
    stuck = 0
    try:
        for f in os.listdir(dl):
            p = os.path.join(dl, f)
            if os.path.isfile(p) and days_since(p) and days_since(p) > 2:
                stuck += 1
    except Exception:
        stuck = None
    vitals['downloads_stuck_count'] = stuck
    vitals['generated_at'] = datetime.utcnow().isoformat() + 'Z'
    with open(VITALS_OUT, 'w') as fh:
        json.dump(vitals, fh, indent=2)
    print('Wrote', VITALS_OUT)

if __name__ == '__main__':
    main()
