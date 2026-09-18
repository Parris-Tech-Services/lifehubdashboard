#!/usr/bin/env python3
"""Simple backup script for LifeHub: creates a tar.gz snapshot and sha256 checksum.
Usage: python3 scripts/backup.py [output-dir]
"""
import os
import sys
import tarfile
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'backups'
OUT_DIR.mkdir(parents=True, exist_ok=True)

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    ts = Path.cwd().stem
    name = f'lifehub-backup-{int(__import__("time").time())}.tar.gz'
    out = OUT_DIR / name
    with tarfile.open(out, 'w:gz') as tar:
        tar.add(ROOT, arcname='LifeHub')
    sh = sha256(out)
    with open(str(out) + '.sha256', 'w') as fh:
        fh.write(sh)
    print('Wrote', out, 'and checksum')

if __name__ == '__main__':
    main()
