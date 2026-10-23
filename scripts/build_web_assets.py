#!/usr/bin/env python3
"""Build browser game sources and a public-file manifest without private folders."""
import json
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / 'scripts/build_text_game_sources.py')], check=True)
paths = sorted(p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and not any(part.startswith('.') or part in ('node_modules', '__pycache__') for part in p.relative_to(ROOT).parts))
(ROOT / 'published-paths.js').write_text('window.LIFEHUB_PUBLISHED_PATHS = ' + json.dumps(paths) + ';\n')
print('Built text-game sources and public-path manifest')
