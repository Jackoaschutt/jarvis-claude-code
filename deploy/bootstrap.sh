#!/usr/bin/env bash
# One paste, run as root, from a fresh Ubuntu box to almost-done.
#
#   curl -fsSL https://raw.githubusercontent.com/Jackoaschutt/jarvis-claude-code/main/deploy/bootstrap.sh -o /tmp/b.sh && bash /tmp/b.sh
#
# Does everything that does not need a human: makes the non-root user, installs
# git and the Claude CLI, clones the repo, creates .env, enables lingering.
#
# Deliberately leaves two things, because both need a person:
#   claude              — signing in needs a browser
#   telegram_setup.py   — the token is a secret and cannot live in a script
#
# No password is set for the new user and none is needed. You reach it with
# `su - jarvis` from this root console, which is already authenticated — so
# SSH, passwords and typing blind are all off the critical path.
#
# Safe to re-run: every step checks before acting.
set -u

USER_NAME="${JARVIS_USER:-jarvis}"
REPO="${JARVIS_REPO:-https://github.com/Jackoaschutt/jarvis-claude-code}"
DIR="/home/$USER_NAME/jarvis-claude-code"

bold() { printf "\033[1m%s\033[0m\n" "$1"; }
ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
bad()  { printf "  \033[31m✗\033[0m %s\n" "$1"; }
note() { printf "    %s\n" "$1"; }

echo
bold "JARVIS bootstrap"
echo

if [ "$(id -u)" -ne 0 ]; then
  bad "run this as root"
  note "You are $(id -un). In the DigitalOcean web console you are already root;"
  note "if you switched user, type  exit  and run it again."
  echo; exit 1
fi
ok "running as root"

# ── the user JARVIS will actually run as ────────────────────────
if id -u "$USER_NAME" >/dev/null 2>&1; then
  ok "user $USER_NAME already exists"
else
  adduser --disabled-password --gecos "" "$USER_NAME" >/dev/null 2>&1 \
    && ok "created user $USER_NAME" || { bad "could not create $USER_NAME"; exit 1; }
fi
usermod -aG sudo "$USER_NAME" 2>/dev/null && ok "$USER_NAME can use sudo"

# User services die at logout without this, which is exactly when they matter.
loginctl enable-linger "$USER_NAME" 2>/dev/null \
  && ok "lingering enabled" || note "lingering not enabled (fine on some hosts)"

# ── swap, if the box has none ───────────────────────────────────
if [ "$(swapon --show --noheadings 2>/dev/null | wc -l)" -gt 0 ]; then
  ok "swap already present"
elif fallocate -l 2G /swapfile 2>/dev/null && chmod 600 /swapfile && mkswap /swapfile >/dev/null 2>&1 && swapon /swapfile 2>/dev/null; then
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  ok "2G swap added (1GB of RAM is not enough on its own)"
else
  note "could not add swap — carry on, but watch memory"
fi

# ── packages ────────────────────────────────────────────────────
if command -v git >/dev/null 2>&1; then
  ok "git present"
else
  note "installing git…"
  DEBIAN_FRONTEND=noninteractive apt-get update -qq >/dev/null 2>&1
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git >/dev/null 2>&1 \
    && ok "git installed" || { bad "could not install git"; exit 1; }
fi
command -v python3 >/dev/null 2>&1 && ok "python3 $(python3 -V 2>&1 | cut -d' ' -f2)" \
  || { bad "python3 missing"; exit 1; }

# ── Claude CLI, as the user, never as root ──────────────────────
if su - "$USER_NAME" -c 'command -v claude >/dev/null 2>&1 || [ -x "$HOME/.local/bin/claude" ]'; then
  ok "claude already installed for $USER_NAME"
else
  note "installing the Claude CLI…"
  su - "$USER_NAME" -c 'curl -fsSL https://claude.ai/install.sh | bash' >/dev/null 2>&1
  if su - "$USER_NAME" -c '[ -x "$HOME/.local/bin/claude" ]'; then
    ok "claude installed"
  else
    bad "claude install failed — try it by hand after su - $USER_NAME"
  fi
fi
# The installer warns about this rather than doing it, and without it the
# service units cannot find the binary.
su - "$USER_NAME" -c 'grep -q ".local/bin" ~/.bashrc 2>/dev/null || echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> ~/.bashrc'
ok "PATH set for $USER_NAME"

# ── the repo ────────────────────────────────────────────────────
if [ -d "$DIR/.git" ]; then
  su - "$USER_NAME" -c "cd '$DIR' && git pull --ff-only" >/dev/null 2>&1 \
    && ok "repo updated" || ok "repo already here"
else
  su - "$USER_NAME" -c "git clone -q '$REPO' '$DIR'" \
    && ok "cloned into $DIR" || { bad "clone failed"; exit 1; }
fi

su - "$USER_NAME" -c "cd '$DIR' && [ -f .env ] || cp .env.example .env"
su - "$USER_NAME" -c "chmod 600 '$DIR/.env' 2>/dev/null"
ok ".env ready"

echo
bold "Two things left, both need you"
echo
note "1.  su - $USER_NAME"
note "    cd jarvis-claude-code"
echo
note "2.  claude"
note "    Press c to copy the URL, open it on your own computer, sign in,"
note "    paste the code back. Then /exit."
echo
note "3.  python3 telegram_setup.py --show"
note "    Bot token, then your Telegram user id. --show lets you see the"
note "    token land, which matters in a browser console."
echo
note "4.  ./deploy/install.sh"
note "    Starts JARVIS and the bot as services, on boot, forever."
echo
bold "No password needed for any of it — su works because you are root."
echo
