"""
Voice picker and speech check for JARVIS.

Steps 5 and 7 of the setup prompt, as one command each. Standard library only,
same as the rest of the repo, and it reads .env exactly the way server.py does
so there is one source of truth for the key.

    python3 voice_setup.py key               # put the API key into .env
    python3 voice_setup.py voices jarvis     # search the library, print ids
    python3 voice_setup.py pick <voice-id>   # write it into .env
    python3 voice_setup.py say               # prove it actually speaks
    python3 voice_setup.py wallet            # TTS balance vs ASR credit

The key is read from .env and never printed: every line here shows at most a
masked fingerprint, so a screen recording of the setup leaks nothing.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
ENV = ROOT / ".env"
API = os.environ.get("FISH_AUDIO_API_BASE", "https://api.fish.audio")

# One or two tags, placed where the register changes — the house style from
# VOICE_DIRECTION. Also a fair test of the voice: if this lands dry, it is a
# JARVIS; if it lands cheerful, keep looking.
PROBE = ("[dry] Voice check complete, sir. [the calm tone of someone who has "
         "done this a thousand times] Everything is exactly where you left it.")


def load_env():
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def key():
    k = os.environ.get("FISH_AUDIO_API_KEY", "").strip()
    if not k:
        sys.exit("No FISH_AUDIO_API_KEY in .env — add it, then run this again.")
    return k


def hidden(prompt):
    """Read without echoing."""
    import getpass
    try:
        return getpass.getpass(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit("cancelled")


def fingerprint(k):
    """Enough to tell two keys apart, not enough to use one."""
    return f"{k[:3]}…{k[-2:]} ({len(k)} chars)"


def call(path, params=None, method="GET", body=None, headers=None, raw=False):
    url = API + path + (("?" + urllib.parse.urlencode(params, doseq=True)) if params else "")
    h = {"authorization": f"Bearer {key()}"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
            return data if raw else json.loads(data)
    except urllib.error.HTTPError as e:
        detail = e.read(400).decode("utf-8", "replace")
        if e.code == 401:
            sys.exit(f"Fish Audio rejected the key ({fingerprint(key())}). Check .env.")
        if e.code == 402:
            sys.exit(f"Fish Audio HTTP 402 — out of balance, not a bug in the code.\n  {detail}")
        sys.exit(f"Fish Audio HTTP {e.code}: {detail}")
    except urllib.error.URLError as e:
        sys.exit(f"Could not reach {API}: {e.reason}")


def search(term="jarvis", count=8):
    res = call("/model", {"title": term, "page_size": count, "sort_by": "score"})
    return res.get("items") or [], res.get("total", 0)


def show(items, total, term):
    print(f"\n  {len(items)} of {total} voices matching {term!r}\n")
    for i, m in enumerate(items, 1):
        langs = ",".join(m.get("languages") or []) or "—"
        author = ((m.get("author") or {}).get("nickname")) or "—"
        print(f"  {i}. {(m.get('title') or 'untitled')[:44]}")
        print(f"     id {m.get('_id')}  ·  {langs}  ·  by {author}  ·  {m.get('task_count', 0)} uses")
        desc = " ".join((m.get("description") or "").split())[:96]
        if desc:
            print(f"     {desc}")
        print()


def _clipboard():
    """Whatever is on the clipboard, or '' where there is no clipboard at all."""
    for cmd in (["pbpaste"], ["wl-paste"], ["xclip", "-o", "-selection", "clipboard"]):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if out.returncode == 0 and out.stdout.strip():
                return out.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            continue
    return ""


def _untangle(value):
    """A paste that landed twice reads as a wrong key, not a doubled one."""
    half = len(value) // 2
    if len(value) % 2 == 0 and value[:half] == value[half:]:
        return value[:half]
    third = len(value) // 3
    if len(value) % 3 == 0 and value[:third] * 3 == value:
        return value[:third]
    return value


def _put(key, value):
    text = ENV.read_text(encoding="utf-8") if ENV.exists() else ""
    if re.search(rf"(?m)^{key}=", text):
        text = re.sub(rf"(?m)^{key}=.*$", f"{key}={value}", text)
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        text += f"{key}={value}\n"
    ENV.write_text(text, encoding="utf-8")


def cmd_key():
    """Put the Fish Audio key into .env, checking it before saving."""
    if not ENV.exists():
        sys.exit("  No .env here. cd into the repo first.")
    print("\n  Fish Audio key\n")
    print("    On your other machine:  grep FISH_AUDIO_API_KEY .env")
    print("    Copy the part after the = sign.\n")

    value = _untangle(_clipboard())
    if value.startswith("sk-") and len(value) > 20:
        print(f"  Found a key on your clipboard: {fingerprint(value)}")
        try:
            if (input("  Use it? [Y/n]: ").strip().lower() or "y") not in ("y", "yes"):
                value = ""
        except (EOFError, KeyboardInterrupt):
            print(); sys.exit("cancelled")
        print()
    else:
        value = ""

    if not value:
        visible = "--show" in sys.argv
        if not visible:
            print("  Paste it below — the screen stays blank, which is normal.")
            print("  Re-run with --show to watch it land.\n")
        raw = (input if visible else hidden)("  Paste the key: ").strip()
        print()
        value = _untangle(raw)
        if value != raw:
            print(f"  ! paste repeated — trimmed to one key ({len(value)} chars)")

    if not value:
        sys.exit("  nothing entered — stopping.")
    if not value.startswith("sk-"):
        sys.exit("  That does not look like a Fish Audio key — they begin with sk-.")

    os.environ["FISH_AUDIO_API_KEY"] = value     # so check() uses the new one
    try:
        pkg = call("/wallet/self/package")
        print(f"  ✓ key works — TTS balance {pkg.get('balance')} of {pkg.get('total')}")
    except SystemExit as e:
        raise SystemExit(f"{e}\n  Key not saved.")

    _put("FISH_AUDIO_API_KEY", value)
    print(f"  ✓ saved to .env ({ENV})\n")
    voice = os.environ.get("FISH_AUDIO_VOICE_ID", "").strip()
    if voice:
        print(f"  Voice already set to {voice[:8]}…  Test it:  python3 voice_setup.py say\n")
    else:
        print("  Now pick a voice:  python3 voice_setup.py voices jarvis\n")


def cmd_voices(term="jarvis", count=8):
    """Step 5: show real voices with their ids. No ids are ever invented here."""
    items, total = search(term, count)
    if not items:
        print(f"Nothing matched {term!r}. Try: butler, narrator, british male, calm male.")
        return
    show(items, total, term)
    print("  Pick one:  python3 voice_setup.py pick <id>\n")


def cmd_choose(term="jarvis"):
    """Search, list, pick by number. Loops until something is chosen."""
    while True:
        items, total = search(term)
        if not items:
            print(f"  Nothing matched {term!r}. Try: butler, narrator, british male, calm male.")
        else:
            show(items, total, term)
        try:
            ans = input("  Number to choose, or another search term (blank to skip): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not ans:
            return
        if ans.isdigit() and items and 1 <= int(ans) <= len(items):
            return cmd_pick(items[int(ans) - 1]["_id"])
        term = ans


def cmd_pick(voice_id):
    """Confirm the id is real, then write it into .env."""
    m = call(f"/model/{voice_id}")
    title = m.get("title") or voice_id
    text = ENV.read_text(encoding="utf-8") if ENV.exists() else "FISH_AUDIO_VOICE_ID=\n"
    if re.search(r"(?m)^FISH_AUDIO_VOICE_ID=.*$", text):
        text = re.sub(r"(?m)^FISH_AUDIO_VOICE_ID=.*$", f"FISH_AUDIO_VOICE_ID={voice_id}", text)
    else:
        text += f"\nFISH_AUDIO_VOICE_ID={voice_id}\n"
    ENV.write_text(text, encoding="utf-8")
    print(f"  Voice set to {title} ({voice_id}). Restart ./start.sh to pick it up.")


def cmd_say(text=PROBE, out="voice-check.mp3"):
    """Step 7: real bytes or it did not happen."""
    load_env()
    model = os.environ.get("FISH_AUDIO_MODEL", "s2.1-pro-free")
    voice = os.environ.get("FISH_AUDIO_VOICE_ID", "").strip()
    payload = {"text": text, "format": "mp3", "latency": "normal"}
    if voice:
        payload["reference_id"] = voice
    audio = call("/v1/tts", method="POST", body=json.dumps(payload).encode(),
                 headers={"content-type": "application/json", "model": model}, raw=True)

    # mp3 is either an ID3 tag or a bare frame sync. Anything else means the
    # endpoint handed back something that is not audio, however long it is.
    is_mp3 = audio[:3] == b"ID3" or (len(audio) > 1 and audio[0] == 0xFF and audio[1] & 0xE0 == 0xE0)
    path = ROOT / out
    path.write_bytes(audio)
    print(f"\n  key      {fingerprint(key())}")
    print(f"  model    {model}")
    print(f"  voice    {voice or 'default'}")
    print(f"  bytes    {len(audio):,}  ·  {'valid mp3' if is_mp3 else 'NOT mp3 — something is wrong'}")
    print(f"  saved    {path}")
    print("\n  Play it. If the brackets are spoken out loud, the model header is wrong.\n")
    if not is_mp3:
        sys.exit(1)


def cmd_wallet():
    """TTS and ASR bill from different balances — this says which one is empty."""
    pkg = call("/wallet/self/package")
    print(f"  TTS balance   {pkg.get('balance')} of {pkg.get('total')} ({pkg.get('type')})")
    cred = call("/wallet/self/api-credit", {"check_free_credit": "true"})
    print(f"  ASR credit    {cred.get('credit')}")
    print("  Listening is billed from ASR credit, speaking from the TTS balance.")


def main():
    load_env()
    args = sys.argv[1:] or ["say"]
    cmd, rest = args[0], args[1:]
    if cmd == "key":
        cmd_key()
    elif cmd == "voices":
        cmd_voices(" ".join(rest) or "jarvis")
    elif cmd == "choose":
        cmd_choose(" ".join(rest) or "jarvis")
    elif cmd == "pick":
        if not rest:
            sys.exit("usage: python3 voice_setup.py pick <voice-id>")
        cmd_pick(rest[0])
    elif cmd == "say":
        cmd_say(" ".join(rest) or PROBE)
    elif cmd == "wallet":
        cmd_wallet()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
