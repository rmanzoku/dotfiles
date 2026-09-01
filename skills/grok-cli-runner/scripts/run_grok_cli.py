#!/usr/bin/env python3
"""Run a Grok Build CLI handoff with observable artifacts."""

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


DEFAULT_OUTPUT_FORMAT = "json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a request artifact through Grok Build CLI headless mode."
    )
    parser.add_argument("--request-file", required=True, help="Path to .context/<task>/grok-request.json.")
    parser.add_argument("--output-dir", required=True, help="Directory for run artifacts.")
    parser.add_argument(
        "--response-artifact",
        default="grok-response.json",
        help="Response artifact path. Relative paths resolve from --output-dir; use absolute paths for artifacts outside it.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model override. Omit to use request.model, GROK_BUILD_MODEL, GROK_MODEL, or the Grok Build CLI default model.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=600, help="Process timeout in seconds. Defaults to 600.")
    parser.add_argument("--cwd", default=os.getcwd(), help="Working directory passed to Grok Build and used for the subprocess.")
    parser.add_argument("--timeout-bin", default=None, help="Timeout binary. Defaults to timeout, then gtimeout.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and record the command without calling Grok Build.")
    parser.add_argument(
        "--grok-bin",
        default=os.getenv("GROK_BIN", "grok"),
        help="Grok Build executable. Defaults to GROK_BIN or grok.",
    )
    parser.add_argument(
        "--output-format",
        choices=("json", "streaming-json", "plain"),
        default=os.getenv("GROK_OUTPUT_FORMAT", DEFAULT_OUTPUT_FORMAT),
        help="Grok Build output format. Defaults to GROK_OUTPUT_FORMAT or json.",
    )
    parser.add_argument(
        "--permission-mode",
        default=os.getenv("GROK_PERMISSION_MODE", "auto"),
        help="Permission mode for headless Grok Build. Defaults to GROK_PERMISSION_MODE or auto.",
    )
    parser.add_argument(
        "--no-plan",
        action="store_true",
        default=True,
        help="Pass --no-plan to Grok Build. Use for retrieval or direct-answer tasks where plan mode prevents tool execution.",
    )
    parser.add_argument(
        "--plan",
        action="store_false",
        dest="no_plan",
        help="Do not pass --no-plan. Use only when Grok Build plan mode is explicitly desired.",
    )
    parser.add_argument(
        "--no-verbatim",
        action="store_true",
        help="Do not pass --verbatim. By default the wrapper sends the derived prompt verbatim.",
    )
    parser.add_argument("--session-id", default=None, help="Create or resume a named Grok Build headless session.")
    parser.add_argument("--resume", default=None, help="Resume an existing Grok Build session ID.")
    parser.add_argument(
        "--continue-session",
        action="store_true",
        help="Continue the most recent Grok Build session in the current directory.",
    )
    parser.add_argument(
        "--always-approve",
        action="store_true",
        help=(
            "Pass --always-approve to Grok Build and omit --permission-mode "
            "(grok 0.2.112 lets an explicit --permission-mode override --always-approve). "
            "Use only when the caller explicitly accepts tool side effects."
        ),
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


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"request artifact not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"request artifact is not valid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("request artifact must be a JSON object")
    return value


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"request artifact must include non-empty string '{key}'")
    return value.strip()


def resolve_model(request_data: dict[str, Any], override: str | None) -> str | None:
    if override:
        return override
    request_obj = request_data.get("request")
    if isinstance(request_obj, dict) and isinstance(request_obj.get("model"), str) and request_obj["model"].strip():
        return request_obj["model"].strip()
    return os.getenv("GROK_BUILD_MODEL") or os.getenv("GROK_MODEL") or None


def compact_json(value: Any, limit: int = 4000) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)[:limit]


def content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content")
                parts.append(text if isinstance(text, str) else compact_json(item))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part)
    return compact_json(content)


def load_request_payload(data: dict[str, Any], *, model: str | None) -> dict[str, Any]:
    require_string(data, "task")
    request_data = data.get("request")
    if not isinstance(request_data, dict):
        raise ValueError("request artifact must include object 'request'")
    payload = dict(request_data)
    if model:
        payload["model"] = model
    else:
        payload.pop("model", None)
    if "input" not in payload:
        raise ValueError("request.request must include 'input'")
    if "instructions" in payload:
        raise ValueError("request.request must not include 'instructions'; put instruction text in request.input")
    return payload


