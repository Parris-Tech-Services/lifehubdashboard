#!/usr/bin/env python3
"""Simple HTTP runner that executes LifeHub automation commands.

Security note (2026-09-27): this server used to accept `Access-Control-
Allow-Origin: *` and run allowlisted commands via `subprocess.run(command,
shell=True)`. Because the dashboard's Content-Type is `application/json`,
browsers preflight the POST -- so the wildcard origin meant ANY website the
user had open in a tab could pass that preflight and trigger a real POST to
this endpoint. Two allowlisted commands accept attacker-influenced argument
text (`allowArguments: true`), which combined with `shell=True` was a
straightforward shell-metacharacter command-injection RCE reachable from any
webpage while this server happened to be running. This was already flagged
in docs/SECURITY.md but never patched.

Fixed by:
- Only ever answering CORS preflight for requests whose Origin is absent,
  "null" (what browsers send for file:// pages, which is how this dashboard
  is normally opened), or an explicit http(s)://localhost|127.0.0.1[:port]
  origin. Any other origin's preflight fails, so the browser never sends
  the real POST.
- Never invoking a shell. Every command, including the fixed "&&"-joined
  allowlist entry, is split with shlex and executed as an argv list
  (`shell=False`). Any shell metacharacters an attacker appends to an
  allowArguments command are now just inert literal argument text, not
  shell syntax -- there is no shell present to interpret them.
"""
from __future__ import annotations

import json
import re
import shlex
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

# Origins allowed to receive CORS headers (and therefore the only origins
# whose preflight can succeed). "null" is what browsers send as the Origin
# for file:// pages, which is how this dashboard is normally opened.
_ALLOWED_LOCAL_ORIGIN = re.compile(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$")


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


def run_allowed_command(
    matched: AllowedCommand, candidate: str, workdir: Path
) -> tuple[int, str, str]:
    """Run a matched allowlisted command with no shell involved.

    For allowArguments commands, the attacker-influenced suffix is parsed
    with shlex and appended as literal argv entries -- never concatenated
    into a shell string, so shell metacharacters in it do nothing. The
    fixed (non-parameterized) allowlist entries are pre-vetted strings, so
    splitting a "&&"-joined entry into sequential shell=False steps (still
    stopping at the first failure, like a real `&&`) is safe here: nothing
    attacker-controlled ever reaches this branch.
    """
    if matched.allow_arguments:
        suffix = candidate[len(matched.command) :].strip()
        argv_steps = [shlex.split(matched.command) + (shlex.split(suffix) if suffix else [])]
    else:
        argv_steps = [shlex.split(step.strip()) for step in matched.command.split("&&")]

    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    returncode = 0
    for argv in argv_steps:
        if not argv:
            continue
        result = subprocess.run(
            argv,
            shell=False,
            cwd=workdir,
            capture_output=True,
            text=True,
        )
        stdout_parts.append(result.stdout)
        stderr_parts.append(result.stderr)
        returncode = result.returncode
        if returncode != 0:
            break
    return returncode, "".join(stdout_parts), "".join(stderr_parts)


class AutomationHandler(BaseHTTPRequestHandler):
    server_version = "LifeHubAutomation/1.0"
    allowed_commands = load_allowed_commands()

    def _allowed_origin(self) -> str | None:
        origin = self.headers.get("Origin")
        if origin is None or origin == "null":
            return "null"
        if _ALLOWED_LOCAL_ORIGIN.match(origin):
            return origin
        return None

    def _set_headers(self, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        allowed_origin = self._allowed_origin()
        if allowed_origin is not None:
            self.send_header("Access-Control-Allow-Origin", allowed_origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._set_headers(204)

    def do_POST(self) -> None:  # noqa: N802
        if self._allowed_origin() is None:
            self._set_headers(403)
            self.wfile.write(b'{"error":"origin_not_allowed"}')
            return
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
            matched = next(
                (allowed for allowed in self.allowed_commands if allowed.matches(command)),
                None,
            )
            if matched is None:
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
            try:
                exit_code, stdout, stderr = run_allowed_command(matched, command, workdir)
            except ValueError as exc:
                # shlex.split raises ValueError on unbalanced quotes, etc.
                exit_code, stdout, stderr = 126, "", f"Could not parse command: {exc}"
            finished = datetime.now(timezone.utc)
            runs.append(
                {
                    "id": task.get("id"),
                    "label": task.get("label"),
                    "command": command,
                    "exitCode": exit_code,
                    "stdout": stdout,
                    "stderr": stderr,
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
