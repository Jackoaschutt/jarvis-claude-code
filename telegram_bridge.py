"""
Talk to JARVIS from Telegram.

    python3 telegram_bridge.py

Long-polls Telegram, hands each message to the JARVIS server on localhost, and
sends the reply back — text, plus the Fish Audio voice as an audio clip if one
is configured. Long polling means Telegram is dialled *out* to, so this needs
no public URL, no port forwarding and no tunnel. The laptop just has to be
awake with ./start.sh running.

Setup:
  1. Message @BotFather on Telegram, /newbot, copy the token.
  2. Message @userinfobot to get your own numeric user id.
  3. Put both in .env:
        TELEGRAM_BOT_TOKEN=123456:AA...
        TELEGRAM_ALLOWED_IDS=123456789
  4. python3 telegram_bridge.py

TELEGRAM_ALLOWED_IDS is not optional and the bridge refuses to start without
it. JARVIS runs `claude` with bypassPermissions in your home directory, so an
unrestricted bot is a shell that anyone who finds it can type into. Anything
from an id not on that list is dropped and logged, never answered.
"""
import atexit
import json
import os
import pathlib
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent

_env = ROOT / ".env"
if _env.exists():
    for line in _env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

API = os.environ.get("TELEGRAM_API_BASE", "https://api.telegram.org").rstrip("/")
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
PORT = int(os.environ.get("JARVIS_PORT", "8720"))
JARVIS = f"http://127.0.0.1:{PORT}"
SEND_VOICE = os.environ.get("TELEGRAM_VOICE", "1").strip().lower() not in {"0", "false", "no"}
POLL = int(os.environ.get("TELEGRAM_POLL", "30"))
# Telegram rate-limits edits to a message; a few seconds apart is safe
# and still reads as live.
EDIT_EVERY = float(os.environ.get("TELEGRAM_EDIT_EVERY", "3"))
# How long JARVIS may go silent before the bridge stops waiting. This is
# silence *between* events, not the length of the turn, so it only trips when
# one tool call runs long with nothing to say — an npm install or a build on a
# small box, which is exactly the case that used to read as "timed out".
ASK_TIMEOUT = int(os.environ.get("TELEGRAM_ASK_TIMEOUT", "900"))
# The status line ticks on its own as well as on tool calls: a frozen status
# and a dead bot look identical from the sofa.
HEARTBEAT = float(os.environ.get("TELEGRAM_HEARTBEAT", "15"))

ALLOWED = {i.strip() for i in os.environ.get("TELEGRAM_ALLOWED_IDS", "").split(",") if i.strip()}
PIDFILE = ROOT / ".bridge.pid"


def claim():
    """Only one bridge per bot. Telegram allows a single getUpdates in flight,
    so a second instance does not fail loudly — both sit there answering every
    other message, which reads as the bot randomly ignoring you."""
    other = _running_bridge()
    if other:
        sys.exit(f"  A bridge is already running (pid {other}).\n"
                 f"  Use that one, or stop it first:  pkill -f telegram_bridge.py")
    PIDFILE.write_text(str(os.getpid()))
    atexit.register(release)


