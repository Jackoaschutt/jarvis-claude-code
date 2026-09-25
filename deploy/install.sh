#!/usr/bin/env bash
# Install JARVIS as a pair of services that start on boot and restart on crash.
#
#     ./deploy/install.sh
#
# Run it on the always-on box, as the ordinary user JARVIS should run as —
# never as root. Safe to re-run; it rewrites the units and restarts.
set -u

cd "$(dirname "$0")/.." || exit 1
DIR="$(pwd -P)"
USER_NAME="$(id -un)"
HOME_DIR="$HOME"

bold() { printf "\033[1m%s\033[0m\n" "$1"; }
ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
bad()  { printf "  \033[31m✗\033[0m %s\n" "$1"; }
note() { printf "    %s\n" "$1"; }

echo
bold "JARVIS service install"
note "$DIR"
echo

fail=0

# ── root is fatal, not cosmetic ─────────────────────────────────
# The CLI refuses bypassPermissions as root, so a root install produces
# services that start cleanly and then fail every single turn.
if [ "$(id -u)" -eq 0 ]; then
  bad "running as root"
  note "The claude CLI refuses bypassPermissions as root, so JARVIS would"
  note "start fine and then fail on every question. Make a normal user:"
  note "    adduser jarvis && usermod -aG sudo jarvis && su - jarvis"
  note "then clone the repo again as that user and re-run this."
  echo; exit 1
fi
ok "running as $USER_NAME (not root)"

command -v systemctl >/dev/null 2>&1 && ok "systemd present" || { bad "no systemctl — this script is for a systemd Linux box"; fail=1; }
command -v python3   >/dev/null 2>&1 && ok "python3 $(python3 -V 2>&1 | cut -d' ' -f2)" || { bad "python3 missing: sudo apt install -y python3"; fail=1; }

if command -v claude >/dev/null 2>&1; then
  ok "claude $(claude --version 2>/dev/null | head -1)"
else
  bad "claude CLI not found"
  note "curl -fsSL https://claude.ai/install.sh | bash"
  note "then:  claude   (sign in — it prints a URL to open on your own machine)"
  fail=1
fi

if [ -f .env ]; then
  ok ".env present"
  chmod 600 .env 2>/dev/null && ok ".env locked to your user (chmod 600)"
  grep -q '^TELEGRAM_BOT_TOKEN=.\+' .env || { bad "no TELEGRAM_BOT_TOKEN in .env — run: python3 telegram_setup.py"; fail=1; }
  grep -q '^TELEGRAM_ALLOWED_IDS=.\+' .env || { bad "no TELEGRAM_ALLOWED_IDS in .env — run: python3 telegram_setup.py"; fail=1; }
  grep -q '^FISH_AUDIO_API_KEY=.\+' .env || note "no Fish Audio key — JARVIS will run, just without its voice"
else
  bad "no .env here"
  note "cp .env.example .env    then:  python3 telegram_setup.py"
  fail=1
fi

[ "$fail" -eq 1 ] && { echo; echo "  Fix the above, then run ./deploy/install.sh again."; echo; exit 1; }

# ── units ───────────────────────────────────────────────────────
mkdir -p logs "$HOME_DIR/.config/systemd/user"
UNIT_DIR="$HOME_DIR/.config/systemd/user"

cat > "$UNIT_DIR/jarvis.service" <<UNIT
[Unit]
Description=JARVIS memory HUD
After=network-online.target
Wants=network-online.target
# Never stop retrying. The default gives up after a few rapid restarts and
# leaves the unit dead, which on a small box means one memory spike takes
# JARVIS off the air until somebody notices hours later.
StartLimitIntervalSec=0

[Service]
Type=simple
WorkingDirectory=$DIR
ExecStart=$DIR/start.sh
Restart=always
RestartSec=5
# No browser on a headless box, and the CLI needs HOME to find its login.
Environment=JARVIS_OPEN=0
Environment=HOME=$HOME_DIR
StandardOutput=append:$DIR/logs/server.log
StandardError=append:$DIR/logs/server.log

[Install]
WantedBy=default.target
UNIT

