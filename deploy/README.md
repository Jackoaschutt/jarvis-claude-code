# Running JARVIS always-on

A laptop that sleeps is a JARVIS that sleeps. This puts it on a small Linux box
that never does, so the Telegram bot answers whether or not your machine is
open — or switched on, or with you.

Everything here is the same JARVIS. Same vault, same voice, same bot. Only the
computer changes.

## What you need

A cheap VPS running Ubuntu. Around €4–6 a month buys plenty at Hetzner,
DigitalOcean, Vultr or similar; check current pricing, it moves.

**Take 2GB of RAM rather than 1.** The Claude CLI is a Node process and 1GB
works right up until it doesn't, which will happen while you are out.

## 1. Make the box

Create the smallest Ubuntu LTS instance. Add your SSH key during setup rather
than using a password — you will be leaving this machine running unattended.

SSH in as root, then immediately make an ordinary user and stop working as root:

```bash
adduser jarvis
usermod -aG sudo jarvis
su - jarvis
```

This is not housekeeping. The `claude` CLI refuses `bypassPermissions` when run
as root, so a root install gives you services that start perfectly and then
fail on every single question. The installer refuses to run as root for exactly
this reason.

## 2. Install Claude Code and sign in

```bash
curl -fsSL https://claude.ai/install.sh | bash
exec $SHELL -l
claude
```

`claude` prints a URL. Open it in the browser on your own machine, sign in with
your Claude subscription, and paste the code back into the terminal. Type
`/exit` once you are in.

Same subscription, no API key, no per-token billing — the box is just another
place you are signed in.

## 3. Get JARVIS

```bash
git clone https://github.com/Jackoaschutt/jarvis-claude-code
cd jarvis-claude-code
cp .env.example .env
```

Put your Fish Audio key in `.env`, then set up Telegram:

```bash
python3 telegram_setup.py
```

Same as on your laptop: paste the token, type your user id. The credentials
live only on this box; nothing is copied from your Mac.

## 4. Install the services

```bash
./deploy/install.sh
```

That writes two systemd units, enables them at boot, and starts them:

- **jarvis** — the server and the memory graph
- **jarvis-bridge** — the Telegram bot, restarted whenever the server is

It also enables *lingering*, without which user services stop the moment you
log out of SSH — which is precisely when you need them running.

## 5. Stop the bridge on your laptop

**Do not skip this.** Telegram allows one `getUpdates` in flight per bot, so a
laptop bridge and a VPS bridge will take turns stealing each other's messages.
The bot appears to answer about half of what you send.

On your Mac:

```bash
pkill -f telegram_bridge.py
```

The single-instance guard only sees the machine it runs on, so this one is on
you. Leave `./start.sh` running locally if you still want the HUD — the server
is fine to have in both places, it is the *bridge* that must be unique.

## Living with it

```bash
journalctl --user -u jarvis-bridge -f          # watch it work, live
systemctl --user restart jarvis jarvis-bridge  # after changing .env
git pull && systemctl --user restart jarvis jarvis-bridge   # update
systemctl --user status jarvis                 # is it alive
```

Both services restart on crash and come back on reboot. There is nothing to
start by hand again.

## Where your notes live now

The VPS has its own copy of the vault, and it is the one JARVIS writes to. Notes
it adds — including the Build log — stay there until you move them.

To bring them back to your laptop, from the VPS:

```bash
git add vault-agency && git commit -m "vault: notes from this week" && git push
```

then on your Mac, `git pull`.

Treat the VPS as the real vault and the laptop as a copy, rather than editing
both. Two people editing the same markdown in two places is a merge conflict
waiting for the least convenient moment.

## What is exposed

Almost nothing, and that is deliberate.

The server still binds `127.0.0.1`, so the HUD is not reachable from the
internet even though the box is. The only inbound path is Telegram, and the
bridge answers nobody but the ids in `TELEGRAM_ALLOWED_IDS`. `install.sh`
chmods `.env` to 600.

Worth remembering what this machine is: JARVIS runs `claude` with
`bypassPermissions`, so anyone who gets a shell on it can run commands as your
user, and anyone who gets your bot token can read what you send the bot. Use an
SSH key, keep the box updated (`sudo apt update && sudo apt upgrade`), and do
not put anything on it you would not put on your laptop.