def _running_bridge():
    """The pid in the pidfile, but only if it is still a live bridge.

    os.kill(pid, 0) is not enough: a killed process that its parent has not
    reaped still answers, and a recycled pid belongs to something unrelated.
    Either would wrongly block a legitimate start, so check the command too.
    """
    try:
        pid = int(PIDFILE.read_text().strip())
    except (OSError, ValueError):
        return 0
    try:
        out = subprocess.run(["ps", "-p", str(pid), "-o", "command="],
                             capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return 0
    return pid if "telegram_bridge" in out.stdout else 0


def release():
    try:
        if int(PIDFILE.read_text().strip()) == os.getpid():
            PIDFILE.unlink()
    except (OSError, ValueError):
        pass


class Busy(Exception):
    """JARVIS is mid-turn. Not a fault: the previous question is still running,
    and the server refuses a second one rather than interleaving them."""

    def __init__(self, seconds=0):
        self.seconds = seconds
        super().__init__(f"busy for {seconds}s")


def tg(method, payload=None, files=None):
    """Telegram Bot API call. JSON, or multipart when sending a file."""
    url = f"{API}/bot{TOKEN}/{method}"
    if files:
        boundary = "----jarvis" + os.urandom(8).hex()
        b = boundary.encode()
        parts = []
        for k, v in (payload or {}).items():
            parts += [b"--", b, b"\r\n",
                      f'Content-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()]
        for k, (name, data, ctype) in files.items():
            parts += [b"--", b, b"\r\n",
                      f'Content-Disposition: form-data; name="{k}"; filename="{name}"\r\n'.encode(),
                      f"Content-Type: {ctype}\r\n\r\n".encode(), data, b"\r\n"]
        parts += [b"--", b, b"--\r\n"]
        body, ctype = b"".join(parts), f"multipart/form-data; boundary={boundary}"
    else:
        body, ctype = json.dumps(payload or {}).encode(), "application/json"
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"content-type": ctype})
    with urllib.request.urlopen(req, timeout=POLL + 30) as r:
        return json.loads(r.read())


def token():
    """The per-launch API token, read off the page the server serves."""
    req = urllib.request.Request(JARVIS + "/", headers={"Host": f"127.0.0.1:{PORT}"})
    with urllib.request.urlopen(req, timeout=15) as r:
        m = re.search(r'jarvis-token" content="([^"]+)"', r.read().decode("utf-8", "replace"))
    if not m:
        raise RuntimeError("could not read the JARVIS token — is ./start.sh running?")
    return m.group(1)


def ask(message, on_step=None):
    """One turn through JARVIS. Returns the reply text.

    on_step, when given, is called with a one-line description of each tool
    call as it happens, so a caller can show the working out somewhere.
    """
    body = json.dumps({"message": message}).encode()
    req = urllib.request.Request(
        JARVIS + "/api/run", data=body, method="POST",
        headers={"content-type": "application/json", "Host": f"127.0.0.1:{PORT}",
                 "Origin": JARVIS, "X-Jarvis-Token": token()})
    out, error = [], None
    try:
        response = urllib.request.urlopen(req, timeout=ASK_TIMEOUT)
    except urllib.error.HTTPError as e:
        if e.code != 409:
            raise
        seconds = 0
        try:
            seconds = int((json.loads(e.read(400)).get("running_for_ms") or 0) / 1000)
        except Exception:                                     # noqa: BLE001
            pass
        raise Busy(seconds) from None
    with response as r:
        for line in r:
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = ev.get("t")
            if kind == "delta":
                out.append(ev.get("text", ""))
            elif kind == "note":
                out.append(ev.get("message", ""))
            elif kind == "error":
                error = ev.get("message", "something went wrong")
            # Telegram only ever shows the finished answer. Print the working
            # out here so this tab says what JARVIS actually did — which file it
            # wrote, which command it ran — rather than going quiet for a minute.
            elif kind == "tool" and ev.get("phase") == "use":
                detail = " ".join(str(ev.get("input") or "").split())[:88]
                print(f"     → {ev.get('name', 'tool')}  {detail}", flush=True)
                if on_step:
                    on_step(f"{ev.get('name', 'tool')} {detail}".strip())
            elif kind == "tool" and ev.get("phase") == "result":
                print(f"       {'ok' if ev.get('ok') else 'FAILED'}", flush=True)
    if error and not out:
        return f"[error] {error}"
    return "".join(out).strip() or "No answer came back."


def speak(text):
    """mp3 bytes for the reply, or None if voice is off or unavailable."""
    if not SEND_VOICE:
        return None
    # Delivery tags are stage directions for the voice, not for the reader.
    spoken = re.sub(r"\[[^\]]{0,60}\]", " ", text)
    spoken = " ".join(spoken.split())
    if not spoken:
        return None
    body = json.dumps({"text": spoken[:2000]}).encode()
    req = urllib.request.Request(
        JARVIS + "/api/speak", data=body, method="POST",
        headers={"content-type": "application/json", "Host": f"127.0.0.1:{PORT}",
                 "Origin": JARVIS, "X-Jarvis-Token": token()})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = r.read()
        return data if data[:3] == b"ID3" or data[:1] == b"\xff" else None
    except (urllib.error.HTTPError, urllib.error.URLError, OSError):
        return None       # browser-voice fallback territory; text still goes out