def payload_to_prompt(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    request_input = payload.get("input")
    if isinstance(request_input, str):
        lines.extend(["User request:", request_input])
    elif isinstance(request_input, list):
        lines.append("Conversation:")
        for item in request_input:
            if isinstance(item, dict):
                role = item.get("role", "message")
                lines.append(f"[{role}]")
                lines.append(content_to_text(item.get("content", "")))
            else:
                lines.append(content_to_text(item))
    else:
        lines.extend(["Input:", content_to_text(request_input)])

    passthrough_fields = {
        key: value
        for key, value in payload.items()
        if key not in {"input", "model"} and value not in (None, [], {})
    }
    if passthrough_fields:
        lines.extend(
            [
                "",
                "Additional request fields to honor when applicable:",
                compact_json(passthrough_fields),
            ]
        )
    return "\n".join(lines).strip()


def log_progress(message: str) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"[grok-cli-runner] {timestamp} {message}", flush=True)


def build_grok_command(args: argparse.Namespace, timeout_bin: str, payload: dict[str, Any], prompt: str) -> list[str]:
    command = [
        timeout_bin,
        str(args.timeout_seconds),
        args.grok_bin,
        "--no-auto-update",
        "-p",
        prompt,
        "--output-format",
        args.output_format,
        "--cwd",
        str(Path(args.cwd).expanduser().resolve()),
    ]
    model = payload.get("model")
    if model:
        command.extend(["-m", str(model)])
    # grok 0.2.112: an explicit --permission-mode overrides --always-approve
    # (contrary to its docs), so the two flags must never be sent together.
    if args.permission_mode and not args.always_approve:
        command.extend(["--permission-mode", args.permission_mode])
    if args.no_plan:
        command.append("--no-plan")
    if not args.no_verbatim:
        command.append("--verbatim")
    if args.always_approve:
        command.append("--always-approve")
    if args.session_id:
        command.extend(["--session-id", args.session_id])
    if args.resume:
        command.extend(["--resume", args.resume])
    if args.continue_session:
        command.append("--continue")
    return command


def redact_command(command: list[str]) -> list[str]:
    redacted = list(command)
    for index, item in enumerate(redacted):
        if item == "-p" and index + 1 < len(redacted):
            redacted[index + 1] = "<prompt from request artifact>"
    return redacted


def parse_stdout(raw_stdout: str, output_format: str) -> tuple[Any, str | None]:
    text = raw_stdout.strip()
    if not text:
        return None, None
    if output_format == "plain":
        return {"type": "plain", "text": text}, text
    if output_format == "streaming-json":
        events: list[Any] = []
        for line in text.splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                events.append({"type": "unparsed_line", "text": line})
        return {"type": "streaming-json", "events": events}, extract_text_from_value(events) or text
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"type": "unparsed_json_stdout", "text": text}, text
    return parsed, extract_text_from_value(parsed) or text


def extract_text_from_value(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, dict):
        for key in ("output_text", "result", "response", "message", "content", "text", "answer"):
            text = extract_text_from_value(value.get(key))
            if text:
                return text
        output = value.get("output")
        text = extract_text_from_value(output)
        if text:
            return text
    if isinstance(value, list):
        parts = [extract_text_from_value(item) for item in value]
        joined = "\n".join(part for part in parts if part)
        return joined or None
    return None


def extract_stop_reason(parsed_stdout: Any) -> str | None:
    if not isinstance(parsed_stdout, dict):
        return None
    value = parsed_stdout.get("stopReason")
    if isinstance(value, str) and value:
        return value
    events = parsed_stdout.get("events")
    if isinstance(events, list):
        for event in reversed(events):
            if isinstance(event, dict):
                value = event.get("stopReason")
                if isinstance(value, str) and value:
                    return value
    return None


def is_end_turn(stop_reason: str | None) -> bool:
    # Grok CLI stop-reason spelling varies by version (EndTurn vs end_turn),
    # so compare lowercased with "_" and "-" removed.
    if not isinstance(stop_reason, str):
        return False
    return stop_reason.lower().replace("_", "").replace("-", "") == "endturn"


