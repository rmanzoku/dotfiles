#!/usr/bin/env python3
"""Antigravity CLI (agy) を print モードでサブプロセス実行し、観測可能な artifact を残す。

プロンプトはファイルを正本とし、実行時のみ agy の argv へ渡す。agy の print モードは
`-p <prompt>` の値渡しだけを受け付け、stdin もプロンプトファイル指定も持たないため
（2026-08-08 に実測）。argv 経由になる分の壊れやすさは、送信バイト数の上限検査と
run.prompt.md への保存で観測可能にしている。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# argv は macOS で args+env 合計 1MiB 程度が上限。超過は execve の失敗という
# 分かりにくい形で出るため、余裕を持った閾値で明示的に失敗させる。
MAX_PROMPT_BYTES = 128 * 1024


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run Antigravity CLI (agy) in print mode with observable artifacts.")
    p.add_argument("--prompt-file", required=True, help="Path to the prompt markdown. This file is the source of truth.")
    p.add_argument("--output-dir", required=True, help="Directory for run artifacts.")
    p.add_argument("--response-artifact", default="agy-response.json",
                   help="Response artifact path. Relative paths resolve from --output-dir.")
    p.add_argument("--model", required=True,
                   help="agy model id (e.g. gemini-3.1-pro-high). agy has no 'auto'; run `agy models` for the list.")
    p.add_argument("--effort", default=None, choices=["low", "medium", "high"], help="Reasoning effort.")
    p.add_argument("--output-format", default="json", choices=["json", "text", "stream-json"],
                   help="agy --output-format. json exposes status/usage and is the default for observability.")
    p.add_argument("--timeout-seconds", type=int, default=600, help="Wrapper process timeout. Defaults to 600.")
    p.add_argument("--print-timeout", default=None,
                   help="agy --print-timeout (e.g. 8m). Defaults to the wrapper timeout minus a small margin.")
    p.add_argument("--cwd", default=os.getcwd(), help="Working directory for the subprocess.")
    p.add_argument("--agy-bin", default="agy", help="agy executable. Defaults to agy on PATH.")
    p.add_argument("--timeout-bin", default=None, help="Timeout binary. Defaults to timeout, then gtimeout.")
    p.add_argument("--skip-permissions", action="store_true",
                   help="Pass --dangerously-skip-permissions. Required for tool use (web search, file writes) in "
                        "headless runs, because nobody can answer a permission prompt.")
    p.add_argument("--sandbox", action="store_true", help="Pass --sandbox (terminal restrictions).")
    p.add_argument("--add-dir", action="append", default=[], help="Pass --add-dir (repeatable).")
    p.add_argument("--agent", default=None, help="Pass --agent for the session.")
    p.add_argument("--dry-run", action="store_true", help="Validate and record the command without calling agy.")
    p.add_argument("--extra-agy-arg", action="append", default=[],
                   help="Extra agy token, one per flag (e.g. --extra-agy-arg=--json-schema --extra-agy-arg=path).")
    return p.parse_args()


def resolve_timeout_bin(explicit: str | None) -> str:
    if explicit:
        return explicit
    for candidate in ("timeout", "gtimeout"):
        found = shutil.which(candidate)
        if found:
            return found
    raise RuntimeError("No timeout binary found. Install coreutils or pass --timeout-bin.")


def artifact_path(raw: str, output_dir: Path) -> Path:
    p = Path(raw).expanduser()
    return p if p.is_absolute() else output_dir / p


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def log(msg: str) -> None:
    print(f"[agy-cli-runner] {msg}", flush=True)


def derive_print_timeout(explicit: str | None, timeout_seconds: int) -> str:
    if explicit:
        return explicit
    # agy 側は wrapper より先に諦めさせる。wrapper の timeout が発火すると
    # agy が結果を書き出す前に殺され、原因が読めなくなるため。
    margin = 30 if timeout_seconds > 60 else max(2, timeout_seconds // 10)
    inner = max(5, timeout_seconds - margin)
    return f"{inner}s"


def build_command(args: argparse.Namespace, timeout_bin: str, prompt: str) -> list[str]:
    cmd = [timeout_bin, str(args.timeout_seconds), args.agy_bin,
           "-p", prompt,
           "--model", args.model,
           "--output-format", args.output_format,
           "--print-timeout", derive_print_timeout(args.print_timeout, args.timeout_seconds)]
    if args.effort:
        cmd += ["--effort", args.effort]
    if args.agent:
        cmd += ["--agent", args.agent]
    if args.skip_permissions:
        cmd.append("--dangerously-skip-permissions")
    if args.sandbox:
        cmd.append("--sandbox")
    for d in args.add_dir:
        cmd += ["--add-dir", d]
    cmd += list(args.extra_agy_arg)
    return cmd


def redact_command(cmd: list[str]) -> list[str]:
    out = []
    skip_next = False
    for tok in cmd:
        if skip_next:
            out.append("<prompt from prompt-file>")
            skip_next = False
            continue
        out.append(tok)
        if tok in ("-p", "--print", "--prompt"):
            skip_next = True
    return out


def parse_stdout(raw: str, output_format: str) -> tuple[Any, str, str | None, dict[str, Any] | None]:
    """returns (parsed, output_text, status, usage)"""
    if output_format == "text":
        return None, raw, "SUCCESS" if raw.strip() else None, None
    if output_format == "stream-json":
        events = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        text = ""
        status = None
        usage = None
        for ev in events:
            if isinstance(ev, dict):
                status = ev.get("status", status)
                usage = ev.get("usage", usage)
                if isinstance(ev.get("response"), str):
                    text = ev["response"]
        return events, text, status, usage
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None, raw, None, None
    if not isinstance(parsed, dict):
        return parsed, raw, None, None
    return parsed, parsed.get("response", "") or "", parsed.get("status"), parsed.get("usage")


def classify(*, exit_code: int, status: str | None, response_non_empty: bool,
             agy_error: str | None, setup_error: str | None, dry_run: bool) -> list[str]:
    reasons: list[str] = []
    if setup_error:
        if "executable not found" in setup_error:
            reasons.append("missing_agy")
        elif "prompt" in setup_error.lower():
            reasons.append("invalid_prompt")
        else:
            reasons.append("setup_error")
        return reasons
    if dry_run:
        return reasons
    if exit_code == 124:
        reasons.append("timeout")
    elif exit_code != 0:
        reasons.append("nonzero_exit")
    if agy_error:
        reasons.append("agy_error")
    if exit_code == 0 and status is not None and status != "SUCCESS":
        reasons.append("status_not_success")
    if exit_code == 0 and not response_non_empty and "agy_error" not in reasons:
        reasons.append("empty_response")
    return reasons


def next_action(reasons: list[str], *, dry_run: bool) -> str:
    if dry_run and not reasons:
        return "Dry-run succeeded; inspect summary.json dry_run_payload and command before making a real call."
    if "missing_agy" in reasons:
        return "Install Antigravity CLI and ensure `agy` is on PATH, then rerun."
    if "invalid_prompt" in reasons:
        return "Fix --prompt-file: it must exist, be non-empty, and stay under the byte limit reported in summary.json."
    if "timeout" in reasons:
        return "Inspect prompt size and agy state, then rerun with a larger --timeout-seconds or a smaller prompt."
    if "agy_error" in reasons:
        return "Read summary.json agy_error. Invalid --model is the common case; run `agy models` for valid ids."
    if "status_not_success" in reasons:
        return "agy returned a non-SUCCESS status. Inspect agy-response.json parsed_stdout and run.err."
    if "empty_response" in reasons:
        return ("agy exited 0 with an empty response. For tasks needing tools (web search, file writes) rerun with "
                "--skip-permissions, since a headless run cannot answer a permission prompt.")
    if "nonzero_exit" in reasons:
        return "Inspect run.err and summary.json, then rerun after fixing auth, model, or flags."
    return "Inspect summary.json and the response artifact, then integrate the response in the caller."


def write_failure(path: Path, summary: dict[str, Any]) -> None:
    reasons = summary.get("failure_reasons", [])
    body = [
        "# agy CLI Runner Failure",
        "",
        f"- Command: `{' '.join(summary['command'])}`",
        f"- Exit code: `{summary['exit_code']}`",
        f"- Status: `{summary.get('status')}`",
        f"- Elapsed seconds: `{summary['elapsed_seconds']}`",
        f"- Model: `{summary.get('model')}`",
        f"- Prompt bytes: `{summary.get('prompt_bytes')}`",
        f"- Response artifact: `{summary.get('response_artifact')}`",
        f"- Response non-empty: `{summary.get('response_non_empty')}`",
        f"- Stderr bytes: `{summary.get('stderr_bytes')}`",
        f"- Failure reasons: {', '.join(reasons) if reasons else 'unknown'}",
        "",
        "## Error",
        "",
        "```",
        str(summary.get("agy_error") or summary.get("setup_error") or "(none)")[:4000],
        "```",
        "",
        "## Recommended Next Action",
        "",
        summary.get("recommended_next_action", "Inspect artifacts and rerun."),
        "",
    ]
    path.write_text("\n".join(body), encoding="utf-8")


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    response_path = artifact_path(args.response_artifact, out_dir)
    stderr_path = out_dir / "run.err"
    summary_path = out_dir / "summary.json"
    failure_path = out_dir / "failure.md"
    saved_prompt = out_dir / "run.prompt.md"

    setup_error: str | None = None
    prompt = ""
    prompt_bytes = 0
    command: list[str] = []
    exit_code = 0
    status: str | None = None
    usage: dict[str, Any] | None = None
    agy_error: str | None = None
    output_text = ""
    started = time.monotonic()

    try:
        pf = Path(args.prompt_file).expanduser()
        if not pf.is_file():
            raise RuntimeError(f"prompt file not found: {pf}")
        prompt = pf.read_text(encoding="utf-8")
        prompt_bytes = len(prompt.encode("utf-8"))
        if not prompt.strip():
            raise RuntimeError(f"prompt file is empty: {pf}")
        if prompt_bytes > MAX_PROMPT_BYTES:
            raise RuntimeError(
                f"prompt is {prompt_bytes} bytes, over the {MAX_PROMPT_BYTES} byte limit for argv transport. "
                "Split the task or summarize the prompt.")
        saved_prompt.write_text(prompt, encoding="utf-8")

        timeout_bin = resolve_timeout_bin(args.timeout_bin)
        if not shutil.which(args.agy_bin):
            raise RuntimeError(f"agy executable not found: {args.agy_bin}")
        command = build_command(args, timeout_bin, prompt)

        if args.dry_run:
            log("dry-run: command built, agy not called")
        else:
            log(f"starting agy print run model={args.model} timeout_seconds={args.timeout_seconds} "
                f"prompt_bytes={prompt_bytes}")
            with stderr_path.open("wb") as errfh:
                proc = subprocess.run(command, cwd=str(Path(args.cwd).expanduser().resolve()),
                                      stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                      stderr=errfh, check=False)
            exit_code = proc.returncode
            raw = proc.stdout.decode("utf-8", errors="replace")
            parsed, output_text, status, usage = parse_stdout(raw, args.output_format)
            if isinstance(parsed, dict) and parsed.get("error"):
                agy_error = str(parsed["error"])
            write_json(response_path, {
                "task": pf.stem,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "request": {"prompt_file": str(pf), "prompt_bytes": prompt_bytes,
                            "model": args.model, "effort": args.effort},
                "response": {"type": "agy_cli_response", "output_format": args.output_format,
                             "stdout_bytes": len(proc.stdout), "parsed_stdout": parsed},
                "output_text": output_text,
                "conversation_id": parsed.get("conversation_id") if isinstance(parsed, dict) else None,
                "model": args.model,
                "backend": "antigravity-cli",
            })
            log(f"finished exit_code={exit_code} status={status} response_chars={len(output_text)}")
    except RuntimeError as exc:
        setup_error = str(exc)
        log(f"setup failed: {setup_error}")

    elapsed = round(time.monotonic() - started, 3)
    response_non_empty = bool(output_text.strip())
    reasons = classify(exit_code=exit_code, status=status, response_non_empty=response_non_empty,
                       agy_error=agy_error, setup_error=setup_error, dry_run=args.dry_run)
    summary = {
        "command": redact_command(command),
        "cwd": str(Path(args.cwd).expanduser().resolve()),
        "prompt_file": str(Path(args.prompt_file).expanduser()),
        "prompt_bytes": prompt_bytes,
        "max_prompt_bytes": MAX_PROMPT_BYTES,
        "model": args.model,
        "effort": args.effort,
        "output_format": args.output_format,
        "skip_permissions": args.skip_permissions,
        "sandbox": args.sandbox,
        "dry_run": args.dry_run,
        "exit_code": exit_code,
        "status": status,
        "usage": usage,
        "elapsed_seconds": elapsed,
        "response_artifact": str(response_path),
        "response_non_empty": response_non_empty,
        "response_bytes": response_path.stat().st_size if response_path.exists() else 0,
        "stderr_bytes": stderr_path.stat().st_size if stderr_path.exists() else 0,
        "agy_error": agy_error,
        "setup_error": setup_error,
        "failure_reasons": reasons,
        "success": not reasons,
        "recommended_next_action": next_action(reasons, dry_run=args.dry_run),
    }
    if args.dry_run:
        summary["dry_run_payload"] = {"command": redact_command(command), "prompt_bytes": prompt_bytes}
    write_json(summary_path, summary)

    if reasons:
        write_failure(failure_path, summary)
        log(f"FAILED reasons={','.join(reasons)} -> {failure_path}")
        return 1
    if failure_path.exists():
        failure_path.unlink()
    log(f"OK summary={summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
