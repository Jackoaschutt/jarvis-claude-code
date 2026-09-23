"""
Put the Telegram credentials into .env, without typing them at a shell.

    python3 telegram_setup.py

Asks for the bot token and your user id, checks both look right, confirms the
token actually works against Telegram, and writes them to .env.

Why this rather than `echo ... >> .env`: a token typed at the shell is copied
into ~/.zsh_history, which is a second copy in a file you will forget about.
Here the token never reaches the shell, never appears on screen, and never
leaves the machine except to Telegram itself.
"""
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
ENV = ROOT / ".env"
API = os.environ.get("TELEGRAM_API_BASE", "https://api.telegram.org").rstrip("/")


def hidden(prompt):
    """Read without echoing. getpass, but honest about what it is doing."""
    import getpass
    try:
        return getpass.getpass(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit("cancelled")


def put(key, value):
    text = ENV.read_text(encoding="utf-8") if ENV.exists() else ""
    if re.search(rf"(?m)^{key}=", text):
        text = re.sub(rf"(?m)^{key}=.*$", f"{key}={value}", text)
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        text += f"{key}={value}\n"
    ENV.write_text(text, encoding="utf-8")


def check(token):
    """Ask Telegram who this token belongs to. Returns the username or None."""
    try:
        with urllib.request.urlopen(f"{API}/bot{token}/getMe", timeout=20) as r:
            return (json.loads(r.read()).get("result") or {}).get("username")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False          # token is wrong or has been revoked
        return None               # some other problem; not the token's fault
    except (urllib.error.URLError, OSError):
        return None               # offline, or blocked — cannot tell either way


def main():
    if not ENV.exists():
        sys.exit("No .env here. Run ./setup.sh first, or cd into the repo.")

    print("\n  Telegram setup\n")
    print("    Token comes from @BotFather (/newbot, or /revoke for a fresh one).")
    print("    Typing is hidden — nothing appears on screen and nothing is echoed back.\n")

    token = hidden("  Paste the bot token: ")
    print()
    if not token:
        sys.exit("  nothing entered — stopping.")
    # A repeated paste is the single most common way this goes wrong.
    dupe = re.match(r"^(\d{5,}:[A-Za-z0-9_-]{30,})\1+$", token)
    if dupe:
        token = dupe.group(1)
        print(f"  ! paste repeated — trimmed to one token ({len(token)} chars)")
    if not re.match(r"^\d{5,}:[A-Za-z0-9_-]{30,}$", token):
        sys.exit("  That does not look like a bot token. It should be a long number,\n"
                 "  then a colon, then a long mixed string. Copy the whole thing.")

    name = check(token)
    if name is False:
        sys.exit("  Telegram rejected that token. If you ran /revoke, use the NEW one.")
    if name:
        print(f"  ✓ token works — this is @{name}")
    else:
        print("  ? could not reach Telegram to verify. Saving anyway.")

    print("\n    Your user id comes from @userinfobot. Just the number.\n")
    try:
        uid = input("  Your Telegram user id: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit("cancelled")
    if not re.match(r"^\d{5,}(,\d{5,})*$", uid):
        sys.exit("  That should be digits only, like 812345678.")

    put("TELEGRAM_BOT_TOKEN", token)
    put("TELEGRAM_ALLOWED_IDS", uid)
    print(f"\n  ✓ saved to .env ({ENV})")
    print("    .env is gitignored, so this is not committed anywhere.\n")
    print("  Start it:\n    python3 telegram_bridge.py\n")


if __name__ == "__main__":
    main()
