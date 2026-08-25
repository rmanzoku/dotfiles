#!/usr/bin/env python3
"""No-API regression checks for Copilot runner budget preflight."""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).with_name("run_copilot_cli.py")
REPO = pathlib.Path(__file__).resolve().parents[3]
CONTEXT = REPO / ".context"


class CopilotBudgetPreflightTest(unittest.TestCase):
    def setUp(self) -> None:
        CONTEXT.mkdir(exist_ok=True)
        self.tempdir = tempfile.TemporaryDirectory(prefix="copilot-runner-test-", dir=CONTEXT)
        self.root = pathlib.Path(self.tempdir.name)
        self.prompt = self.root / "prompt.md"
        self.prompt.write_text("Return ok without external side effects.\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_wrapper(self, *budget_args: str) -> subprocess.CompletedProcess[str]:
        output_dir = self.root / f"run-{len(list(self.root.glob('run-*')))}"
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--prompt-file",
                str(self.prompt),
                "--output-dir",
                str(output_dir),
                "--model",
                "claude-fable-5",
                "--copilot-bin",
                "copilot",
                "--timeout-bin",
                "/usr/bin/true",
                *budget_args,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_positive_fable_cap_below_legacy_floor_reaches_execution(self) -> None:
        result = self.run_wrapper("--max-ai-credits", "50")
        self.assertNotEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Fable 5 runs require --max-ai-credits >=", result.stderr)

    def test_uncapped_fable_is_rejected(self) -> None:
        result = self.run_wrapper("--allow-uncapped")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Fable 5 runs require --max-ai-credits", result.stderr)


if __name__ == "__main__":
    unittest.main()
