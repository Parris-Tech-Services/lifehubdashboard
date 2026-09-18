#!/usr/bin/env python3
"""Simple rule-applier stub for Smart Inbox.
Rules should be stored in scripts/rules.json with simple matchers.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = Path(__file__).parent / 'rules.json'

def load_rules():
    if RULES.exists():
        return json.loads(RULES.read_text())
    return []

def preview():
    rules = load_rules()
    print('Rules:', len(rules))
    # naive preview: show which files in Downloads match any rule
    dl = Path.home() / 'Downloads'
    matches = []
    for f in dl.glob('*'):
        for r in rules:
            if r.get('filename_contains') and r['filename_contains'] in f.name:
                matches.append({ 'file': str(f), 'rule': r })
    print('Preview matches:', matches[:10])

if __name__ == '__main__':
    preview()
