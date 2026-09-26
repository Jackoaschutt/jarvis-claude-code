"""
JARVIS — a memory HUD driven by Claude Code.

    python3 server.py

The brain is your own `claude` CLI, so this inherits your subscription, your
tools, your MCP servers and your CLAUDE.md. The memory is a folder of markdown
you can open in Obsidian. Nothing is hosted; it binds to localhost only.
"""
import json
import mimetypes
import os
import pathlib
import secrets
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = pathlib.Path(__file__).resolve().parent
UI = ROOT / "ui"

_env = ROOT / ".env"
if _env.exists():
    for line in _env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

import commands    # noqa: E402
import journal     # noqa: E402
import memory      # noqa: E402
import runtime     # noqa: E402
import voice       # noqa: E402

PORT = int(os.environ.get("JARVIS_PORT", "8720"))

# Loopback by default, and it should stay that way unless you mean it. JARVIS
# runs `claude` with bypassPermissions in your home directory, so anything that
# can reach this port can run commands on your machine. Bind wider only over a
# private network you control (Tailscale), never a cafe or office LAN.
BIND = os.environ.get("JARVIS_BIND", "127.0.0.1").strip() or "127.0.0.1"


def _hosts():
    """Host/Origin values the browser is allowed to use. Loopback always."""
    out = {f"127.0.0.1:{PORT}", f"localhost:{PORT}"}
    for h in os.environ.get("JARVIS_HOSTS", "").split(","):
        h = h.strip()
        if h:
            out.add(h)
            if ":" not in h:
                out.add(f"{h}:{PORT}")   # bare name covers HTTPS on 443 too
    return out


