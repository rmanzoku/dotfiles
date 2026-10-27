"""Codex JSON-RPC client. Own a stdio server or connect to an existing daemon."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import queue
import socket
import struct
import subprocess
import sys
import threading
import time
from pathlib import Path


DEFAULT_OBJECTIVE = (
    "Complete the request in the first message, satisfying all of its Success criteria. "
    "Stop as blocked only when its Stop only if conditions apply."
)


def log(message):
    # Never include prompts, tool arguments, server error bodies, or credentials here.
    print(f"[codex-runner {time.strftime('%H:%M:%S')}] {message}", file=sys.stderr, flush=True)


class ServerExited(Exception):
    pass


class RpcError(Exception):
    pass


class UnixWebSocket:
    def __init__(self, path, timeout):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.buffer = b""
        try:
            self.sock.connect(str(path))
            key = base64.b64encode(os.urandom(16)).decode()
            self.sock.sendall((
                "GET / HTTP/1.1\r\nHost: localhost\r\nUpgrade: websocket\r\n"
                f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
                "Sec-WebSocket-Version: 13\r\n\r\n"
            ).encode())
            # Read exactly through the HTTP header, preserving any first frame.
            while b"\r\n\r\n" not in self.buffer:
                chunk = self.sock.recv(4096)
                if not chunk:
                    raise ServerExited()
                self.buffer += chunk
                if len(self.buffer) > 65536:
                    raise ValueError("WebSocket upgrade header too large")
            header, self.buffer = self.buffer.split(b"\r\n\r\n", 1)
            lines = header.decode("ascii").split("\r\n")
            headers = {name.lower(): value for name, value in
                       (line.split(":", 1) for line in lines[1:] if ":" in line)}
            accept = base64.b64encode(hashlib.sha1(
                (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()
            ).digest()).decode()
            if " 101 " not in lines[0] or headers.get("sec-websocket-accept", "").strip() != accept:
                raise ValueError("WebSocket upgrade rejected")
            self.sock.settimeout(None)
        except BaseException:
            self.sock.close()
            raise
        self.lock = threading.Lock()

    def send(self, data, opcode=1):
        mask = os.urandom(4)
        length = len(data)
        header = bytes([0x80 | opcode])
        if length < 126:
            header += bytes([0x80 | length])
        elif length < 65536:
            header += bytes([0xFE]) + struct.pack(">H", length)
        else:
            header += bytes([0xFF]) + struct.pack(">Q", length)
        with self.lock:
            self.sock.sendall(header + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def read(self, size):
        while len(self.buffer) < size:
            chunk = self.sock.recv(max(4096, size - len(self.buffer)))
            if not chunk:
                raise ServerExited()
            self.buffer += chunk
        data, self.buffer = self.buffer[:size], self.buffer[size:]
        return data

    def messages(self):
        fragments = b""
        while True:
            first, second = self.read(2)
            opcode, length = first & 15, second & 127
            if length == 126:
                length = struct.unpack(">H", self.read(2))[0]
            elif length == 127:
                length = struct.unpack(">Q", self.read(8))[0]
            if second & 128 or length > 64 * 1024 * 1024:
                raise ValueError("Invalid server WebSocket frame")
            data = self.read(length)
            if opcode == 8:
                raise ServerExited()
            if opcode == 9:
                self.send(data, 10)
            elif opcode == 10:
                continue
            elif opcode in (0, 1):
                fragments += data
                if first & 128:
                    yield fragments.decode("utf-8")
                    fragments = b""
            else:
                raise ValueError("Unsupported WebSocket opcode")

    def close(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.sock.close()


class Client:
    def __init__(self, command, cwd, daemon_path, stderr, events, deadline):
        self.proc = None
        self.ws = None
        self.events = events
        self.deadline = deadline
        self.inbox = queue.Queue()
        self.next_id = 1
        self.responses = {}
        self.thread_id = None
        self.turn_id = None
        self.active_turns = set()
        self.started_turns = set()
        self.completed_turns = set()
        self.goal = None
        self.last_message = ""
        self.failures = []
        self.nonfatal = []
        self.last_heartbeat = time.monotonic()
        if daemon_path:
            self.ws = UnixWebSocket(daemon_path, max(0.01, deadline - time.monotonic()))
        else:
            self.proc = subprocess.Popen(command, cwd=str(cwd), stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE, stderr=stderr, text=True, bufsize=1)
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        try:
            for line in self.ws.messages() if self.ws else self.proc.stdout:
                if line.strip():
                    message = json.loads(line)
                    if not isinstance(message, dict):
                        raise ValueError("JSON-RPC message must be an object")
                    self.inbox.put(("message", message))
            self.inbox.put(("eof", None))
        except ServerExited:
            self.inbox.put(("eof", None))
        except Exception as exc:
            self.inbox.put(("client_error", type(exc).__name__))

    def record(self, direction, message):
        self.events.write(json.dumps({"direction": direction, "message": message}, ensure_ascii=False) + "\n")
        self.events.flush()

    def send(self, message):
        self.record("client_to_server", message)
        line = json.dumps(message, ensure_ascii=False)
        try:
            if self.ws:
                self.ws.send(line.encode())
            else:
                self.proc.stdin.write(line + "\n")
                self.proc.stdin.flush()
        except (BrokenPipeError, ConnectionError):
            raise ServerExited() from None

    def request(self, method, params, deadline=None):
        request_id = self.next_id
        self.next_id += 1
        self.send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        while request_id not in self.responses:
            self.pump(deadline)
        response = self.responses.pop(request_id)
        if "error" in response:
            raise RpcError(method)
        return response["result"]

    def pump(self, deadline=None):
        remaining = (self.deadline if deadline is None else deadline) - time.monotonic()
        if remaining <= 0:
            raise TimeoutError()
        try:
            kind, message = self.inbox.get(timeout=min(remaining, 1))
        except queue.Empty:
            if time.monotonic() - self.last_heartbeat >= 120:
                log(f"waiting turns={len(self.started_turns)} goal={(self.goal or {}).get('status', 'disabled')}")
                self.last_heartbeat = time.monotonic()
            return
        if kind == "eof":
            raise ServerExited()
        if kind == "client_error":
            raise ValueError(message)
        self.record("server_to_client", message)
        if "id" in message and "method" not in message:
            self.responses[message["id"]] = message
            return
        method = message.get("method", "")
        if "id" in message:
            # Fail closed for every server request, including approvals and user input.
            self.nonfatal.append("server_request_rejected:" + method)
            log("server request rejected")
            self.send({"jsonrpc": "2.0", "id": message["id"], "error": {
                "code": -32601, "message": "Non-interactive runner rejects server requests"
            }})
            return
        params = message.get("params", {})
        if params.get("threadId") != self.thread_id or self.thread_id is None:
            return
        if method == "turn/started":
            turn_id = params["turn"]["id"]
            self.turn_id = turn_id
            self.active_turns.add(turn_id)
            self.started_turns.add(turn_id)
            log(f"turn started count={len(self.started_turns)}")
        elif method == "turn/completed":
            turn = params["turn"]
            self.active_turns.discard(turn["id"])
            self.completed_turns.add(turn["id"])
            log("turn completed status=" + turn["status"])
            if turn["status"] != "completed":
                self.failures.append("turn_" + turn["status"])
        elif method == "thread/goal/updated":
            self.goal = params["goal"]
            log("goal updated status=" + self.goal["status"])
        elif method == "item/completed" and params.get("item", {}).get("type") == "agentMessage":
            self.last_message = params["item"]["text"]
        elif method == "error":
            if params.get("willRetry"):
                self.nonfatal.append("server_error_retrying")
            else:
                self.failures.append("server_error")

    def interrupt(self):
        if self.thread_id and self.turn_id:
            log("interrupt requested")
            self.request("turn/interrupt", {"threadId": self.thread_id, "turnId": self.turn_id},
                         deadline=time.monotonic() + 5)

    def close(self):
        if self.ws:
            self.ws.close()
        if self.proc:
            if self.proc.poll() is None:
                self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
        self.reader.join(timeout=1)
        # Preserve already-received traffic even when the terminal notification came first.
        while not self.inbox.empty():
            kind, message = self.inbox.get_nowait()
            if kind == "message":
                self.record("server_to_client", message)
        if self.proc:
            self.proc.stdin.close()
            self.proc.stdout.close()


def run_app_server(args, cwd, short_prompt, events_path, stderr_path, last_message_path):
    command = [args.codex_bin]
    command += ["app-server", "--stdio"]
    daemon_path = None
    if args.app_server_daemon:
        daemon_path = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "app-server-control/app-server-control.sock"
        command = []  # No subprocess or daemon lifecycle commands are executed.
    result = {
        "command": command, "transport": "app-server-daemon" if daemon_path else "app-server-stdio",
        "thread_id": None, "goal": None, "turn_count": 0,
        "exit_code": 0, "failure_reasons": [], "nonfatal_reasons": [],
    }
    deadline = time.monotonic() + args.timeout_seconds
    client = None
    log("start transport=" + result["transport"])
    with events_path.open("w", encoding="utf-8") as events, stderr_path.open("w", encoding="utf-8") as stderr:
        try:
            objective = args.goal_objective or DEFAULT_OBJECTIVE
            if args.goal_objective_file:
                objective = Path(args.goal_objective_file).expanduser().read_text(encoding="utf-8")
            if not args.no_goal and not objective.strip():
                raise ValueError("Empty goal objective")
            client = Client(command, cwd, daemon_path, stderr, events, deadline)
            client.request("initialize", {
                "clientInfo": {"name": "codex-runner", "version": "1"},
                "capabilities": {"experimentalApi": True},
            })
            client.send({"jsonrpc": "2.0", "method": "initialized"})
            params = {"cwd": str(cwd)}
            if args.model:
                params["model"] = args.model
            thread = client.request("thread/start", params)
            client.thread_id = thread["thread"]["id"]
            if not args.no_goal:
                client.goal = client.request("thread/goal/set", {
                    "threadId": client.thread_id, "objective": objective,
                    "status": "active", "origin": "user",
                })["goal"]
                log("goal set status=" + client.goal["status"])
            params = {"threadId": client.thread_id, "input": [{"type": "text", "text": short_prompt}]}
            if args.effort:
                params["effort"] = args.effort
            turn = client.request("turn/start", params)
            client.turn_id = turn["turn"]["id"]
            while True:
                terminal = client.goal and client.goal["status"] != "active"
                if terminal and client.goal["status"] != "complete":
                    client.failures.append("goal_" + client.goal["status"])
                    break
                if client.failures:
                    break
                # Goal audits may schedule further turns; a completed turn alone is insufficient.
                if client.completed_turns and not client.active_turns and (args.no_goal or terminal):
                    break
                client.pump()
            if not args.no_goal:
                client.goal = client.request("thread/goal/get", {"threadId": client.thread_id})["goal"]
                if not client.goal or client.goal["status"] != "complete":
                    reason = "goal_" + (client.goal or {}).get("status", "missing")
                    if reason not in client.failures:
                        client.failures.append(reason)
        except TimeoutError:
            result["exit_code"] = 124
            result["failure_reasons"].append("timeout")
        except ServerExited:
            result["exit_code"] = 1
            result["failure_reasons"].append("server_exited")
        except RpcError as exc:
            result["exit_code"] = 1
            result["failure_reasons"].append("rpc_error:" + str(exc))
        except Exception as exc:
            result["exit_code"] = 1
            result["failure_reasons"].append("client_error")
            # Exception type is useful without leaking server content or credentials.
            stderr.write("client_error: " + type(exc).__name__ + "\n")
        finally:
            if client:
                if result["failure_reasons"] or client.failures:
                    try:
                        client.interrupt()
                    except Exception:
                        result["nonfatal_reasons"].append("interrupt_failed")
                result["thread_id"] = client.thread_id
                result["goal"] = client.goal
                result["turn_count"] = len(client.started_turns)
                result["failure_reasons"].extend(client.failures)
                result["nonfatal_reasons"].extend(client.nonfatal)
                if client.last_message:
                    last_message_path.write_text(client.last_message, encoding="utf-8")
                client.close()
    if result["failure_reasons"] and result["exit_code"] == 0:
        result["exit_code"] = 1
    return result
