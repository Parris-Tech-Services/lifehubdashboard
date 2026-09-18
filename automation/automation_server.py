#!/usr/bin/env python3
"""Simple HTTP runner that executes LifeHub automation commands."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "automation" / "logs"
HISTORY_FILE = LOG_DIR / "history.json"
ALLOWED_COMMANDS_FILE = ROOT / "automation" / "allowed_commands.json"
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8766


@dataclass
class AllowedCommand:
    command: str
    allow_arguments: bool = False

    def matches(self, candidate: str) -> bool:
        candidate = candidate.strip()
        if self.allow_arguments:
            return candidate == self.command or candidate.startswith(f"{self.command} ")
        return candidate == self.command


def load_allowed_commands() -> list[AllowedCommand]:
    if not ALLOWED_COMMANDS_FILE.exists():
        return []
    try:
        commands = json.loads(ALLOWED_COMMANDS_FILE.read_text())
    except json.JSONDecodeError:
        return []
    parsed: list[AllowedCommand] = []
    for entry in commands:
        if isinstance(entry, str):
            value = entry.strip()
            if value:
                parsed.append(AllowedCommand(value, False))
            continue
        if isinstance(entry, dict):
            value = str(entry.get("command", "")).strip()
            if value:
                parsed.append(AllowedCommand(value, bool(entry.get("allowArguments"))))
    return parsed


def ensure_history_file() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text("[]\n")


def read_history() -> list[dict[str, Any]]:
    ensure_history_file()
    try:
        return json.loads(HISTORY_FILE.read_text())
    except json.JSONDecodeError:
        return []


def write_history(runs: list[dict[str, Any]]) -> None:
    ensure_history_file()
    HISTORY_FILE.write_text(json.dumps(runs, indent=2))


def append_history(new_runs: list[dict[str, Any]]) -> None:
    history = new_runs + read_history()
    history = history[:100]
    write_history(history)


class AutomationHandler(BaseHTTPRequestHandler):
    server_version = "LifeHubAutomation/1.0"
    allowed_commands = load_allowed_commands()

    def _set_headers(self, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._set_headers(204)

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/run":
            self._set_headers(404)
            self.wfile.write(b'{"error":"not_found"}')
            return
        content_length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(content_length) or b"{}")
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(b'{"error":"invalid_json"}')
            return
        tasks = payload.get("tasks") or []
        workdir = Path(payload.get("workdir") or ROOT).expanduser()
        workdir = workdir if workdir.exists() else ROOT
        runs: list[dict[str, Any]] = []
        for task in tasks:
            command = task.get("command")
            if not command:
                continue
            if not any(allowed.matches(command) for allowed in self.allowed_commands):
                runs.append(
                    {
                        "id": task.get("id"),
                        "label": task.get("label"),
                        "command": command,
                        "exitCode": 126,
                        "stdout": "",
                        "stderr": "Command not allowed by automation_server.",
                        "startedAt": datetime.now(timezone.utc).isoformat(),
                        "finishedAt": datetime.now(timezone.utc).isoformat(),
                        "durationMs": 0,
                    }
                )
                continue
            started = datetime.now(timezone.utc)
            result = subprocess.run(
                command,
                shell=True,
                cwd=workdir,
                capture_output=True,
                text=True,
            )
            finished = datetime.now(timezone.utc)
            runs.append(
                {
                    "id": task.get("id"),
                    "label": task.get("label"),
                    "command": command,
                    "exitCode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "startedAt": started.isoformat(),
                    "finishedAt": finished.isoformat(),
                    "durationMs": int((finished - started).total_seconds() * 1000),
                }
            )
        append_history(runs)
        self._set_headers()
        self.wfile.write(json.dumps({"runs": runs}).encode("utf-8"))


def run_server() -> None:
    ensure_history_file()
    server = HTTPServer((SERVER_HOST, SERVER_PORT), AutomationHandler)
    print(f"LifeHub automation runner listening on http://{SERVER_HOST}:{SERVER_PORT}/run")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down automation runner.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