HOSTS = _hosts()
API_TOKEN = secrets.token_urlsafe(32)
RUN_LOCK = threading.Lock()
# When the current turn started, so a caller that gets turned away can be
# told "still working, six minutes in" rather than a bare 409.
RUN_STARTED = {"at": 0.0}
MAX_JSON = 1024 * 1024
MAX_AUDIO = 12 * 1024 * 1024
SESSION = {"id": None}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        if os.environ.get("JARVIS_VERBOSE"):
            sys.stderr.write("  " + (fmt % args) + "\n")

    def _json(self, body, code=200):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _bytes(self, data, ctype, code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _read(self, limit):
        n = int(self.headers.get("Content-Length", 0))
        if n < 0 or n > limit:
            raise ValueError("body too large")
        return self.rfile.read(n) if n else b""

    def _host_ok(self):
        return self.headers.get("Host", "") in HOSTS

    def _origin_ok(self):
        origin = self.headers.get("Origin")
        return bool(origin) and any(origin == f"{scheme}://{h}"
                                    for h in HOSTS for scheme in ("http", "https"))

    def _token_ok(self):
        supplied = self.headers.get("X-Jarvis-Token", "")
        return bool(supplied) and secrets.compare_digest(supplied, API_TOKEN)

    def do_GET(self):
        if not self._host_ok():
            return self._json({"error": "invalid host"}, 403)
        p = urlparse(self.path).path

        if p == "/api/status":
            g = memory.build_graph()
            return self._json(dict(
                runtime=runtime.runtime_kind(), version=runtime.version(),
                model=runtime.MODEL or "Claude default", permission=runtime.PERMISSION,
                workdir=runtime.WORKDIR, vault=g["vault"], notes=g["total"],
                links=len(g["links"]), voice=voice.describe(),
                listener=voice.describe_stt(), stt=voice.stt_kind(),
                server_stt=voice.stt_kind() in ("whisper", "fish"),
                server_voice=voice.available(), session=SESSION["id"]))

        if p == "/api/graph":
            force = parse_qs(urlparse(self.path).query).get("force", ["0"])[0] == "1"
            return self._json(memory.build_graph(force=force))

        if p == "/api/note":
            title = parse_qs(urlparse(self.path).query).get("id", [""])[0].lower()
            for n in memory.build_graph()["nodes"]:
                if n["id"] == title:
                    return self._json(n)
            return self._json({"error": "not found"}, 404)

        rel = "index.html" if p == "/" else p.lstrip("/")
        f = (UI / rel).resolve()
        if not str(f).startswith(str(UI.resolve())) or not f.is_file():
            return self._bytes(b"not found", "text/plain", 404)
        data = f.read_bytes()
        if rel == "index.html":
            data = data.replace(b"__JARVIS_TOKEN__", API_TOKEN.encode())
        ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        return self._bytes(data, ctype)

    def do_POST(self):
        p = urlparse(self.path).path
        if not self._host_ok() or not self._origin_ok():
            return self._json({"error": "origin rejected"}, 403)
        if not self._token_ok():
            return self._json({"error": "unauthorized"}, 401)
        ctype = self.headers.get("Content-Type", "").split(";", 1)[0].lower()
        if p in {"/api/run", "/api/speak", "/api/new", "/api/cancel"} and ctype != "application/json":
            return self._json({"error": "application/json required"}, 415)
        try:
            raw = self._read(MAX_AUDIO if p == "/api/listen" else MAX_JSON)
        except (TypeError, ValueError):
            return self._json({"error": "body too large"}, 413)

        if p == "/api/speak":
            try:
                text = (json.loads(raw or b"{}").get("text") or "").strip()
                return self._bytes(voice.speak(text), "audio/mpeg")
            except Exception as e:  # noqa: BLE001
                return self._json({"error": str(e)[:200]}, 503)

        if p == "/api/listen":
            try:
                return self._json({"text": voice.transcribe(raw, self.headers.get("Content-Type", "audio/webm"))})
            except Exception as e:  # noqa: BLE001
                return self._json({"error": str(e)[:400], "text": ""}, 503)

        if p == "/api/new":
            runtime.cancel_active()
            SESSION["id"] = None
            return self._json({"ok": True})

        if p == "/api/cancel":
            stopped = runtime.cancel_active()
            SESSION["id"] = None
            return self._json({"ok": True, "stopped": stopped})

        if p == "/api/run":
            if not RUN_LOCK.acquire(blocking=False):
                busy = int((time.time() - RUN_STARTED["at"]) * 1000) if RUN_STARTED["at"] else 0
                return self._json({"error": "JARVIS is already processing a request",
                                   "busy": True, "running_for_ms": busy}, 409)
            RUN_STARTED["at"] = time.time()
            try:
                return self._stream(raw)
            finally:
                RUN_STARTED["at"] = 0.0
                RUN_LOCK.release()

        return self._json({"error": "no such endpoint"}, 404)

    def _stream(self, raw):
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return self._json({"error": "bad json"}, 400)
        message = (payload.get("message") or "").strip()
        if not message:
            return self._json({"error": "empty message"}, 400)
        if payload.get("fresh"):
            SESSION["id"] = None

        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()

        def emit(ev):
            self.wfile.write((json.dumps(ev) + "\n").encode())
            self.wfile.flush()

        cmd = commands.handle(message, runner=lambda m: runtime.run(m, None, commands.context_block(m)))
        if cmd:
            if cmd.get("note"):
                emit(dict(t="note", message=cmd["note"]))
            if cmd.get("fresh"):
                SESSION["id"] = None
            if cmd.get("focus"):
                emit(dict(t="focus", id=str(cmd["focus"]).lower()))
            if cmd.get("graph"):
                emit(dict(t="graph"))
            if cmd.get("message") is None:
                delay = float(cmd.get("delay") or 0)
                for event in cmd.get("events", []):
                    if delay and event.get("phase") == "result":
                        time.sleep(delay)
                        delay = 0
                    emit(event)
                emit(dict(t="delta", text=cmd.get("reply", "Done.")))
                emit(dict(t="complete", ms=0))
                return
            message = cmd["message"]

        system = commands.context_block(message) or None
        hit = memory.top_match(message)
        if hit:
            emit(dict(t="focus", id=hit))
        actions, took = [], 0
        try:
            for ev in runtime.run(message, SESSION["id"], system):
                if ev.get("t") == "complete" and runtime.valid_session(ev.get("session_id")):
                    SESSION["id"] = ev["session_id"]
                if ev.get("t") == "error":
                    SESSION["id"] = None
                if ev.get("t") == "tool" and ev.get("phase") == "use":
                    actions.append({"name": ev.get("name", "tool"), "input": ev.get("input")})
                if ev.get("t") == "complete":
                    took = ev.get("ms") or 0
                emit(ev)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:  # noqa: BLE001
            try:
                emit(dict(t="error", message=str(e)[:300]))
            except OSError:
                pass
        # A session remembers this conversation; the vault remembers the work.
        # Written after the stream so a slow disk never stalls the reply.
        try:
            if journal.record(memory.build_graph()["vault"], message, actions, took):
                memory.build_graph(force=True)
        except Exception:  # noqa: BLE001
            pass            # journalling must never take the turn down with it


def main():
    kind = runtime.runtime_kind()
    g = memory.build_graph()
    brain = (f"Claude Code {runtime.version()} — your subscription, no API key"
             if kind == "claude" else "MOCK — claude CLI not reachable")
    print(f"""
  JARVIS · Claude Code Memory HUD
  ────────────────────────────────────────────────
  brain        {brain}
  model        {runtime.MODEL or 'Claude default'}
  vault        {g['total']} notes · {len(g['links'])} links
               {g['vault']}
  voice        {voice.describe()}
  listening    {voice.describe_stt()}
  workdir      {runtime.WORKDIR}
  open         http://localhost:{PORT}
""", flush=True)
    if BIND != "127.0.0.1":
        print(f"  !  bound to {BIND}, not loopback. Anything that can reach this\n"
              f"     port can run commands as you. Private network only.\n", flush=True)
    try:
        srv = ThreadingHTTPServer((BIND, PORT), Handler)
    except OSError as e:
        if e.errno not in (48, 98):          # EADDRINUSE on macOS / Linux
            raise
        print(f"  Port {PORT} is already in use — JARVIS is probably already\n"
              f"  running in another tab. Use that one, or stop it first:\n"
              f"      pkill -f 'python3 server.py'\n"
              f"  Or run this one somewhere else:  JARVIS_PORT=8721 ./start.sh\n")
        raise SystemExit(1)
    if os.environ.get("JARVIS_OPEN", "1") != "0":
        webbrowser.open(f"http://localhost:{PORT}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  down.")
        srv.shutdown()


if __name__ == "__main__":
    main()
