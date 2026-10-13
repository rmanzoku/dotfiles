import subprocess
import sys
import unittest
from pathlib import Path


SOURCE = (
    Path(__file__).resolve().parents[2]
    / "dot_codex/automations/changer-issue-intake/modify_automation.toml.tmpl"
)


class IssueIntakeAutomationTests(unittest.TestCase):
    def run_modifier(self, existing):
        return subprocess.run(
            [sys.executable, str(SOURCE)],
            input=existing,
            text=True,
            capture_output=True,
        )

    def test_preserves_owner_prompt_and_app_target(self):
        local = (
            'prompt = "Use the locally approved principal and policy.\\nKeep boundaries."\n'
            'cwds = ["/owner/worktree"]\n'
            'project_id = "owner-project"\n'
            'created_at = 123\n'
        )
        result = self.run_modifier(local + 'status = "ACTIVE"\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        for line in local.splitlines():
            self.assertIn(line, result.stdout.splitlines())
        self.assertIn('status = "PAUSED"', result.stdout)
        repeated = self.run_modifier(result.stdout)
        self.assertEqual(repeated.stdout, result.stdout)

    def test_missing_or_empty_prompt_refuses_to_emit_configuration(self):
        for existing in ('', 'prompt = ""\n', 'status = "ACTIVE"\n'):
            with self.subTest(existing=existing):
                result = self.run_modifier(existing)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, '')
                self.assertIn('prompt is missing', result.stderr)


if __name__ == '__main__':
    unittest.main()
