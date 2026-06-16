#!/usr/bin/env python3
"""Run op/opmaterialize commands with observable direct logs."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


AUTH_SIGNATURES = [
    ("auth_required", re.compile(r"account is not signed in", re.I)),
    ("prompt_error", re.compile(r"promptError|prompt error", re.I)),
    ("authorization_dismissed", re.compile(r"authorization prompt dismissed", re.I)),
    ("auth_timeout", re.compile(r"authorization timeout", re.I)),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def redact_arg(arg: str) -> str:
    return re.sub(r"op://[^\s'\"`]+", "op://REDACTED", arg)


def classify(text: str, exit_code: int | None, timed_out: bool) -> str | None:
    if timed_out:
        return "timeout"
    for name, pattern in AUTH_SIGNATURES:
        if pattern.search(text):
            return name
    if exit_code not in (None, 0):
        return "command_failed"
    return None


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def log_line(log_path: Path, message: str) -> None:
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(f"{utc_now()} {message}\n")


def signin_account(command: list[str]) -> str | None:
    if len(command) < 2 or Path(command[0]).name != "op" or command[1] != "signin":
        return None
    for index, value in enumerate(command):
        if value == "--account" and index + 1 < len(command):
            return command[index + 1]
        if value.startswith("--account="):
            return value.split("=", 1)[1]
    return os.environ.get("OP_ACCOUNT")


def verify_signin(args: argparse.Namespace, command: list[str], log_path: Path) -> tuple[bool, str | None, str]:
    account = signin_account(command)
    if not account:
        return True, None, ""

    verify_command = ["op", "whoami", "--account", account]
    log_line(log_path, f"[verify] op whoami --account {account}")
    try:
        proc = subprocess.run(
            verify_command,
            cwd=args.cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=min(args.timeout_seconds, 60),
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        combined = f"{exc.stdout or ''}\n{exc.stderr or ''}"
        log_line(log_path, "[verify-timeout] signin verification exceeded timeout")
        return False, "signin_unverified", combined

    if proc.returncode == 0:
        log_line(log_path, "[verify] signin verified by whoami")
        return True, None, f"{proc.stdout}\n{proc.stderr}"

    combined = f"{proc.stdout}\n{proc.stderr}"
    if proc.stderr:
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(proc.stderr)
            if not proc.stderr.endswith("\n"):
                fh.write("\n")
    failure = classify(combined, proc.returncode, False) or "signin_unverified"
    log_line(log_path, f"[verify-failed] signin did not create a usable session failure_kind={failure}")
    return False, failure, combined


def run_direct(args: argparse.Namespace, command: list[str], out_dir: Path, log_path: Path) -> dict:
    started = time.monotonic()
    log_line(log_path, f"[start] direct cwd={args.cwd}")
    timed_out = False
    exit_code: int | None = None
    combined = ""
    try:
        proc = subprocess.run(
            command,
            cwd=args.cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=args.timeout_seconds,
            check=False,
        )
        exit_code = proc.returncode
        if proc.stdout:
            with log_path.open("a", encoding="utf-8") as fh:
                fh.write(proc.stdout)
                if not proc.stdout.endswith("\n"):
                    fh.write("\n")
        if proc.stderr:
            with log_path.open("a", encoding="utf-8") as fh:
                fh.write(proc.stderr)
                if not proc.stderr.endswith("\n"):
                    fh.write("\n")
        combined = f"{proc.stdout}\n{proc.stderr}"
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = 124
        combined = f"{exc.stdout or ''}\n{exc.stderr or ''}"
        log_line(log_path, f"[timeout] exceeded {args.timeout_seconds}s")

    verify_failure: str | None = None
    if exit_code == 0 and not timed_out:
        verified, verify_failure, verify_output = verify_signin(args, command, log_path)
        combined = f"{combined}\n{verify_output}"
        if not verified:
            exit_code = 1

    elapsed = round(time.monotonic() - started, 3)
    failure_kind = verify_failure or classify(combined, exit_code, timed_out)
    log_line(log_path, f"[done] direct exit_code={exit_code} elapsed={elapsed}s failure_kind={failure_kind or 'none'}")
    return {
        "mode": "direct",
        "cwd": str(Path(args.cwd).resolve()),
        "exit_code": exit_code,
        "elapsed_seconds": elapsed,
        "timed_out": timed_out,
        "failure_kind": failure_kind,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run op/opmaterialize through one observable direct subprocess path.")
    parser.add_argument("--output-dir", required=True, help="Directory for logs and summary artifacts.")
    parser.add_argument("--cwd", default=os.getcwd(), help="Working directory for the command.")
    parser.add_argument("--timeout-seconds", type=int, default=300, help="Timeout for the command.")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to run after --, e.g. -- op whoami.")
    args = parser.parse_args(argv)
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("command is required after --")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "run.log"
    redacted = [redact_arg(part) for part in args.command]
    (out_dir / "command.redacted.json").write_text(json.dumps(redacted, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = run_direct(args, args.command, out_dir, log_path)

    summary.update(
        {
            "created_at": utc_now(),
            "command_redacted": redacted,
            "output_dir": str(out_dir),
        }
    )
    write_json(out_dir / "summary.json", summary)
    return int(summary.get("exit_code") or 0)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
