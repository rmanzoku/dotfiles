#!/usr/bin/env python3
"""Run Claude Code CLI with stream-json artifacts and failure summaries."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ERROR_RE = re.compile(
    r"(auth|authentication|api key|login|model|permission|rate limit|rate-limit|quota|overloaded)",
    re.IGNORECASE,
)

OPUS_4_7_MODEL_RE = re.compile(r"opus.*4[-_.]?7|4[-_.]?7.*opus", re.IGNORECASE)
OPUS_4_8_MODEL_RE = re.compile(r"opus.*4[-_.]?8|4[-_.]?8.*opus", re.IGNORECASE)

OPUS_4_7_ADAPTER = """\
## Claude Opus 4.7 Prompt Adapter

Execute the source prompt literally and completely.

- Treat the source prompt's outcome, constraints, tool limits, artifact paths, and completion criteria as the contract.
- Do not add fixed progress-update scaffolding. Report progress only if the source prompt asks for it or a real blocker requires it.
- Prefer direct completion over unnecessary subagents or tool calls. Use tools when needed to satisfy the source prompt, and respect explicit WebSearch/WebFetch, timeout, and output limits.
- If scope is ambiguous, resolve only what is explicitly supported by the source prompt and mark genuinely missing inputs as blocked.
- Do not emulate effort with phrases like "think hard"; rely on the CLI effort setting supplied by the caller.
"""

OPUS_4_8_ADAPTER = """\
## Claude Opus 4.8 Prompt Adapter

Execute the source prompt literally and completely.

