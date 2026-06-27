#!/usr/bin/env python3
"""Run Gemini CLI with stream-json artifacts and failure summaries."""

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


FATAL_STDERR_RE = re.compile(
    r"(auth(?:entication)?\s+(?:failed|required|error)|api key|login\s+(?:required|failed)|"
    r"permission\s+(?:denied|required|error)|rate[- ]limit|quota|overloaded|"
    r"trust\s+(?:required|error)|policy\s+(?:violation|denied|error)|sandbox\s+(?:denied|error)|"
    r"model\s+(?:not found|unsupported|unavailable|invalid|error))",
    re.IGNORECASE,
)
RAW_MODE_RE = re.compile(r"setRawMode\s+(?:EIO|EBADF)", re.IGNORECASE)

GEMINI_ADAPTER = """\
## Gemini CLI Prompt Adapter

Complete the source prompt as an outcome-first task contract.

- Treat the source prompt's outcome, artifact paths, success criteria, allowed side effects, evidence rules, output shape, and stop condition as the contract.
- Write requested artifacts exactly where specified.
- If an expected artifact path is absolute, use that absolute path exactly; do not rewrite it as a path relative to the current working directory.
- Do not create, update, or delete files outside the requested artifacts unless the source prompt explicitly allows that side effect.
- Use the tools available under the caller's Gemini CLI config/profile when they are needed to complete the contract.
- Prefer the smallest sufficient plan and tool use that completes the contract.
- Do not emulate model effort with phrases like "think hard" or mandatory step-by-step narration; rely on the CLI/config settings supplied by the caller.
- If a required input is missing or unreadable, mark the requested artifact blocked with the missing input instead of guessing.
- Keep final output concise unless the source prompt asks for a detailed report.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run gemini -p with stream-json output, timeout, and artifact checks."
    )
    parser.add_argument("--prompt-file", required=True, help="Path to the saved prompt.md file.")
    parser.add_argument("--output-dir", required=True, help="Directory for run artifacts.")
    parser.add_argument(
        "--model",
        default=None,
        help="Gemini model. Omit to use the Gemini CLI configured default.",
    )
    parser.add_argument(
        "--approval-mode",
        choices=("default", "auto_edit", "yolo", "plan"),
        default=None,
        help="Gemini approval mode. Omit to use the Gemini CLI configured default.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=600, help="Timeout in seconds. Defaults to 600.")
    parser.add_argument(
        "--expected-artifact",
        action="append",
        default=[],
        help="Expected non-empty artifact. Relative paths resolve from --output-dir; use absolute paths for artifacts outside it.",
    )
    parser.add_argument("--cwd", default=os.getcwd(), help="Working directory for Gemini.")
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
        "--gemini-bin",
        default="gemini",
        help="Gemini CLI binary to execute. Use the default for real runs; pass a fake CLI only for no-API tests.",
    )
    parser.add_argument(
        "--prompt-profile",
        choices=("auto", "gemini", "none"),
        default="auto",
        help="Prompt adapter profile. Auto applies the Gemini adapter.",
    )
    parser.add_argument(
        "--extra-gemini-arg",
        action="append",
        default=[],
        help="Additional Gemini CLI argument. Repeat for each token.",
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
        return "gemini"
    return requested


def write_launch_prompt(
    path: Path,
    source_prompt: Path,
    source_prompt_text: str,
    profile: str,
    expected_artifact_paths: list[Path],
    target_cwd: Path,
) -> None:
    sections = [
        "---",
        "task: gemini-cli-runner-launch",
        f"source_prompt: {source_prompt}",
        f"prompt_profile: {profile}",
        f"target_cwd: {target_cwd}",
        "---",
        "",
    ]
    if profile == "gemini":
        sections.extend([GEMINI_ADAPTER, ""])
    sections.extend(
        [
            "## Target Working Directory",
            "",
            f"The caller's target working directory is `{target_cwd}`.",
            "",
            "## Expected Artifacts",
            "",
        ]
    )
    if expected_artifact_paths:
        sections.extend(f"- `{path}`" for path in expected_artifact_paths)
    else:
        sections.append("- No explicit expected artifacts were provided by the runner.")
    sections.extend(
        [
            "",
            "## Source Prompt",
            "",
            "The complete source prompt is embedded below. Follow it directly; do not try to reread it from another file path.",
            "",
            "<source_prompt>",
            source_prompt_text,
            "</source_prompt>",
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


def record_is_final_success(record: dict[str, Any] | None) -> bool:
    if not record:
        return False
    record_type = str(record.get("type", "")).lower()
    record_status = str(record.get("status", "")).lower()
    return record_type == "result" and record_status == "success"


def stderr_has_cli_error(stderr_text: str) -> bool:
    return any(FATAL_STDERR_RE.search(line) for line in stderr_text.splitlines())


def has_raw_mode_error(*texts: str) -> bool:
    return any(RAW_MODE_RE.search(text) for text in texts if text)


def write_failure(path: Path, summary: dict[str, Any]) -> None:
    command = " ".join(summary["command"])
    last = summary.get("last_error_record") or summary.get("last_stream_record") or {}
    missing = [
        item for item in summary["expected_artifacts"] if not item["exists"] or not item["non_empty"]
    ]
    reasons = summary.get("failure_reasons", [])
    recommendation = summary.get("recommended_next_action", "Inspect artifacts and rerun with adjusted limits.")

    body = [
        "# Gemini CLI Run Failure",
        "",
        f"- Command: `{command}`",
        f"- Exit code: `{summary['exit_code']}`",
        f"- Elapsed seconds: `{summary['elapsed_seconds']}`",
        f"- Stream bytes: `{summary['stream_bytes']}`",
        f"- Stderr bytes: `{summary['stderr_bytes']}`",
        f"- Failure reasons: {', '.join(reasons) if reasons else 'unknown'}",
        "",
        "## Last Error Or Stream Record",
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
    prompt_profile = resolve_prompt_profile(args.prompt_profile)
    expected_artifact_paths = [artifact_path(raw, output_dir) for raw in args.expected_artifact]
    source_prompt_text = prompt_file.read_text(encoding="utf-8", errors="replace")
    write_launch_prompt(
        launch_prompt_path,
        prompt_file,
        source_prompt_text,
        prompt_profile,
        expected_artifact_paths,
        cwd,
    )

    short_prompt = (
        f"Read and follow ./{launch_prompt_path.name} in the current working directory. "
        "Write only the requested artifacts exactly where specified."
    )
    extra_gemini_args = list(args.extra_gemini_arg)
    if str(cwd) != str(output_dir) and "--include-directories" not in extra_gemini_args:
        extra_gemini_args.extend(["--include-directories", str(cwd)])
    command = [
        timeout_bin,
        str(args.timeout_seconds),
        args.gemini_bin,
    ]
    if args.model:
        command.extend(["--model", args.model])
    if args.approval_mode:
        command.extend(["--approval-mode", args.approval_mode])
    command.extend(extra_gemini_args)
    command.extend(["-p", short_prompt, "--output-format", "stream-json"])

    start = time.monotonic()
    with stream_path.open("wb") as stdout_fh, stderr_path.open("wb") as stderr_fh:
        proc = subprocess.run(
            command,
            cwd=str(output_dir),
            stdin=subprocess.DEVNULL,
            stdout=stdout_fh,
            stderr=stderr_fh,
            check=False,
        )
    elapsed = round(time.monotonic() - start, 3)

    records = load_json_lines(stream_path)
    error_records = [record for record in records if record_is_error(record)]
    last_stream_record = records[-1] if records else None
    last_error_record = error_records[-1] if error_records else None
    final_stream_success = record_is_final_success(last_stream_record)
    stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.exists() else ""
    stream_text = stream_path.read_text(encoding="utf-8", errors="replace") if stream_path.exists() else ""
    stderr_error = stderr_has_cli_error(stderr_text)
    raw_mode_error = has_raw_mode_error(stderr_text, stream_text)

    expected = []
    for path in expected_artifact_paths:
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

    stream_missing = not stream_path.exists() or stream_path.stat().st_size == 0
    missing_expected_artifact = any(not item["exists"] or not item["non_empty"] for item in expected)
    success_evidence_ok = (
        proc.returncode == 0
        and not stream_missing
        and final_stream_success
        and not raw_mode_error
        and not missing_expected_artifact
    )
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
    if raw_mode_error:
        failure_reasons.append("raw_mode_tty_error")
    if error_records:
        if success_evidence_ok:
            nonfatal_reasons.append("stream_error")
        else:
            failure_reasons.append("stream_error")
    if stream_missing:
        failure_reasons.append("missing_stream")
    elif not final_stream_success:
        failure_reasons.append("missing_final_success")
    if missing_expected_artifact:
        failure_reasons.append("missing_expected_artifact")

    if "timeout" in failure_reasons:
        recommended = "Inspect run.stream.jsonl for partial progress, then rerun with a tighter prompt or larger timeout."
    elif "raw_mode_tty_error" in failure_reasons:
        recommended = "Gemini CLI attempted raw terminal mode in a noninteractive run; inspect run.stream.jsonl/run.err and let the caller materialize a blocked artifact."
    elif "stderr_cli_error" in failure_reasons:
        recommended = "Fix authentication, model, permission, trust, policy, quota, or rate-limit settings before rerunning."
    elif "missing_expected_artifact" in failure_reasons:
        recommended = "Check the prompt artifact path contract and rerun with an explicit expected output path."
    elif "missing_final_success" in failure_reasons:
        recommended = "Inspect the last stream record; rerun if Gemini did not emit a final result success."
    elif "stream_error" in failure_reasons:
        recommended = "Inspect last_error_record, run.stream.jsonl, and run.err, then rerun with an adjusted prompt or access policy."
    elif nonfatal_reasons:
        recommended = "Run succeeded with non-fatal Gemini warnings; inspect nonfatal_reasons, last_error_record, and run.err if task quality is suspicious."
    elif not failure_reasons:
        recommended = "Run succeeded; evaluate task-specific artifact quality against the source prompt."
    else:
        recommended = "Inspect run.stream.jsonl and run.err, then rerun with adjusted prompt, model, approval mode, extra args, or timeout."

    summary = {
        "command": command,
        "gemini_bin": args.gemini_bin,
        "cwd": str(cwd),
        "target_cwd": str(cwd),
        "process_cwd": str(output_dir),
        "prompt_file": str(prompt_file),
        "launch_prompt_path": str(launch_prompt_path),
        "prompt_profile": prompt_profile,
        "output_dir": str(output_dir),
        "exit_code": proc.returncode,
        "elapsed_seconds": elapsed,
        "stream_path": str(stream_path),
        "stderr_path": str(stderr_path),
        "stream_bytes": stream_path.stat().st_size if stream_path.exists() else 0,
        "stderr_bytes": stderr_path.stat().st_size if stderr_path.exists() else 0,
        "record_count": len(records),
        "last_stream_record": last_stream_record,
        "last_error_record": last_error_record,
        "final_stream_success": final_stream_success,
        "stderr_cli_error": stderr_error,
        "raw_mode_tty_error": raw_mode_error,
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
