#!/usr/bin/env python3
"""Exercise the credential boundary with fake op and a local STS endpoint."""

import contextlib
from datetime import datetime, timezone
import http.server
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest


ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "dot_local/bin/executable_op-aws-credential-process"
FAKE_OP = '''#!/usr/bin/env python3
import os, subprocess, sys
assert sys.argv[1:4] == ["run", "--account", "test-account"]
assert "--no-masking" in sys.argv
assert not any(k.startswith(("AWS_", "OP_")) for k in os.environ)
env = dict(os.environ, AWS_ACCESS_KEY_ID="test-access", AWS_SECRET_ACCESS_KEY="test-secret")
sys.exit(subprocess.call(sys.argv[sys.argv.index("--") + 1:], env=env))
'''


class CredentialProcessTests(unittest.TestCase):
    def setUp(self):
        context = ROOT / ".context"
        context.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="test-aws-process-", dir=context)
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        (self.directory / "metadata.json").write_text(json.dumps({
            "task": "aws-credential-process-tests", "phase_or_step": "validation",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }))
        self.env_file = self.directory / "profile.env"
        self.env_file.write_text('AWS_ACCESS_KEY_ID="op://test-vault/test-item/access key id"\n'
                                 'AWS_SECRET_ACCESS_KEY="op://test-vault/test-item/secret access key"\n')
        self.env_file.chmod(0o600)
        self.op = self.directory / "op"
        self.op.write_text(FAKE_OP)
        self.op.chmod(0o700)
        self.environment = dict(os.environ, PATH=f"{self.directory}:{os.environ['PATH']}",
                                AWS_ACCESS_KEY_ID="stale-access", AWS_SECRET_ACCESS_KEY="stale-secret",
                                OP_SERVICE_ACCOUNT_TOKEN="unrelated-principal")
        self.command = [sys.executable, str(HELPER), "--account", "test-account",
                        "--env-file", str(self.env_file)]

    def run_helper(self):
        return subprocess.run(self.command, env=self.environment, capture_output=True, text=True, timeout=10)

    def test_sdk_json_and_no_secret_logs(self):
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {
            "Version": 1, "AccessKeyId": "test-access", "SecretAccessKey": "test-secret"})
        for value in ("test-access", "test-secret", "op://", "test-account"):
            self.assertNotIn(value, result.stderr)
        self.assertIn("start:", result.stderr)
        self.assertIn("complete:", result.stderr)

    def test_invalid_reference_files_never_call_op(self):
        valid = self.env_file.read_text()
        invalid_cases = [
            valid.replace("op://test-vault/test-item/access key id", "plaintext"),
            valid.replace("test-item/secret", "different-item/secret"),
            valid.replace("test-vault", "$VAULT"),
            valid.replace('"', '').replace("access key id", "access key id # comment"),
            valid + 'AWS_SESSION_TOKEN="op://test-vault/test-item/token"\n',
            valid + valid,
        ]
        self.op.write_text('#!/bin/sh\necho unexpected-provider-call >&2\nexit 90\n')
        for content in invalid_cases:
            with self.subTest(content=content):
                self.env_file.write_text(content)
                result = self.run_helper()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertNotIn("unexpected-provider-call", result.stderr)
                self.assertNotIn("op exit", result.stderr)
        self.env_file.write_text(valid)
        self.env_file.chmod(0o644)
        self.assertNotEqual(self.run_helper().returncode, 0)

    def test_provider_error_is_classified_without_raw_output_or_retry(self):
        calls = self.directory / "calls"
        self.op.write_text(f'#!/usr/bin/env python3\nfrom pathlib import Path\nimport sys\n'
                           f'with Path({str(calls)!r}).open("a") as f: f.write("called\\n")\n'
                           'print("test-secret", file=sys.stderr)\n'
                           'print("account is not signed in", file=sys.stderr)\nsys.exit(1)\n')
        result = self.run_helper()
        self.assertEqual(result.stdout, "")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("account is not signed in", result.stderr)
        self.assertNotIn("test-secret", result.stderr)
        self.assertEqual(calls.read_text(), "called\n")

    def test_invalid_response_is_not_forwarded(self):
        self.op.write_text('#!/bin/sh\nprintf "test-secret invalid JSON"\n')
        result = self.run_helper()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("test-secret", result.stderr)

    def test_missing_field_diagnostic_does_not_expose_item_or_field(self):
        self.op.write_text('#!/bin/sh\necho "item private-item does not have a field private-field" >&2\nexit 1\n')
        result = self.run_helper()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("referenced field not found", result.stderr)
        self.assertNotIn("private-item", result.stderr)
        self.assertNotIn("private-field", result.stderr)

    def test_file_redirection_is_rejected(self):
        with (self.directory / "output").open("w") as stream:
            result = subprocess.run(self.command, env=self.environment, stdout=stream,
                                    stderr=subprocess.PIPE, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.directory / "output").read_text(), "")

    def test_timeout_is_bounded_and_does_not_leak(self):
        self.op.write_text('#!/usr/bin/env python3\nimport time\ntime.sleep(10)\n')
        loader = importlib.machinery.SourceFileLoader("credential_helper", str(HELPER))
        module = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
        loader.exec_module(module)
        module.TIMEOUT_SECONDS = 0.05
        old_path = os.environ["PATH"]
        os.environ["PATH"] = self.environment["PATH"]
        try:
            with contextlib.redirect_stderr(__import__("io").StringIO()) as error:
                self.assertEqual(module.fetch_credentials("test-account", self.env_file), 1)
            self.assertIn("timeout", error.getvalue())
        finally:
            os.environ["PATH"] = old_path

    @unittest.skipUnless(shutil.which("aws"), "AWS CLI is required for the consumer integration test")
    def test_real_aws_cli_consumes_credentials(self):
        requests = []

        class STS(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                requests.append(self.headers.get("Authorization", ""))
                body = (b'<GetCallerIdentityResponse xmlns="https://sts.amazonaws.com/doc/2011-06-15/">'
                        b'<GetCallerIdentityResult><Arn>arn:aws:iam::000000000000:user/test</Arn>'
                        b'<UserId>test</UserId><Account>000000000000</Account></GetCallerIdentityResult>'
                        b'<ResponseMetadata><RequestId>test</RequestId></ResponseMetadata></GetCallerIdentityResponse>')
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), STS)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        config = self.directory / "config"
        process = " ".join('"' + arg + '"' for arg in self.command)
        config.write_text(f"[profile test]\nregion = us-east-1\ncredential_process = {process}\n")
        credentials = self.directory / "credentials"
        credentials.touch()
        environment = {k: v for k, v in self.environment.items() if not k.startswith("AWS_")}
        environment.update(AWS_CONFIG_FILE=str(config), AWS_SHARED_CREDENTIALS_FILE=str(credentials),
                           AWS_EC2_METADATA_DISABLED="true", AWS_PAGER="", NO_PROXY="127.0.0.1")
        try:
            result = subprocess.run([shutil.which("aws"), "--profile", "test", "--endpoint-url",
                                     f"http://127.0.0.1:{server.server_port}", "sts", "get-caller-identity"],
                                    env=environment, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["UserId"], "test")
            self.assertEqual(len(requests), 1)
            self.assertIn("Credential=test-access/", requests[0])
            self.assertNotIn("test-secret", result.stdout + result.stderr)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
