"""
Write the real vault: LeadBack, the machine it runs on, and what is unknown.

    python3 seed_leadback.py            # show what would be written
    python3 seed_leadback.py --yes      # write it

Run `clear_sample_vault.py --yes` first. This does not delete anything; it
adds notes, overwriting only ones of the same name it wrote before.

Every claim about the product is taken from leadback.tech as it reads on
2026-11-25, and the wording is quoted where it matters. Where something is
not known — pricing, how many customers, whether anyone has churned — there
is a note saying so, rather than a plausible number.

That is the whole design. These notes go into Claude's system prompt on every
turn via `commands.context_block`, so a confident invention here does not sit
quietly in a file: it becomes something JARVIS believes and reasons from. An
"unknown" is worth more than a guess, because JARVIS can ask about an unknown.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
VAULT = pathlib.Path(__file__).resolve().parent / "vault"
TODAY = "2026-11-25"

# (title, type, body, [links])
NOTES = [
    ("LeadBack", "project", """
Missed call text back for tradies. The business.

From the site: "Missed a call on the tools? Don't miss the job. LeadBack texts
every missed caller back in seconds, so they wait for you instead of ringing
the next tradie on Google."

Positioned as "Built in Brisbane for Aussie trades". leadback.tech.

The sales argument in one line: a tradesman cannot answer the phone with his
hands full, and the caller will not wait. LeadBack answers for him in five
seconds by text, which is enough to stop the caller moving on.
""", ["Missed call text back", "Tradies", "The offer", "Why callers do not wait",
      "LeadBack app", "Risk — Australian SMS rules", "Open question — Pricing",
      "Open question — Customers"]),

    ("Missed call text back", "concept", """
The mechanism. A call comes in and is not answered; within about five seconds
an SMS goes to that number and a conversation starts.

The site's worked example: missed call at 2:14pm, automatic text "Hi Sarah,
sorry we missed your call! We're on a job. What can we help with?" sent five
seconds later. She replies asking for a bathroom reno quote in Paddington.
Booked for Thursday. Marked JOB BOOKED · $8,400.

Note what the mechanism is not. It does not cold-call, and it does not chase
old leads. It only ever replies to somebody who just rang, which is both the
product's appeal and the reason it sits on much safer ground than outbound.
""", ["LeadBack", "Why callers do not wait", "Risk — Australian SMS rules"]),

    ("Tradies", "concept", """
The customer. Australian trades — the site says "Built in Brisbane for Aussie
trades". Plumbers, sparkies, builders, the sort of operator who is up a ladder
or under a sink when the phone goes.

Two things about them that shape the product: they cannot answer mid-job, and
they are usually the business owner, so a missed call is money out of their own
pocket rather than a statistic on somebody's dashboard.
""", ["LeadBack", "Why callers do not wait"]),

    ("Why callers do not wait", "concept", """
The premise the whole product rests on, in the site's own words:

- "Most callers won't leave a voicemail. They just ring the next [tradie]"
- "Minutes, not hours is how long a new customer waits before trying [another]"
- "5 seconds is how long LeadBack takes to text them back"

So the competitor is not another app. It is the next search result. The window
is minutes, and voicemail does not hold it open.
""", ["LeadBack", "Missed call text back"]),

    ("The offer", "concept", """
From the site: "Start free 14-day trial", and underneath, "No card. No lock-in.
Up and running the same day."

Every one of those removes a specific objection — risk, commitment, and the
fear of a week of setup. Worth keeping intact: a tradesman who has to ring a
salesperson to get started will not get started.

The second call to action is "What are missed calls costing me?", which sells
the problem rather than the product.
""", ["LeadBack", "Open question — Pricing"]),

    ("LeadBack app", "project", """
The build, on the JARVIS droplet at ~/leadback.

Next.js. Known pieces:
- src/lib/urgency.ts — ranks how urgent an incoming enquiry is
- src/app/api/twilio/sms/route.ts — the Twilio SMS webhook

Also ~/leadback-ads and ~/leadback-upload, purpose not recorded here.

Unknown: whether this is what serves leadback.tech today, or a work in
progress alongside it.
""", ["LeadBack", "Urgency ranking", "The droplet"]),

    ("Urgency ranking", "concept", """
src/lib/urgency.ts in the LeadBack app. Scores an incoming enquiry so the
urgent ones surface first.

Built in a single JARVIS session on 2026-09-25. That session is also the one
that appeared to fail — it ran past the bridge's five minute timeout and
reported "timed out" while still working. The code landed; the message did
not.
""", ["LeadBack app", "Outage history"]),

    ("Risk — Australian SMS rules", "note", """
LeadBack is Australian, so the regime is the Spam Act 2003 and the Do Not Call
Register, not the American TCPA.

The product's position is unusually strong here: it only ever texts somebody
who has just rung the business. That is about as clean a consent story as
automated SMS gets — inferred consent from an inbound contact, not a purchased
list.

What still needs checking rather than assuming:
- every message needs a working opt-out, and it must actually work
- sender identification must be clear
- consent is for this enquiry, not a licence to market later

Not currently known whether any of this has been reviewed by anyone qualified.
Worth doing before the first complaint rather than after.
""", ["LeadBack", "Missed call text back"]),

    ("Open question — Pricing", "note", """
Not known. The site has a Pricing page; its contents have not been captured
into this vault.

Until it is, nothing here should state or imply what LeadBack costs.
""", ["LeadBack", "The offer"]),

    ("Open question — Customers", "note", """
Not known, and worth being blunt about:

