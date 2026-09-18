#!/usr/bin/env python3
"""Minimal automation runner stub.
Define jobs in scripts/jobs.json and run by name:
  python3 scripts/runner.py run job-name
"""
import json
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOBS_FILE = Path(__file__).parent / 'jobs.json'

def load_jobs():
    if JOBS_FILE.exists():
        return json.loads(JOBS_FILE.read_text())
    return {}

def run_job(name):
    jobs = load_jobs()
    job = jobs.get(name)
    if not job:
        print('Unknown job', name); return
    # Support either an explicit args list or a cmd string.
    cmd = job.get('cmd')
    args = job.get('args')
    if isinstance(args, list) and args:
        parts = [str(x) for x in args]
    elif isinstance(cmd, str) and cmd:
        # parse into argv safely
        parts = shlex.split(cmd)
    else:
        print('Invalid job configuration, expected "args" list or "cmd" string.');
        return

    # Safety checks: only allow running scripts that live inside the repository root
    # If invoking Python, normalize to use the current interpreter and require the script path to be inside the project.
    try:
        first = parts[0]
        exec_args = None
        if first in ("python", "python3"):
            if len(parts) < 2:
                print('Missing script to run');
                return
            script_path = Path(parts[1])
            if not script_path.is_absolute():
                script_path = ROOT / parts[1]
            script_path = script_path.resolve()
            # ensure script_path is inside project root
            if str(script_path).startswith(str(ROOT)):
                exec_args = [sys.executable, str(script_path)] + [str(x) for x in parts[2:]]
            else:
                print('Refusing to run script outside project root:', script_path)
                return
        else:
            # If the first part is a path to an executable inside the repo, allow it.
            possible = Path(first)
            if not possible.is_absolute():
                possible = ROOT / first
            possible = possible.resolve()
            if possible.exists() and str(possible).startswith(str(ROOT)):
                exec_args = [str(possible)] + [str(x) for x in parts[1:]]
            else:
                print('Refusing to run non-project executable:', first)
                return

        print('Running (safe):', exec_args)
        subprocess.run(exec_args, check=False)
    except Exception as e:
        print('Runner error:', e)

if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] != 'run':
        print('Usage: runner.py run <job-name>')
        sys.exit(1)
    run_job(sys.argv[2])
