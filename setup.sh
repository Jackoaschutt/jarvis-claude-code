#!/usr/bin/env bash
# Stand up JARVIS on this machine, in one command:
#
#     ./setup.sh
#
# Checks what it needs, takes your Fish Audio key without echoing it, lets you
# pick a voice from the real library, proves the voice works by playing it back,
# then starts the server. Safe to re-run — it keeps what you already set.
set -u

cd "$(dirname "$0")" || exit 1
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$HOME/.npm-global/bin:$PATH"

bold() { printf "\033[1m%s\033[0m\n" "$1"; }
ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
bad()  { printf "  \033[31m✗\033[0m %s\n" "$1"; }
note() { printf "    %s\n" "$1"; }

echo
bold "JARVIS setup"
echo

# ── 1. what we need ────────────────────────────────────────────
fail=0
if command -v python3 >/dev/null 2>&1; then
  ok "python3 $(python3 -V 2>&1 | cut -d' ' -f2)"
else
  bad "python3 not found"
  note "macOS: xcode-select --install     Debian/Ubuntu: sudo apt install python3"
  fail=1
fi

if command -v claude >/dev/null 2>&1; then
  ok "claude $(claude --version 2>/dev/null | head -1)"
else
  bad "claude CLI not found — JARVIS has no brain without it"
  note "Install (macOS/Linux, no Node needed):"
  note "    curl -fsSL https://claude.ai/install.sh | bash"
  note "Homebrew:  brew install --cask claude-code"
  note "With Node: npm install -g @anthropic-ai/claude-code"
  note ""
  note "Then run  claude  once and sign in. It uses your Claude subscription —"
  note "no API key, no per-token billing. Then re-run ./setup.sh."
  fail=1
fi

if [ "$(id -u)" -eq 0 ]; then
  bad "running as root — the claude CLI refuses bypassPermissions as root"
  note "Run this as your normal user, or set JARVIS_PERMISSION=acceptEdits in .env"
fi

[ "$fail" -eq 1 ] && { echo; echo "  Fix the above, then run ./setup.sh again."; echo; exit 1; }

# ── 2. .env ────────────────────────────────────────────────────
if [ ! -f .env ]; then
  cp .env.example .env
  ok "created .env from .env.example"
else
  ok ".env already exists — keeping it"
fi

# Read a value out of .env without printing it.
envval() { sed -n "s/^$1=//p" .env | head -1; }

# ── 3. the key ─────────────────────────────────────────────────
echo
if [ -n "$(envval FISH_AUDIO_API_KEY)" ]; then
  ok "Fish Audio key already in .env"
else
  bold "Fish Audio key"
  note "Get one at https://fish.audio → API keys."
  note "Typing is hidden and the key is never printed back."
  note "Leave blank to skip — JARVIS still runs, using the robotic browser voice."
  printf "  Paste key: "
  stty -echo 2>/dev/null; IFS= read -r KEY; stty echo 2>/dev/null; echo
  if [ -n "$KEY" ]; then
    KEY="$KEY" python3 - <<'PY'
import os, pathlib, re
p = pathlib.Path(".env"); t = p.read_text()
k = os.environ["KEY"].strip()
# A terminal paste that repeats lands here as the key two or three times over,
# which Fish rejects as a bad key rather than as a malformed one — so the error
# sends you hunting for a new key instead of for a stray paste. Keep copy one.
i = k.find("sk-", 3)
if i > 0:
    k = k[:i]
    print(f"  \033[33m!\033[0m paste repeated — trimmed to the first key ({len(k)} chars)")
if re.search(r"(?m)^FISH_AUDIO_API_KEY=", t):
    t = re.sub(r"(?m)^FISH_AUDIO_API_KEY=.*$", "FISH_AUDIO_API_KEY=" + k, t)
else:
    t += "\nFISH_AUDIO_API_KEY=" + k + "\n"
p.write_text(t)
print(f"  \033[32m✓\033[0m key saved to .env ({len(k)} chars, gitignored)")
PY
  else
    note "skipped — add it to .env later and restart"
  fi
fi

# ── 4. the voice ───────────────────────────────────────────────
if [ -n "$(envval FISH_AUDIO_API_KEY)" ]; then
  echo
  if [ -n "$(envval FISH_AUDIO_VOICE_ID)" ]; then
    ok "voice already set ($(envval FISH_AUDIO_VOICE_ID | cut -c1-8)…)"
    printf "  Pick a different one? [y/N] "; read -r again
    [ "${again:-n}" = "y" ] && python3 voice_setup.py choose jarvis
  else
    bold "Pick a voice"
    python3 voice_setup.py choose jarvis
  fi

  # ── 5. prove it speaks ───────────────────────────────────────
  echo
  bold "Voice check"
  if python3 voice_setup.py say; then
    for p in afplay "mpv --no-video" ffplay "cvlc --play-and-exit" aplay; do
      bin="${p%% *}"
      if command -v "$bin" >/dev/null 2>&1; then
        note "playing voice-check.mp3 …"
        $p voice-check.mp3 >/dev/null 2>&1
        break
      fi
    done
    note "If the words 'dry' and 'calm' were NOT read aloud, the voice layer is correct."
  else
    bad "voice check failed — read the error above"
    note "402 means out of balance, 401 means bad key, anything else is worth pasting to Claude."
    note "JARVIS still works; it will just use the browser voice."
  fi
fi

# ── 6. go ──────────────────────────────────────────────────────
PORT="$(envval JARVIS_PORT)"; PORT="${PORT:-8720}"
echo
bold "Starting JARVIS on http://localhost:$PORT"
note "Ctrl-C to stop. Re-run ./start.sh next time — setup only needs doing once."
echo
exec ./start.sh
