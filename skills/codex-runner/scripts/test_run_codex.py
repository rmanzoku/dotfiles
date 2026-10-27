"""No-API protocol and artifact regression checks; all scratch data stays in .context."""

import hashlib
import base64
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import unittest

from codex_app_server import UnixWebSocket


# Run this file itself as a fake codex binary to exercise real subprocess/stdio boundaries.
def fake_server():
    mode = os.environ["FAKE_CODEX_MODE"]
    marker = os.environ.get("FAKE_CODEX_MARKER")
    if marker:
        Path(marker).write_text("started")
    if sys.argv[1:] == ["--version"]:
        print(os.environ.get("FAKE_CODEX_VERSION", "codex-cli fake-test"))
        return
    if "exec" in sys.argv:
        Path(sys.argv[sys.argv.index("-o") + 1]).write_text("done")
        print(json.dumps({"type": "event", "status": "ok"}))
        return
    goal = {"threadId": "test-thread", "status": "active", "tokensUsed": 12, "timeUsedSeconds": 1}

    def send(message):
        print(json.dumps(message), flush=True)

    def note(method, **params):
        send({"method": method, "params": {"threadId": "test-thread", **params}})

    for line in sys.stdin:
        message = json.loads(line)
        method = message.get("method")
        if method is None:
            if mode == "approval":
                assert message["id"] == "approval" and "error" in message
            continue
        if "id" not in message:
            continue
        result = {}
        if method == "initialize":
            assert message["params"]["clientInfo"]["name"] == "codex-runner"
        elif method == "thread/start":
            assert "sandbox" not in message["params"] and "approvalPolicy" not in message["params"]
            result = {"thread": {"id": "test-thread"}}
        elif method == "thread/goal/set":
            assert message["params"]["origin"] == "user"
            result = {"goal": goal}
        elif method == "thread/goal/get":
            result = {"goal": goal}
        elif method == "turn/start":
            if mode == "exited":
                return
            if mode == "malformed":
                print("not-json", flush=True)
                continue
            result = {"turn": {"id": "turn-1"}}
        send({"id": message["id"], "result": result})
        if method == "turn/start":
            note("turn/started", turn={"id": "turn-1", "status": "inProgress"})
            # Unrelated daemon threads must not affect this run.
            send({"method": "thread/goal/updated", "params": {
                "threadId": "other-thread", "goal": {"status": "blocked"}}})
            if mode == "timeout":
                continue
            if mode == "approval":
                send({"id": "approval", "method": "item/commandExecution/requestApproval", "params": {}})
            note("item/completed", item={"type": "agentMessage", "id": "answer", "text": "done"})
            note("turn/completed", turn={"id": "turn-1", "status": "completed"})
            if mode == "multi":
                note("turn/started", turn={"id": "turn-2", "status": "inProgress"})
                note("item/completed", item={"type": "agentMessage", "id": "answer2", "text": "final answer"})
                note("turn/completed", turn={"id": "turn-2", "status": "completed"})
            goal["status"] = mode if mode in {"blocked", "budgetLimited", "usageLimited", "paused"} else "complete"
            note("thread/goal/updated", goal=goal)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        root = Path.cwd() / ".context"
        root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="codex-runner-test-", dir=root)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.prompt = self.root / "prompt.md"
        self.prompt.write_text("Create the requested artifacts.")
        self.fake = self.root / "codex"
        self.fake.write_text(f"#!{sys.executable}\nimport runpy, sys\nsys.path.insert(0, {str(Path(__file__).resolve().parent)!r})\nrunpy.run_path({str(Path(__file__).resolve())!r}, run_name='fake_codex')\n")
        self.fake.chmod(0o755)

    def run_case(self, mode, *extra):
        out = self.root / mode
        command = [sys.executable, str(Path(__file__).with_name("run_codex.py")),
                   "--prompt-file", str(self.prompt), "--output-dir", str(out),
                   "--codex-bin", str(self.fake), "--timeout-seconds", "2", *extra]
        # Hold caller stdin open: app-server must use its own pipe, never inherit it.
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env={**os.environ, "FAKE_CODEX_MODE": mode})
        proc.wait(timeout=15)
        proc.stdin.close()
        stderr = proc.stderr.read().decode()
        proc.stdout.close()
        proc.stderr.close()
        summary = json.loads((out / "summary.json").read_text())
        if "--profile" not in extra or "--transport" in extra:
            self.assertIn("start transport=", stderr)
        self.assertEqual(proc.returncode == 0, summary["success"])
        return out, summary

    def test_success_and_multi_turn(self):
        for mode in ("success", "multi", "approval"):
            with self.subTest(mode=mode):
                out, summary = self.run_case(mode)
                self.assertTrue(summary["success"], summary)
                self.assertEqual(summary["codex_bin_path"], str(self.fake))
                self.assertEqual(summary["codex_version"], "codex-cli fake-test")
                self.assertEqual(summary["goal"]["status"], "complete")
                self.assertEqual(summary["turn_count"], 2 if mode == "multi" else 1)
                self.assertEqual((out / "last-message.md").read_text(), "final answer" if mode == "multi" else "done")
                records = [json.loads(line) for line in (out / "run.events.jsonl").read_text().splitlines()]
                self.assertEqual({r["direction"] for r in records}, {"client_to_server", "server_to_client"})
                if mode == "approval":
                    self.assertIn("server_request_rejected:item/commandExecution/requestApproval", summary["nonfatal_reasons"])
                    self.assertTrue(any(r["message"].get("id") == "approval" and "error" in r["message"] for r in records))

    def test_failures(self):
        cases = {"blocked": "goal_blocked", "budgetLimited": "goal_budgetLimited",
                 "usageLimited": "goal_usageLimited", "paused": "goal_paused",
                 "timeout": "timeout", "exited": "server_exited", "malformed": "client_error"}
        for mode, reason in cases.items():
            with self.subTest(mode=mode):
                out, summary = self.run_case(mode)
                self.assertFalse(summary["success"])
                self.assertIn(reason, summary["failure_reasons"])
                self.assertTrue((out / "failure.md").exists())
                if mode == "timeout":
                    records = [json.loads(line)["message"] for line in (out / "run.events.jsonl").read_text().splitlines()]
                    self.assertTrue(any(r.get("method") == "turn/interrupt" for r in records))
                    self.assertEqual(summary["exit_code"], 124)

    def test_no_goal_and_missing_artifact(self):
        _, summary = self.run_case("success", "--no-goal")
        self.assertTrue(summary["success"])
        self.assertIsNone(summary["goal"])
        _, summary = self.run_case("success", "--expected-artifact", "missing.md")
        self.assertIn("missing_expected_artifact", summary["failure_reasons"])

    def test_profile_rejected_before_any_codex_start(self):
        marker = self.root / "started"
        old = os.environ.get("FAKE_CODEX_MARKER")
        os.environ["FAKE_CODEX_MARKER"] = str(marker)
        try:
            for extra in ((), ("--app-server-daemon",)):
                out, summary = self.run_case("success", "--profile", "named", *extra)
                self.assertFalse(summary["success"])
                self.assertNotEqual(summary["exit_code"], 0)
                self.assertIn("profile_unsupported_app_server", summary["failure_reasons"])
                self.assertIn("--transport exec", summary["recommended_next_action"])
                self.assertFalse(marker.exists())
                self.assertIsNone(summary["codex_version"])
                self.assertTrue((out / "failure.md").exists())
        finally:
            if old is None:
                os.environ.pop("FAKE_CODEX_MARKER", None)
            else:
                os.environ["FAKE_CODEX_MARKER"] = old

    def test_exec_profile_and_binary_metadata(self):
        _, summary = self.run_case("success", "--transport", "exec", "--profile", "named")
        self.assertTrue(summary["success"], summary)
        self.assertEqual(summary["codex_bin_path"], str(self.fake))
        self.assertEqual(summary["codex_version"], "codex-cli fake-test")
        self.assertIn("named", summary["command"])

    def test_binary_selection_from_path_and_cwd(self):
        second_dir = self.root / "second"
        second_dir.mkdir()
        second = second_dir / "codex"
        second.write_text(self.fake.read_text().replace(
            "import runpy, sys", "import runpy, sys, os\nos.environ['FAKE_CODEX_VERSION'] = 'codex-cli second-test'"))
        second.chmod(0o755)
        original_path = os.environ["PATH"]
        try:
            for directories, selected, version in (
                ((self.root, second_dir), self.fake, "codex-cli fake-test"),
                ((second_dir, self.root), second, "codex-cli second-test"),
            ):
                os.environ["PATH"] = os.pathsep.join([*(str(p) for p in directories), original_path])
                _, summary = self.run_case("success", "--codex-bin", "codex")
                self.assertTrue(summary["success"], summary)
                self.assertEqual(summary["codex_bin"], "codex")
                self.assertEqual(summary["codex_bin_path"], str(selected))
                self.assertEqual(summary["command"][0], str(selected))
                self.assertEqual(summary["codex_version"], version)
        finally:
            os.environ["PATH"] = original_path
        _, summary = self.run_case("success", "--codex-bin", "./codex", "--cwd", str(self.root))
        self.assertTrue(summary["success"], summary)
        self.assertEqual(summary["codex_bin_path"], str(self.fake))

    def test_websocket_upgrade_fragment_ping_and_mask(self):
        path = (self.root / "daemon.sock").relative_to(Path.cwd())
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(path))
        server.listen(1)
        self.addCleanup(server.close)
        errors = []

        def serve():
            try:
                conn, _ = server.accept()
                with conn:
                    conn.settimeout(3)
                    header = b""
                    while b"\r\n\r\n" not in header:
                        header += conn.recv(4096)
                    key = next(line.split(b": ")[1] for line in header.split(b"\r\n") if line.startswith(b"Sec-WebSocket-Key"))
                    accept = base64.b64encode(hashlib.sha1(key + b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest())
                    conn.sendall(b"HTTP/1.1 101 Switching Protocols\r\nSec-WebSocket-Accept: " + accept + b"\r\n\r\n" + b'\x01\x03{"a' + b'\x89\x01p' + b'\x80\x04":1}')
                    data = b""
                    while len(data) < 7:
                        chunk = conn.recv(4096)
                        if not chunk:
                            raise EOFError()
                        data += chunk
                    self.assertEqual(data[:2], b"\x8a\x81")
                    self.assertEqual(data[6] ^ data[2], ord("p"))
            except BaseException as exc:
                errors.append(exc)

        thread = threading.Thread(target=serve)
        thread.start()
        client = UnixWebSocket(path, 3)
        self.assertEqual(next(client.messages()), '{"a":1}')
        thread.join(timeout=5)
        client.close()
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])


if __name__ == "fake_codex":
    fake_server()
elif __name__ == "__main__":
    unittest.main()