def cancel():
    """Drop whatever turn is running. True if something was actually stopped."""
    req = urllib.request.Request(
        JARVIS + "/api/cancel", data=b"{}", method="POST",
        headers={"content-type": "application/json", "Host": f"127.0.0.1:{PORT}",
                 "Origin": JARVIS, "X-Jarvis-Token": token()})
    with urllib.request.urlopen(req, timeout=30) as r:
        return bool(json.loads(r.read()).get("stopped"))


class Status:
    """The one message in the chat that shows what JARVIS is doing.

    It ticks on a thread as well as on tool calls, because a long build emits
    nothing for minutes and a status frozen at "thinking" is indistinguishable
    from a bot that has fallen over — which is how a perfectly healthy JARVIS
    ends up being restarted.
    """

    def __init__(self, chat):
        self.chat, self.steps = chat, []
        self.started, self.last = time.monotonic(), 0.0
        self.lock, self.stop, self.id = threading.Lock(), threading.Event(), None
        try:
            self.id = (tg("sendMessage", {"chat_id": chat, "text": "⋯ thinking"})
                       .get("result") or {}).get("message_id")
        except Exception:                                     # noqa: BLE001
            return                                 # no status line; the work still runs
        threading.Thread(target=self._tick, daemon=True).start()

    def _tick(self):
        while not self.stop.wait(HEARTBEAT):
            self.draw(force=True)

    def step(self, line):
        with self.lock:
            self.steps.append(line)
        self.draw()

    def draw(self, force=False):
        if not self.id or self.stop.is_set():
            return
        now = time.monotonic()
        with self.lock:
            if not force and now - self.last < EDIT_EVERY:     # Telegram rate-limits edits
                return
            self.last, steps = now, list(self.steps[-6:])
        body = f"⋯ working · {int(now - self.started)}s\n\n" + "\n".join(f"· {s}" for s in steps)
        try:
            tg("editMessageText", {"chat_id": self.chat, "message_id": self.id,
                                   "text": body[:3500]})
        except Exception:                                     # noqa: BLE001
            pass                                   # never let the view break the work

    def done(self, keep=False):
        self.stop.set()
        if self.id and not keep:
            try:
                tg("deleteMessage", {"chat_id": self.chat, "message_id": self.id})
            except Exception:                                 # noqa: BLE001
                pass