- Treat the source prompt's outcome, constraints, tool limits, artifact paths, and completion criteria as the contract.
- Do not add fixed progress-update scaffolding. Report progress only if the source prompt asks for it or a real blocker requires it.
- Prefer direct completion over unnecessary subagents or tool calls. Use tools when needed to satisfy the source prompt, and respect explicit WebSearch/WebFetch, timeout, and output limits.
- For review or finding tasks, do not silently filter findings by importance unless the source prompt explicitly asks for filtering at that phase.
- If scope is ambiguous, resolve only what is explicitly supported by the source prompt and mark genuinely missing inputs as blocked.
- Do not emulate effort with phrases like "think hard"; rely on the CLI effort setting supplied by the caller.
"""


def normalize_argv(argv: list[str]) -> list[str]:
    normalized: list[str] = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--extra-claude-arg" and index + 1 < len(argv):
            normalized.append(f"--extra-claude-arg={argv[index + 1]}")
            index += 2
            continue
        normalized.append(token)
        index += 1
    return normalized


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run claude -p with stream-json output, timeout, optional budget, and artifact checks."
    )
    parser.add_argument("--prompt-file", required=True, help="Path to the saved prompt.md file.")
    parser.add_argument("--output-dir", required=True, help="Directory for run artifacts.")
    parser.add_argument(
        "--model",
        default=None,
        help="Claude model or alias. Omit to use the Claude CLI configured default.",
    )
    parser.add_argument(
        "--effort",
        choices=("low", "medium", "high", "xhigh", "max"),
        default=None,
        help="Claude effort level. Omit to use the Claude CLI configured default.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=600, help="Timeout in seconds. Defaults to 600.")
    parser.add_argument(
        "--budget-usd",
        default=None,
        help="Optional maximum Claude CLI API budget. Omit for subscription-based Claude CLI usage.",
    )
    parser.add_argument(
        "--expected-artifact",
        action="append",
        default=[],
        help="Expected non-empty artifact. Relative paths resolve from --output-dir; use absolute paths for artifacts outside it.",
    )
    parser.add_argument("--cwd", default=os.getcwd(), help="Working directory for claude.")
    parser.add_argument(
        "--stream-name",
        default="run",
        help="Artifact filename prefix. Defaults to run.",
    )
    parser.add_argument(
        "--timeout-bin",
        default=None,
        help="Timeout binary. Defaults to timeout, then gtimeout.",
    )
    parser.add_argument(
        "--claude-bin",
        default="claude",
        help="Claude CLI binary to execute. Use the default for real runs; pass a fake CLI only for no-API tests.",
    )
    parser.add_argument(
        "--permission-mode",
        default=None,
        help="Claude permission mode override. Omit to use the Claude CLI configured default.",
    )
    parser.add_argument(
        "--safe-mode",
        action="store_true",
        default=False,
        help="Pass Claude CLI --safe-mode. Omit to use the Claude CLI configured default customizations.",
    )
    parser.add_argument(
        "--extra-claude-arg",
        action="append",
        default=[],
        help="Additional Claude CLI argument. Repeat for each token.",
    )
    parser.add_argument(
        "--prompt-profile",
        choices=("auto", "opus-4-7", "opus-4-8", "none"),
        default="auto",
        help="Prompt adapter profile. Auto applies an Opus adapter for explicit opus-4.7 or opus-4.8 models.",
    )
    return parser.parse_args(normalize_argv(sys.argv[1:]))


def resolve_timeout_bin(explicit: str | None) -> str:
    if explicit:
        return explicit
    for candidate in ("timeout", "gtimeout"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise SystemExit("No timeout binary found. Install GNU coreutils or pass --timeout-bin.")


def artifact_path(raw: str, output_dir: Path) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = output_dir / path
    return path.resolve()


def load_json_lines(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)[:4000]


def resolve_prompt_profile(requested: str, model: str | None) -> str:
    if requested != "auto":
        return requested
    if model and OPUS_4_7_MODEL_RE.search(model):
        return "opus-4-7"
    if model and OPUS_4_8_MODEL_RE.search(model):
        return "opus-4-8"
    return "none"


def write_launch_prompt(path: Path, source_prompt: Path, profile: str) -> None:
    sections = [
        "---",
        "task: claude-cli-runner-launch",
        f"source_prompt: {source_prompt}",
        f"prompt_profile: {profile}",
        "---",
        "",
    ]
    if profile == "opus-4-7":
        sections.extend([OPUS_4_7_ADAPTER, ""])
    elif profile == "opus-4-8":
        sections.extend([OPUS_4_8_ADAPTER, ""])
    sections.extend(
        [
            "## Source Prompt",
            "",
            f"Read and follow `{source_prompt}`. Write requested artifacts exactly where specified.",
            "",
            "Stop only after every requested item is completed or explicitly marked blocked with the missing input.",
            "",
        ]
    )
    path.write_text("\n".join(sections), encoding="utf-8")


def classify_stream(records: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, dict[str, Any] | None, bool]:
    result_records = [record for record in records if record.get("type") == "result"]
    last_result = result_records[-1] if result_records else None
    error_result = next(
        (
            record
            for record in result_records
            if str(record.get("subtype", "")).lower().startswith("error")
        ),
        None,
    )
    success = bool(last_result and last_result.get("subtype") == "success")
    return last_result, error_result, success


def write_failure(path: Path, summary: dict[str, Any]) -> None:
    command = " ".join(summary["command"])
    last = summary.get("last_result") or summary.get("error_result") or {}
    missing = [
        item for item in summary["expected_artifacts"] if not item["exists"] or not item["non_empty"]
    ]
    reasons = summary.get("failure_reasons", [])
    recommendation = summary.get("recommended_next_action", "Inspect artifacts and rerun with adjusted limits.")

    body = [
        "# Claude CLI Run Failure",
        "",
        f"- Command: `{command}`",
        f"- Exit code: `{summary['exit_code']}`",
        f"- Elapsed seconds: `{summary['elapsed_seconds']}`",
        f"- Stream stdout bytes: `{summary['stream_stdout_bytes']}`",
        f"- Stderr bytes: `{summary['stderr_bytes']}`",
        f"- Failure reasons: {', '.join(reasons) if reasons else 'unknown'}",
        "",
        "## Last Result Or Error",
        "",
        "```json",
        compact_json(last),
        "```",
        "",
        "## Expected Artifacts",
        "",
    ]
    if missing:
        body.extend(
            f"- missing or empty: `{item['path']}` (exists={item['exists']}, non_empty={item['non_empty']})"
            for item in missing
        )
    else:
        body.append("- no missing expected artifacts recorded")
    body.extend(["", "## Recommended Next Action", "", recommendation, ""])
    path.write_text("\n".join(body), encoding="utf-8")


def main() -> int:
    args = parse_args()
    prompt_file = Path(args.prompt_file).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    cwd = Path(args.cwd).expanduser().resolve()
    timeout_bin = resolve_timeout_bin(args.timeout_bin)

    if not prompt_file.exists() or not prompt_file.is_file():
        print(f"prompt file does not exist: {prompt_file}", file=sys.stderr)
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)
    stream_path = output_dir / f"{args.stream_name}.stream.jsonl"
    stderr_path = output_dir / f"{args.stream_name}.err"
    launch_prompt_path = output_dir / f"{args.stream_name}.prompt.md"
    summary_path = output_dir / "summary.json"
    failure_path = output_dir / "failure.md"
    prompt_profile = resolve_prompt_profile(args.prompt_profile, args.model)
    write_launch_prompt(launch_prompt_path, prompt_file, prompt_profile)

    short_prompt = (
        f"Read and follow the launch prompt in {launch_prompt_path}. "
        "Write the requested artifacts exactly where specified."
    )
    command = [
        timeout_bin,
        str(args.timeout_seconds),
        args.claude_bin,
        "-p",
        "--verbose",
        "--output-format",
        "stream-json",
        "--include-partial-messages",
    ]
    if args.permission_mode:
        command.extend(["--permission-mode", args.permission_mode])
    if args.safe_mode:
        command.append("--safe-mode")
    if args.budget_usd:
        command.extend(["--max-budget-usd", str(args.budget_usd)])
    if args.model:
        command.extend(["--model", args.model])
    if args.effort:
        command.extend(["--effort", args.effort])
    command.extend([*args.extra_claude_arg, short_prompt])

    start = time.monotonic()
    with stream_path.open("wb") as stdout_fh, stderr_path.open("wb") as stderr_fh:
        proc = subprocess.run(
            command,
            cwd=str(cwd),
            stdout=stdout_fh,
            stderr=stderr_fh,
            check=False,
        )
    elapsed = round(time.monotonic() - start, 3)

    records = load_json_lines(stream_path)
    last_result, error_result, stream_success = classify_stream(records)
    stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.exists() else ""
    stderr_error = bool(ERROR_RE.search(stderr_text))

    expected = []
    for raw in args.expected_artifact:
        path = artifact_path(raw, output_dir)
        exists = path.exists()
        non_empty = exists and path.is_file() and path.stat().st_size > 0
        expected.append(
            {
                "path": str(path),
                "exists": exists,
                "non_empty": non_empty,
                "size_bytes": path.stat().st_size if exists and path.is_file() else 0,
            }
        )

    failure_reasons: list[str] = []
    if proc.returncode == 124:
        failure_reasons.append("timeout")
    elif proc.returncode != 0:
        failure_reasons.append("nonzero_exit")
    if stderr_error:
        failure_reasons.append("stderr_cli_error")
    if error_result:
        failure_reasons.append("stream_result_error")
    if not stream_success:
        failure_reasons.append("missing_success_result")
    if any(not item["exists"] or not item["non_empty"] for item in expected):
        failure_reasons.append("missing_expected_artifact")

    if "timeout" in failure_reasons:
        recommended = "Inspect run.stream.jsonl for partial progress, then rerun with a tighter prompt or larger timeout."
    elif "stderr_cli_error" in failure_reasons:
        recommended = "Fix authentication, model, permission, quota, or rate-limit settings before rerunning."
    elif "missing_expected_artifact" in failure_reasons:
        recommended = "Check the prompt artifact path contract and rerun with an explicit expected output path."
    elif not failure_reasons:
        recommended = "Run succeeded; evaluate task-specific artifact quality against the source prompt."
    else:
        recommended = "Inspect run.stream.jsonl and run.err, then rerun with adjusted prompt, model, optional budget, or timeout."

    summary = {
        "command": command,
        "claude_bin": args.claude_bin,
        "permission_mode": args.permission_mode,
        "safe_mode": args.safe_mode,
        "cwd": str(cwd),
        "prompt_file": str(prompt_file),
        "launch_prompt_path": str(launch_prompt_path),
        "prompt_profile": prompt_profile,
        "output_dir": str(output_dir),
        "exit_code": proc.returncode,
        "elapsed_seconds": elapsed,
        "stream_stdout_path": str(stream_path),
        "stderr_path": str(stderr_path),
        "stream_stdout_bytes": stream_path.stat().st_size if stream_path.exists() else 0,
        "stderr_bytes": stderr_path.stat().st_size if stderr_path.exists() else 0,
        "record_count": len(records),
        "last_result": last_result,
        "error_result": error_result,
        "stderr_cli_error": stderr_error,
        "expected_artifacts": expected,
        "success": not failure_reasons,
        "failure_reasons": failure_reasons,
        "recommended_next_action": recommended,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if failure_reasons:
        write_failure(failure_path, summary)
        return 1
    if failure_path.exists():
        failure_path.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
