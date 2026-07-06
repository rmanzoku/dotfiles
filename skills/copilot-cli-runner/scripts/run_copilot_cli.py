#!/usr/bin/env python3
"""Run GitHub Copilot CLI with JSONL artifacts and failure summaries."""

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
    r"(auth(?:entication)?\s+(?:failed|required|error)|api key|login\s+(?:required|failed)|"
    r"permission\s+(?:denied|required|error)|rate[- ]limit|quota|overloaded|"
    r"trust\s+(?:required|error)|policy\s+(?:violation|denied|error)|sandbox\s+(?:denied|error)|"
    r"model\s+(?:not found|unsupported|unavailable|invalid|error))",
    re.IGNORECASE,
)

COPILOT_ADAPTER = """\
## Copilot CLI Prompt Adapter

Complete the source prompt as an outcome-first task contract.

- Treat the source prompt's outcome, artifact paths, success criteria, allowed side effects, evidence rules, output shape, and stop condition as the contract.
- Write requested artifacts exactly where specified.
- Prefer the smallest sufficient plan and tool use that completes the contract.
- Do not emulate reasoning effort with phrases like "think hard" or mandatory step-by-step narration; rely on the CLI/config effort setting supplied by the caller.
- If a required input is missing, mark that item blocked with the missing input instead of guessing.
- Keep final output concise unless the source prompt asks for a detailed report.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run copilot -p with JSONL output, timeout, and artifact checks."
    )
    parser.add_argument("--prompt-file", required=True, help="Path to the saved prompt.md file.")
    parser.add_argument("--output-dir", required=True, help="Directory for run artifacts.")
    parser.add_argument(
        "--model",
        default=None,
        help="Copilot model. Omit to use the Copilot CLI configured default.",
    )
    parser.add_argument(
        "--effort",
        choices=("low", "medium", "high", "xhigh"),
        default=None,
        help="Copilot reasoning effort. Omit to use the Copilot CLI configured default.",
    )
    parser.add_argument(
        "--agent",
        default=None,
        help="Copilot custom agent. Omit to use the Copilot CLI configured default.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=600, help="Timeout in seconds. Defaults to 600.")
    parser.add_argument(
        "--expected-artifact",
        action="append",
        default=[],
        help="Expected non-empty artifact. Relative paths resolve from --output-dir; use absolute paths for artifacts outside it.",
    )
    parser.add_argument("--cwd", default=os.getcwd(), help="Working directory for Copilot.")
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
        "--copilot-bin",
        default="copilot",
        help="Copilot CLI binary to execute. Use the default for real runs; pass a fake CLI only for no-API tests.",
    )
    parser.add_argument(
        "--prompt-profile",
        choices=("auto", "copilot", "none"),
        default="auto",
        help="Prompt adapter profile. Auto applies the Copilot adapter.",
    )
    parser.add_argument(
        "--extra-copilot-arg",
        action="append",
        default=[],
        help="Additional Copilot CLI argument. Repeat for each token.",
    )
    return parser.parse_args()


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


def resolve_prompt_profile(requested: str) -> str:
    if requested == "auto":
        return "copilot"
    return requested


def write_launch_prompt(path: Path, source_prompt: Path, profile: str) -> None:
    sections = [
        "---",
        "task: copilot-cli-runner-launch",
        f"source_prompt: {source_prompt}",
        f"prompt_profile: {profile}",
        "---",
        "",
    ]
    if profile == "copilot":
        sections.extend([COPILOT_ADAPTER, ""])
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


def record_is_error(record: dict[str, Any]) -> bool:
    record_type = str(record.get("type", "")).lower()
    record_level = str(record.get("level", "")).lower()
    record_status = str(record.get("status", "")).lower()
    record_outcome = str(record.get("outcome", "")).lower()
    return (
        "error" in record_type
        or record_level == "error"
        or record_status == "error"
        or record_outcome in {"error", "failed", "failure"}
        or record.get("is_error") is True
        or ("error" in record and record.get("error") not in (None, "", False))
    )


def write_failure(path: Path, summary: dict[str, Any]) -> None:
    command = " ".join(summary["command"])
    last = summary.get("last_error_event") or summary.get("last_event") or {}
    missing = [
        item for item in summary["expected_artifacts"] if not item["exists"] or not item["non_empty"]
    ]
    reasons = summary.get("failure_reasons", [])
    recommendation = summary.get("recommended_next_action", "Inspect artifacts and rerun with adjusted limits.")

    body = [
        "# Copilot CLI Run Failure",
        "",
        f"- Command: `{command}`",
        f"- Exit code: `{summary['exit_code']}`",
        f"- Elapsed seconds: `{summary['elapsed_seconds']}`",
        f"- Events bytes: `{summary['events_bytes']}`",
        f"- Stderr bytes: `{summary['stderr_bytes']}`",
        f"- Failure reasons: {', '.join(reasons) if reasons else 'unknown'}",
        "",
        "## Last Error Or Event",
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
    events_path = output_dir / f"{args.stream_name}.events.jsonl"
    stderr_path = output_dir / f"{args.stream_name}.err"
    launch_prompt_path = output_dir / f"{args.stream_name}.prompt.md"
    summary_path = output_dir / "summary.json"
    failure_path = output_dir / "failure.md"
    prompt_profile = resolve_prompt_profile(args.prompt_profile)
    write_launch_prompt(launch_prompt_path, prompt_file, prompt_profile)

    short_prompt = (
        f"Read and follow the launch prompt in {launch_prompt_path}. "
        "Write the requested artifacts exactly where specified."
    )
    command = [
        timeout_bin,
        str(args.timeout_seconds),
        args.copilot_bin,
    ]
    if args.model:
        command.extend(["--model", args.model])
    if args.effort:
        command.extend(["--effort", args.effort])
    if args.agent:
        command.extend(["--agent", args.agent])
    command.extend(args.extra_copilot_arg)
    command.extend(["-p", short_prompt, "--output-format", "json"])

    start = time.monotonic()
    with events_path.open("wb") as stdout_fh, stderr_path.open("wb") as stderr_fh:
        proc = subprocess.run(
            command,
            cwd=str(cwd),
            stdout=stdout_fh,
            stderr=stderr_fh,
            check=False,
        )
    elapsed = round(time.monotonic() - start, 3)

    records = load_json_lines(events_path)
    error_events = [record for record in records if record_is_error(record)]
    last_event = records[-1] if records else None
    last_error_event = error_events[-1] if error_events else None
    stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.exists() else ""
    stderr_error = any(ERROR_RE.search(line) for line in stderr_text.splitlines())

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

    expected_ok = all(item["exists"] and item["non_empty"] for item in expected)
    events_present = events_path.exists() and events_path.stat().st_size > 0
    success_evidence_ok = proc.returncode == 0 and not error_events and events_present and expected_ok

    failure_reasons: list[str] = []
    nonfatal_reasons: list[str] = []
    if proc.returncode == 124:
        failure_reasons.append("timeout")
    elif proc.returncode != 0:
        failure_reasons.append("nonzero_exit")
    if stderr_error:
        if success_evidence_ok:
            nonfatal_reasons.append("stderr_cli_error")
        else:
            failure_reasons.append("stderr_cli_error")
    if error_events:
        failure_reasons.append("event_error")
    if not events_present:
        failure_reasons.append("missing_events")
    if not expected_ok:
        failure_reasons.append("missing_expected_artifact")

    if "timeout" in failure_reasons:
        recommended = "Inspect run.events.jsonl for partial progress, then rerun with a tighter prompt or larger timeout."
    elif "stderr_cli_error" in failure_reasons:
        recommended = "Fix authentication, model, permission, trust, policy, quota, or rate-limit settings before rerunning."
    elif "missing_expected_artifact" in failure_reasons:
        recommended = "Check the prompt artifact path contract and rerun with an explicit expected output path."
    elif nonfatal_reasons:
        recommended = "Run succeeded with non-fatal Copilot CLI warnings; inspect nonfatal_reasons and run.err if task quality is suspicious."
    elif not failure_reasons:
        recommended = "Run succeeded; evaluate task-specific artifact quality against the source prompt."
    else:
        recommended = "Inspect run.events.jsonl and run.err, then rerun with adjusted prompt, model, effort, agent, permissions, or timeout."

    summary = {
        "command": command,
        "copilot_bin": args.copilot_bin,
        "cwd": str(cwd),
        "prompt_file": str(prompt_file),
        "launch_prompt_path": str(launch_prompt_path),
        "prompt_profile": prompt_profile,
        "output_dir": str(output_dir),
        "exit_code": proc.returncode,
        "elapsed_seconds": elapsed,
        "events_path": str(events_path),
        "stderr_path": str(stderr_path),
        "events_bytes": events_path.stat().st_size if events_path.exists() else 0,
        "stderr_bytes": stderr_path.stat().st_size if stderr_path.exists() else 0,
        "record_count": len(records),
        "last_event": last_event,
        "last_error_event": last_error_event,
        "stderr_cli_error": stderr_error,
        "expected_artifacts": expected,
        "success": not failure_reasons,
        "failure_reasons": failure_reasons,
        "nonfatal_reasons": nonfatal_reasons,
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