def run_grok_build(
    args: argparse.Namespace,
    command: list[str],
    request_artifact: dict[str, Any],
    payload: dict[str, Any],
    response_path: Path,
    stderr_path: Path,
) -> tuple[int, str | None]:
    if not shutil.which(args.grok_bin):
        raise RuntimeError(
            f"Grok Build executable not found: {args.grok_bin}. Install with `curl -fsSL https://x.ai/cli/install.sh | bash` "
            "and authenticate with `grok login`, `grok login --device-auth`, or XAI_API_KEY."
        )
    log_progress(f"starting Grok Build headless run timeout_seconds={args.timeout_seconds}")
    with stderr_path.open("wb") as stderr_fh:
        proc = subprocess.run(
            command,
            cwd=str(Path(args.cwd).expanduser().resolve()),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=stderr_fh,
            check=False,
        )
    if proc.returncode != 0:
        log_progress(f"Grok Build headless run failed exit_code={proc.returncode}")
        return proc.returncode, None
    stdout_text = proc.stdout.decode("utf-8", errors="replace")
    parsed_stdout, output_text = parse_stdout(stdout_text, args.output_format)
    stop_reason = extract_stop_reason(parsed_stdout)
    artifact = {
        "task": require_string(request_artifact, "task"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "meta": request_artifact.get("meta"),
        "request": payload,
        "response": {
            "type": "grok_build_cli_response",
            "output_format": args.output_format,
            "stdout_bytes": len(proc.stdout),
            "parsed_stdout": parsed_stdout,
        },
        "output_text": output_text,
        "response_id": None,
        "model": payload.get("model"),
        "backend": "grok-build",
    }
    write_json(response_path, artifact)
    if args.output_format in {"json", "streaming-json"} and not is_end_turn(stop_reason):
        log_progress(f"Grok Build turn did not complete stop_reason={stop_reason}")
    else:
        log_progress(f"completed Grok Build headless run bytes={len(proc.stdout)}")
    return 0, stop_reason


def classify_failure_reasons(
    *,
    exit_code: int,
    api_error: dict[str, Any] | None,
    response_non_empty: bool,
    dry_run: bool,
    stop_reason: str | None,
    output_format: str,
) -> list[str]:
    reasons: list[str] = []
    if exit_code == 124:
        reasons.append("timeout")
    elif exit_code != 0:
        reasons.append("nonzero_exit")
    if api_error:
        message = api_error.get("message", "")
        if "Grok Build executable not found" in message:
            reasons.append("missing_grok")
        elif "input" in message or "request artifact" in message or "instructions" in message:
            reasons.append("invalid_request")
        else:
            reasons.append("grok_build_error")
    if (
        not dry_run
        and exit_code == 0
        and output_format in {"json", "streaming-json"}
        and not is_end_turn(stop_reason)
    ):
        reasons.append("stop_reason_not_end_turn")
    if not dry_run and not response_non_empty and "missing_grok" not in reasons and "invalid_request" not in reasons:
        reasons.append("missing_response_artifact")
    return reasons


def recommended_next_action(failure_reasons: list[str], *, dry_run: bool) -> str:
    if dry_run and not failure_reasons:
        return "Dry-run succeeded; inspect summary.json dry_run_payload and command before making a real call."
    if "missing_grok" in failure_reasons:
        return "Install Grok Build CLI, authenticate with `grok login` or `grok login --device-auth`, or provide XAI_API_KEY, then rerun."
    if "timeout" in failure_reasons:
        return "Inspect request size and Grok Build state, then rerun with a smaller request or larger --timeout-seconds."
    if "invalid_request" in failure_reasons:
        return "Fix grok-request.json against references/schema.md, then rerun with --dry-run before a real call."
    if "stop_reason_not_end_turn" in failure_reasons:
        return (
            "Grok Build ended the turn without completing (stop_reason does not normalize to end_turn; Cancelled usually means a headless "
            "permission prompt nobody could answer). For tasks with shell or file side effects rerun with "
            "--permission-mode bypassPermissions, and inspect events.jsonl under ~/.grok/sessions/ for permission_cancelled."
        )
    if "missing_response_artifact" in failure_reasons:
        return "Inspect run.err and Grok Build stdout behavior, then rerun after fixing auth, model, permission mode, or request shape."
    return "Inspect summary.json and grok-response.json, then integrate the response in the caller."


def write_failure(path: Path, summary: dict[str, Any]) -> None:
    reasons = summary.get("failure_reasons", [])
    api_error = summary.get("api_error") or {}
    body = [
        "# Grok CLI Runner Failure",
        "",
        f"- Command: `{' '.join(summary['command'])}`",
        f"- Exit code: `{summary['exit_code']}`",
        f"- Stop reason: `{summary.get('stop_reason')}`",
        f"- Elapsed seconds: `{summary['elapsed_seconds']}`",
        f"- Request bytes: `{summary['request_bytes']}`",
        f"- Response artifact: `{summary['response_artifact']}`",
        f"- Response non-empty: `{summary['response_non_empty']}`",
        f"- Response bytes: `{summary['response_bytes']}`",
        f"- Stderr bytes: `{summary['stderr_bytes']}`",
        f"- Failure reasons: {', '.join(reasons) if reasons else 'unknown'}",
        "",
        "## API Or Validation Error",
        "",
        "```json",
        compact_json(api_error),
        "```",
        "",
        "## Recommended Next Action",
        "",
        summary.get("recommended_next_action", "Inspect artifacts and rerun with adjusted request or environment."),
        "",
    ]
    path.write_text("\n".join(body), encoding="utf-8")


def main() -> int:
    args = parse_args()
    request_path = Path(args.request_file).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    response_path = artifact_path(args.response_artifact, output_dir)
    stderr_path = output_dir / "run.err"
    summary_path = output_dir / "summary.json"
    failure_path = output_dir / "failure.md"
    output_dir.mkdir(parents=True, exist_ok=True)

    timeout_bin = resolve_timeout_bin(args.timeout_bin)
    start = time.monotonic()
    api_error: dict[str, Any] | None = None
    dry_run_payload: dict[str, Any] | None = None
    exit_code = 0
    stop_reason: str | None = None
    model_used = args.model or os.getenv("GROK_BUILD_MODEL") or os.getenv("GROK_MODEL") or None
    command: list[str] = []
    prompt_bytes = 0

    try:
        request_data = load_json(request_path)
        model = resolve_model(request_data, args.model)
        model_used = model
        payload = load_request_payload(request_data, model=model)
        prompt = payload_to_prompt(payload)
        prompt_bytes = len(prompt.encode("utf-8"))
        command = build_grok_command(args, timeout_bin, payload, prompt)
        if args.dry_run:
            dry_run_payload = {
                "request": payload,
                "prompt_bytes": prompt_bytes,
                "command": redact_command(command),
            }
            stderr_path.write_text("", encoding="utf-8")
        else:
            exit_code, stop_reason = run_grok_build(args, command, request_data, payload, response_path, stderr_path)
    except Exception as exc:  # noqa: BLE001 - convert all local/backend failures to artifacts
        exit_code = 1
        api_error = {"type": exc.__class__.__name__, "message": str(exc)}

    elapsed = round(time.monotonic() - start, 3)
    request_bytes = request_path.stat().st_size if request_path.exists() else 0
    response_non_empty = response_path.exists() and response_path.is_file() and response_path.stat().st_size > 0
    response_bytes = response_path.stat().st_size if response_path.exists() and response_path.is_file() else 0
    stderr_bytes = stderr_path.stat().st_size if stderr_path.exists() else 0
    failure_reasons = classify_failure_reasons(
        exit_code=exit_code,
        api_error=api_error,
        response_non_empty=response_non_empty,
        dry_run=args.dry_run,
        stop_reason=stop_reason,
        output_format=args.output_format,
    )
    recommended = recommended_next_action(failure_reasons, dry_run=args.dry_run)
    summary = {
        "command": redact_command(command),
        "cwd": str(Path(args.cwd).expanduser().resolve()),
        "request_file": str(request_path),
        "response_artifact": str(response_path),
        "output_dir": str(output_dir),
        "model": model_used,
        "backend": "grok-build",
        "grok_bin": args.grok_bin,
        "output_format": args.output_format,
        "permission_mode": None if args.always_approve else args.permission_mode,
        "no_plan": args.no_plan,
        "verbatim": not args.no_verbatim,
        "session_id": args.session_id,
        "resume": args.resume,
        "continue_session": args.continue_session,
        "always_approve": args.always_approve,
        "dry_run": args.dry_run,
        "dry_run_payload": dry_run_payload,
        "prompt_bytes": prompt_bytes,
        "exit_code": exit_code,
        "stop_reason": stop_reason,
        "elapsed_seconds": elapsed,
        "request_bytes": request_bytes,
        "response_bytes": response_bytes,
        "stderr_bytes": stderr_bytes,
        "response_non_empty": response_non_empty,
        "api_error": api_error,
        "success": not failure_reasons,
        "failure_reasons": failure_reasons,
        "recommended_next_action": recommended,
    }
    write_json(summary_path, summary)

    if failure_reasons:
        write_failure(failure_path, summary)
        return 1
    if failure_path.exists():
        failure_path.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