def handle(msg):
    chat = str(((msg.get("chat") or {}).get("id")) or "")
    sender = str(((msg.get("from") or {}).get("id")) or "")
    if sender not in ALLOWED:
        print(f"  refused message from id {sender or '?'}", flush=True)
        return
    text = (msg.get("text") or msg.get("caption") or "").strip()
    if not text:
        tg("sendMessage", {"chat_id": chat,
                           "text": "Text only for now — voice notes are not wired up."})
        return
    if text.startswith("/start") or text.startswith("/help"):
        tg("sendMessage", {"chat_id": chat, "text":
            "JARVIS is listening.\n\n"
            "/cancel — drop the turn that is running\n"
            "/status — is the server actually there"})
        return
    if text.startswith("/cancel"):
        try:
            stopped = cancel()
        except Exception as e:                                # noqa: BLE001
            tg("sendMessage", {"chat_id": chat, "text": f"Could not reach JARVIS: {str(e)[:150]}"})
            return
        tg("sendMessage", {"chat_id": chat,
                           "text": "Stopped it. Ask me something else."
                           if stopped else "Nothing was running."})
        return
    if text.startswith("/status"):
        try:
            token()
            tg("sendMessage", {"chat_id": chat, "text": "Bridge up, JARVIS reachable."})
        except Exception as e:                                # noqa: BLE001
            tg("sendMessage", {"chat_id": chat,
                               "text": f"Bridge up, but JARVIS is not answering: {str(e)[:150]}"})
        return

    tg("sendChatAction", {"chat_id": chat, "action": "typing"})
    print(f"\n  ← {' '.join(text.split())[:100]}", flush=True)
    started = time.monotonic()

    # A long turn is a minute of silence in Telegram, which is indistinguishable
    # from a dead bot. Keep one message updated with what it is doing instead of
    # posting a new one per step, which would bury the answer.
    status = Status(chat)
    try:
        reply = ask(text, on_step=status.step)
    except Busy as b:
        # Not an error. The previous question is still running, and saying
        # "HTTP Error 409: Conflict" to someone on their phone is useless.
        status.done()
        been = f"{b.seconds // 60}m {b.seconds % 60}s in" if b.seconds else "still going"
        tg("sendMessage", {"chat_id": chat, "text":
            f"Still working on the last thing ({been}). It is not stuck — a build on "
            f"this box can run for minutes with nothing to show.\n\n"
            f"Wait for it, or send /cancel to drop it and ask again."})
        return
    except Exception as e:                                    # noqa: BLE001
        print(f"  ! {str(e)[:160]}", flush=True)
        status.done(keep=True)          # leave it up on failure: it shows how far it got
        if "timed out" in str(e).lower():
            tg("sendMessage", {"chat_id": chat, "text":
                f"No word from JARVIS for {ASK_TIMEOUT // 60} minutes, so I stopped "
                f"waiting. The turn is most likely still running on the server — long "
                f"builds go quiet.\n\n"
                f"Give it a bit and ask again, or send /cancel to drop it."})
        else:
            tg("sendMessage", {"chat_id": chat, "text": f"JARVIS is not answering: {str(e)[:200]}"})
        return
    print(f"  → {' '.join(reply.split())[:100]}  ({time.monotonic() - started:.0f}s)", flush=True)
    status.done()
    tg("sendMessage", {"chat_id": chat, "text": reply[:4000]})
    audio = speak(reply)
    if audio:
        tg("sendAudio", {"chat_id": chat, "title": "JARVIS"},
           {"audio": ("jarvis.mp3", audio, "audio/mpeg")})


def main():
    if not TOKEN:
        sys.exit("No TELEGRAM_BOT_TOKEN in .env. Get one from @BotFather.")
    if not ALLOWED:
        sys.exit("No TELEGRAM_ALLOWED_IDS in .env. Refusing to start.\n"
                 "An open bot is a shell anyone can type into — JARVIS runs with\n"
                 "full tool access. Message @userinfobot for your numeric id.")
    claim()
    try:
        token()
    except Exception as e:                                    # noqa: BLE001
        sys.exit(f"Cannot reach JARVIS on {JARVIS}: {e}\nStart it with ./start.sh first.")

    me = tg("getMe").get("result", {})
    print(f"\n  bridge up · @{me.get('username', '?')} · {len(ALLOWED)} allowed id(s)")
    print(f"  JARVIS    {JARVIS}")
    print(f"  voice     {'on' if SEND_VOICE else 'off'}\n  Ctrl-C to stop.\n", flush=True)

    offset = None
    while True:
        try:
            payload = {"timeout": POLL, "allowed_updates": ["message"]}
            if offset is not None:
                payload["offset"] = offset
            for update in tg("getUpdates", payload).get("result", []):
                offset = update["update_id"] + 1
                if update.get("message"):
                    handle(update["message"])
        except KeyboardInterrupt:
            print("\n  bridge down.")
            return
        except Exception as e:                                # noqa: BLE001
            note = ""
            if "409" in str(e):
                note = ("  (another getUpdates is in flight — usually a bridge you just\n"
                        "   stopped, clearing within a minute. If it keeps repeating, a\n"
                        "   second bridge is running: pkill -f telegram_bridge.py)")
            print(f"  poll error: {str(e)[:160]}{note and chr(10) + note}", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
