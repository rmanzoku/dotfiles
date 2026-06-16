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

PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
    re.S,
)
KEY_VALUE_SECRET_PATTERN = re.compile(
    r"(?i)\b(password|token|secret|api[_-]?key|client[_-]?secret|credential)\b\s*[:=]\s*[^\s'\"`\\]+"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def redact_text(text: str) -> str:
    redacted = re.sub(r"op://[^\s'\"`]+", "op://REDACTED", text)
    redacted = re.sub(r"OP_SESSION_[A-Z0-9_]+=[^\s'\"`\\]+", "OP_SESSION_REDACTED=REDACTED", redacted)
    redacted = PRIVATE_KEY_PATTERN.sub("-----BEGIN PRIVATE KEY-----\nREDACTED\n-----END PRIVATE KEY-----", redacted)
    return KEY_VALUE_SECRET_PATTERN.sub(lambda match: f"{match.group(1)}=REDACTED", redacted)


def redact_arg(arg: str) -> str:
    return redact_text(arg)


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


def log_output(log_path: Path, output: str) -> None:
    if not output:
        return
    safe_output = redact_text(output)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(safe_output)
        if not safe_output.endswith("\n"):
            fh.write("\n")


def command_name(command: list[str]) -> str:
    if not command:
        return ""
    return Path(command[0]).name


def command_rejection(command: list[str]) -> str | None:
    name = command_name(command)
    if name == "op":
        has_out_file = "--out-file" in command or any(part.startswith("--out-file=") for part in command)
        has_reveal = "--reveal" in command or any(part.startswith("--reveal=") for part in command)
        if len(command) >= 2 and command[1] == "read":
            return "op read prints secret values to stdout"
        if len(command) >= 3 and command[1:3] == ["item", "get"] and has_reveal:
            return "op item get --reveal can print secret values to stdout"
        if len(command) >= 3 and command[1:3] == ["document", "get"] and not has_out_file:
            return "op document get requires --out-file to avoid stdout secret output"
        return None

    if name in {"sh", "bash", "zsh"} and len(command) >= 3 and command[1] == "-c":
        script = command[2]
        if re.search(r"\bop\s+read\b", script):
            return "shell command contains op read, which can print secret values to stdout"
        if re.search(r"\bop\s+item\s+get\b[^\n;]*--reveal", script):
            return "shell command contains op item get --reveal, which can print secret values to stdout"
        if re.search(r"\bop\s+document\s+get\b", script) and "--out-file" not in script:
            return "shell command contains op document get without --out-file"

    return None


def resolve_cwd(cwd: str) -> Path:
    return Path(cwd).expanduser().resolve()


def resolve_output_dir(output_dir: str, cwd: Path) -> Path:
    out_dir = Path(output_dir).expanduser()
    if not out_dir.is_absolute():
        out_dir = cwd / out_dir
    out_dir = out_dir.resolve(strict=False)
    context_root = (cwd / ".context").resolve(strict=False)
    if out_dir != context_root and context_root not in out_dir.parents:
        raise ValueError(f"--output-dir must be inside {context_root}")
    return out_dir


def signin_account(command: list[str]) -> str | None:
    if len(command) < 2 or command_name(command) != "op" or command[1] != "signin":
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
            cwd=args.cwd_path,
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
    log_output(log_path, proc.stderr)
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
            cwd=args.cwd_path,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=args.timeout_seconds,
            check=False,
        )
        exit_code = proc.returncode
        log_output(log_path, proc.stdout)
        log_output(log_path, proc.stderr)
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
        "cwd": str(args.cwd_path),
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
    args.cwd_path = resolve_cwd(args.cwd)
    try:
        out_dir = resolve_output_dir(args.output_dir, args.cwd_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "run.log"
    redacted = [redact_arg(part) for part in args.command]
    (out_dir / "command.redacted.json").write_text(json.dumps(redacted, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    rejection = command_rejection(args.command)
    if rejection:
        log_line(log_path, f"[rejected] {rejection}")
        summary = {
            "mode": "direct",
            "cwd": str(args.cwd_path),
            "exit_code": 2,
            "elapsed_seconds": 0,
            "timed_out": False,
            "failure_kind": "rejected_secret_stdout",
            "rejection_reason": rejection,
        }
    else:
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