- how many tradies are on a trial right now
- how many are paying
- whether anyone has cancelled, and why
- how many missed calls have actually been texted back

Nothing in this vault should imply an answer to any of these. The right move
is to ask rather than guess.
""", ["LeadBack"]),

    ("Correction — LeadBack is not the dealership idea", "note", """
Load-bearing, because the wrong version was discussed at length.

In September 2026 a business idea was worked through here in detail: recovering
dead leads for car dealerships, chased on a 30/60/90 day cycle. It was
kill-tested, and the conclusions were about American TCPA consent, competitors
like AutoAlert, and why performance-only pricing is a trap.

LeadBack is not that. It is missed call text back for Australian tradespeople.
Different customer, different country, different mechanism — replying to a live
inbound call rather than chasing a cold one.

That earlier analysis does not transfer. If a dealership conclusion is ever
reached for, it is the wrong file.
""", ["LeadBack"]),

    ("JARVIS", "project", """
This system. A Claude Code front end with a memory vault, reachable three ways:
Telegram, the HUD over Tailscale, and the console on the droplet.

Runs on a Claude subscription through the CLI — never an API key, which would
bypass the subscription and bill per token.

/status in Telegram reports what it is doing, disk and memory, and what it last
built.
""", ["The droplet", "Outage history", "Hermes"]),

    ("The droplet", "note", """
One DigitalOcean box in NYC1 running everything: JARVIS, the Telegram bridge,
the LeadBack app, and Hermes.

1GB RAM, 24GB disk, one CPU. Undersized for what is on it — swap sits around
40% at idle. A resize to 2GB/50GB has been the right call since September and
has not been done.

Owner is in Brisbane, UTC+10, so the box's UTC clock reads ten hours behind
local time. OpenRouter's daily free quota resets at midnight UTC, which is
10am local.
""", ["JARVIS", "Outage history", "Hermes"]),

    ("Outage history", "note", """
What has actually taken this system down, so it is not rediagnosed from
scratch each time.

- **systemd BindsTo.** The bridge was bound to the server, so when the server
  died systemd *stopped* the bridge rather than failing it, and Restart=always
  does not apply to a deliberate stop. Server came back; bridge did not. Fixed
  by using Wants.
- **Disk full.** Hit 100%. Not logs and not the vault: 11GB of container images
  in /var/lib/containerd from Hermes, plus a 4.6GB npm cache. A full disk is
  worse than a crash, because JARVIS keeps answering while every write fails.
- **Expired login.** The Claude CLI's session expired and every turn failed for
  five weeks. The header read "API Usage Billing" and nothing ran. Fixed with
  /login.
- **Silent long turns.** A build that ran past the bridge's timeout reported
  "timed out" while still working, then "HTTP 409" on the next message. Both
  now explained in plain words.
- **Un-rotated logs.** The services appended to logs/*.log with nothing to
  rotate them. Now they use the journal, which caps itself.

The pattern worth remembering: in every case JARVIS looked broken and mostly
was not. The failures were in how it reported itself.
""", ["JARVIS", "The droplet"]),

    ("Hermes", "project", """
A separate Discord bot on the same droplet. Nous Research's Hermes agent, in
Docker — containers "hermes" and "hermes-dashboard", about 10GB of images.

Nothing to do with LeadBack or JARVIS; it just shares the machine. Which is
why it went down with them when the disk filled.

Rationed rather than broken. It makes three to ten model calls per message, and
free tiers are built to stop exactly that, so it runs out after a handful of
messages a day. Groq's free tier cannot run it at all — 8,000 tokens a minute
against an agent that needs more than that for one message. $10 of OpenRouter
credit fixes it properly; that has not been spent.
""", ["The droplet", "JARVIS"]),

    ("Trading lab", "project", """
A separate thread from LeadBack. A strategy called Razz's Odds (v3 SIM) being
forward-tested in TradingView since 12 October 2026, judged on trades, profit
factor and drawdown, under a 40-trade kill rule.

The kill rule is the good part and should be left alone. Below about 40 trades
profit factor is mostly noise, and tuning a strategy on the sample you measured
it with is how a working system gets destroyed.

JARVIS runs the weekly check: export the trade list from the Strategy Tester
and it reports trades, profit factor, drawdown and where the kill rule stands.
""", ["JARVIS"]),
]


def body_for(title, ntype, text, links):
    link_line = ("\n\n" + " ".join(f"[[{l}]]" for l in links)) if links else ""
    return (f"---\ntype: {ntype}\nupdated: {TODAY}\n---\n\n"
            f"# {title}\n{text.rstrip()}{link_line}\n")


def main():
    write = "--yes" in sys.argv
    if not VAULT.is_dir():
        sys.exit(f"  No vault at {VAULT}")

    existing = {p.name for p in VAULT.rglob("*.md")}
    print(f"\n  vault   {VAULT}")
    print(f"  has     {len(existing)} notes\n")
    for title, ntype, text, links in NOTES:
        name = f"{title}.md"
        mark = "overwrite" if name in existing else "new"
        print(f"    {mark:<10} {title}")
        if write:
            (VAULT / name).write_text(body_for(title, ntype, text, links),
                                      encoding="utf-8")
    print()
    if not write:
        print(f"  Dry run. To write these {len(NOTES)} notes:")
        print(f"      python3 {pathlib.Path(__file__).name} --yes\n")
        return
    print(f"  Wrote {len(NOTES)} notes. Run /graph in the HUD to reload memory.\n")


if __name__ == "__main__":
    main()