cat > "$UNIT_DIR/jarvis-bridge.service" <<UNIT
[Unit]
Description=JARVIS Telegram bridge
# Start after the server, but do NOT bind to it.
#
# BindsTo used to be here, and it is a trap: when the server dies, systemd
# *stops* the bridge rather than failing it — and Restart=always does not
# apply to a unit that was stopped on purpose. The server then restarts
# itself and the bridge stays down, so the bot goes quiet with a healthy
# looking server beside it. That is silent, and it lasts until a human
# intervenes.
#
# Wants gives the ordering without the stop propagation. The bridge already
# copes with a missing server: it re-reads the token on every turn and
# retries its poll loop.
After=jarvis.service
Wants=jarvis.service
StartLimitIntervalSec=0

[Service]
Type=simple
WorkingDirectory=$DIR
ExecStart=/usr/bin/env python3 $DIR/telegram_bridge.py
Restart=always
RestartSec=10
Environment=HOME=$HOME_DIR
StandardOutput=append:$DIR/logs/bridge.log
StandardError=append:$DIR/logs/bridge.log

[Install]
WantedBy=default.target
UNIT

ok "wrote jarvis.service and jarvis-bridge.service"

# Without lingering, user services stop the moment you log out of SSH —
# which is exactly when you need them to keep running.
if loginctl enable-linger "$USER_NAME" 2>/dev/null; then
  ok "lingering enabled — services survive you logging out"
else
  bad "could not enable lingering (needs sudo once)"
  note "sudo loginctl enable-linger $USER_NAME"
fi

# Reaching this user with `su` gives no user systemd session, which is the
# normal way in from a provider's web console. Rather than sending people off
# to fix SSH, fall back to system units: they need no session, start at boot
# regardless of who is logged in, and are the better fit for a server anyway.
if ! systemctl --user daemon-reload 2>/dev/null; then
  note "no user systemd session (you probably got here with su) — using"
  note "system services instead, which do not need one."
  echo
  note "sudo will ask for ${USER_NAME}'s password."
  for unit in jarvis jarvis-bridge; do
    sudo cp "$UNIT_DIR/$unit.service" "/etc/systemd/system/$unit.service" || {
      bad "could not install system units — is $USER_NAME in the sudo group?"; exit 1; }
    # A system unit runs as root unless told otherwise, and the CLI refuses
    # bypassPermissions as root, so this line is what makes it work at all.
    sudo sed -i "/^\[Service\]/a User=$USER_NAME\nGroup=$USER_NAME" "/etc/systemd/system/$unit.service"
    sudo sed -i "s/^WantedBy=default.target/WantedBy=multi-user.target/" "/etc/systemd/system/$unit.service"
  done
  sudo systemctl daemon-reload
  sudo systemctl enable jarvis.service jarvis-bridge.service >/dev/null 2>&1
  sudo systemctl restart jarvis.service
  sleep 3
  sudo systemctl restart jarvis-bridge.service
  sleep 2
  echo
  bold "Status"
  for unit in jarvis jarvis-bridge; do
    state="$(systemctl is-active "$unit" 2>/dev/null)"
    if [ "$state" = "active" ]; then ok "$unit is running"; else
      bad "$unit is $state"; note "why:  sudo journalctl -u $unit -n 30 --no-pager"; fi
  done
  echo
  bold "From now on"
  note "watch:    sudo journalctl -u jarvis-bridge -f"
  note "restart:  sudo systemctl restart jarvis jarvis-bridge"
  note "update:   git pull && sudo systemctl restart jarvis jarvis-bridge"
  echo
  note "Both start on boot. Message your bot to check it."
  echo
  exit 0
fi
systemctl --user enable jarvis.service jarvis-bridge.service >/dev/null 2>&1
systemctl --user restart jarvis.service
sleep 3
systemctl --user restart jarvis-bridge.service
sleep 2

echo
bold "Status"
for unit in jarvis jarvis-bridge; do
  state="$(systemctl --user is-active "$unit" 2>/dev/null)"
  if [ "$state" = "active" ]; then
    ok "$unit is running"
  else
    bad "$unit is $state"
    note "why:  journalctl --user -u $unit -n 30 --no-pager"
  fi
done

echo
bold "From now on"
note "watch:    journalctl --user -u jarvis-bridge -f"
note "or:       tail -f $DIR/logs/bridge.log"
note "restart:  systemctl --user restart jarvis jarvis-bridge"
note "stop:     systemctl --user stop jarvis jarvis-bridge"
note "update:   git pull && systemctl --user restart jarvis jarvis-bridge"
echo
note "Both start on boot. Message your bot to check it."
echo
