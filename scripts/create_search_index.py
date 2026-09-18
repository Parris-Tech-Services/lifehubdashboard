#!/usr/bin/env python3
"""Create a simple filename->path index (stub for semantic search).
Writes scripts/search_index.json
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).parent / 'search_index.json'

def main():
    index = []
    for dirpath, dirs, files in os.walk(ROOT):
        # skip large directories
        if 'node_modules' in dirpath or '.git' in dirpath:
            continue
        for f in files:
            if f.lower().endswith(('.md','.txt','.py','.csv','.html')):
                p = os.path.join(dirpath, f)
                index.append({ 'name': f, 'path': os.path.relpath(p, ROOT) })
    OUT.write_text(json.dumps(index, indent=2))
    print('Wrote', OUT)

if __name__ == '__main__':
    main()
