"""
Write the real vault: LeadBack as it actually stands.

    python3 seed_leadback.py            # show what would be written
    python3 seed_leadback.py --yes      # write it

Run `clear_sample_vault.py --yes` first. This adds notes; it deletes nothing,
and overwrites only notes of the same name it wrote before.

Sources: leadback.tech as it reads on 2026-11-25, and JARVIS's own account of
the build from 24 September to today. Where something is not known there is a
note saying so, rather than a plausible number.

That rule is the point. These notes go into Claude's system prompt on every
turn via `commands.context_block`, so an invention here does not sit quietly
in a file — it becomes something JARVIS believes and reasons from. The vault
this replaced was 133 invented notes, and it shaped two months of answers.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
VAULT = ROOT / "vault"
TODAY = "2026-11-25"

# (title, type, body, [links])
NOTES = [
    # ── the business ────────────────────────────────────────────
    ("LeadBack", "project", """
Missed call text back for tradies. leadback.tech.

From the site: "Missed a call on the tools? Don't miss the job. LeadBack texts
every missed caller back in seconds, so they wait for you instead of ringing
the next tradie on Google." Positioned as "Built in Brisbane for Aussie
trades".

Started 24 September 2026. Paused 4 October for trading, restarted 11
November. Essentially complete as a product and has never been sold.

Read [[Traction]] before forming any view about how it is going.
""", ["Traction", "Missed call text back", "Tradies", "The offer", "Pricing",
      "The product", "The marketing site", "What is blocking revenue",
      "Correction — LeadBack is not the dealership idea"]),

    ("Missed call text back", "concept", """
A call comes in unanswered; within about five seconds an SMS goes to that
number and a conversation starts.

The site's worked example: missed call 2:14pm, auto-text five seconds later —
"Hi Sarah, sorry we missed your call! We're on a job. What can we help with?"
She asks for a bathroom reno quote in Paddington, books Thursday. JOB BOOKED ·
$8,400.

It never cold-contacts anyone. It only replies to someone who just rang, which
is both the appeal and why it sits on safer legal ground than outbound.
""", ["LeadBack", "The webhooks", "Risk — Australian SMS rules"]),

    ("Tradies", "concept", """
Australian trades — plumbers, sparkies, builders. The operator who is up a
ladder or under a sink when the phone rings.

Two things shape everything: they cannot answer mid-job, and they are usually
the owner, so a missed call is money out of their own pocket.
""", ["LeadBack", "Why callers do not wait"]),

    ("Why callers do not wait", "concept", """
The premise the product rests on, in the site's words:

- "Most callers won't leave a voicemail. They just ring the next [tradie]"
- "Minutes, not hours is how long a new customer waits before trying [another]"
- "5 seconds is how long LeadBack takes to text them back"

The competitor is not another app. It is the next search result.
""", ["LeadBack", "Missed call text back"]),

    ("The offer", "concept", """
"Start free 14-day trial". Underneath: "No card. No lock-in. Up and running
the same day."

Each line removes an objection — risk, commitment, setup. Worth keeping
intact: a tradesman who has to ring a salesperson will not get started.

Second call to action is "What are missed calls costing me?", which sells the
problem rather than the product.
""", ["LeadBack", "Pricing", "The marketing site"]),

    ("Pricing", "note", """
$79 a month, published on the landing page.

Billing is built end to end and has never been switched on. See
[[Stripe billing]].

No customer has ever been charged, so the price is a number on a page rather
than something the market has answered.
""", ["LeadBack", "The offer", "Stripe billing", "Traction"]),

    # ── the truth ───────────────────────────────────────────────
    ("Traction", "note", """
The number that matters, as of 25 November 2026.

- **Six leads in the database. Ever.** Four in September, two in October, none
  since 23 October.
- **Every one of them is my own.** Three businesses in the system, all mine.
- **Zero paying clients.**
- **$0 spent on Meta ads**, across a campaign built, paused, resumed, paused.
- **Zero outreach emails sent**, out of thirty drafted.

So the product is not only unsold, it is unvalidated: no stranger has ever used
it. "Everything works" means twenty-one checks pass, not that a real tradie's
real customer was texted back and booked a real job.

Two months of building. The whole gap is between built and sold.
""", ["LeadBack", "What is blocking revenue", "The outreach list",
      "The ad campaign", "Pricing"]),

    ("What is blocking revenue", "note", """
Not engineering. Every remaining blocker is administrative, cheap, and
measured in minutes.

- **No Stripe account.** Billing is built and cannot be switched on. Free,
  about twenty minutes.
- **No mailbox.** Thirty researched tradies and thirty drafted emails cannot
  be sent. A few dollars a month.
- **Twilio needs topping up** for live numbers.
- **No ad spend.** Creatives are finished and the campaign is paused.

The asymmetry is the finding: two months of building against perhaps an
afternoon of admin, and the admin is what stands between this and a first
customer.
""", ["Traction", "Stripe billing", "The outreach list", "The ad campaign"]),

    # ── what exists ─────────────────────────────────────────────
    ("The product", "project", """
Next.js on Vercel, Supabase for data and auth, Twilio for voice and SMS.

Built: magic-link and password login, two-step sign-up with a texted code,
onboarding, a leads inbox, a chat-style thread you can reply to, and settings.
An admin console for sign-ups.

Hands-free activation buys the client an Australian number by itself. That
went live on 25 September when Twilio approved the regulatory bundle in about
half an hour.
""", ["LeadBack", "The webhooks", "The dashboard", "Hands-free activation",
      "Hosting"]),

    ("The webhooks", "concept", """
Three, all signature-verified: catch the missed call, ring the tradie, text
the caller back and log the lead.

The Twilio fallback was rewritten in plain Python on 25 November, to work
around the droplet no longer being able to build the Next app. See
[[The droplet cannot build]].
""", ["The product", "Missed call text back", "The droplet cannot build"]),

    ("Hands-free activation", "concept", """
A new client gets an Australian phone number bought and configured for them
without anyone touching it. Live since 25 September.

This is the part that makes "up and running the same day" true rather than
marketing.
""", ["The product", "The offer"]),

    ("Urgency scorer", "concept", """
Reads the words in a lead's text and the pattern of their calls, and ranks how
urgent the job is — a burst pipe or no power jumps the queue ahead of a quote
request.

src/lib/urgency.ts. Built in one JARVIS session on 25 September — the session
that reported "timed out" while still working. The code landed; the message
did not.
""", ["The product", "Outage history"]),

    ("Win-loss follow-up", "concept", """
Hourly "did you win it?" texts to the tradie. A one-letter reply marks the job
won or lost.

The quiet value here is data: it is the only mechanism that would ever tell
you what LeadBack is actually worth per customer. With six leads and no
clients it has nothing to measure yet.
""", ["The product", "Traction"]),

    ("Friday recap", "concept", """
A weekly text to each client summarising their week.

Retention mechanic: it puts the product's value in front of someone who
otherwise only notices it when they are busy.
""", ["The product"]),

    ("The dashboard", "note", """
Rebuilt three times. The current one has a sidebar, a money hero and a
pipeline board.

The first was called horrendous, which was correct and useful. Worth
remembering that the third attempt is the one that worked.
""", ["The product"]),

    ("The marketing site", "project", """
Twenty-three URLs: landing page with an ROI calculator, product page, pricing
page, eight trade pages, six city pages, five guides. Sitemap, structured
data, share images, Search Console tag. Brand images for the Facebook page.

Built for organic search. Nothing is known about whether any of it ranks or
has ever been visited.
""", ["LeadBack", "The offer", "Open question — Traffic"]),

    ("Stripe billing", "project", """
Checkout, customer portal, webhook, paywall and trial countdown. Built end to
end.

**Never switched on, because there is no Stripe account.** Nothing can be
charged until there is. See [[What is blocking revenue]].
""", ["Pricing", "What is blocking revenue", "Traction"]),

    ("The ad campaign", "project", """
Seven still creatives and three silent video ads, plus a page for choosing
between them. The videos now play correctly on iPhone as of 25 November.

Campaign built, paused, resumed, paused again. **Total spent on Meta: nothing.**
""", ["Traction", "What is blocking revenue"]),

    ("The outreach list", "project", """
Thirty Brisbane tradies researched, thirty emails drafted, a sender script
written.

**Not one sent. There is no mailbox to send from.**

This is the cheapest untried route to a first customer — the list already
exists and the writing is done.
""", ["Traction", "What is blocking revenue", "Tradies"]),

    # ── risks and unknowns ──────────────────────────────────────
    ("Risk — Australian SMS rules", "note", """
Australian regime: the Spam Act 2003 and the Do Not Call Register, not the
American TCPA.

The position is strong — LeadBack only texts someone who just rang the
business, which is inferred consent from an inbound contact rather than a
purchased list.

Still needs checking rather than assuming: a working opt-out on every message,
clear sender identification, and that consent covers this enquiry and not
later marketing. Not known whether anyone qualified has reviewed it.
""", ["LeadBack", "Missed call text back"]),

    ("Open question — Traffic", "note", """
Not known: whether the twenty-three marketing URLs have ever been visited,
whether anything ranks, and whether the Search Console tag has been checked
since it was added.

Twenty-three pages with no traffic data is twenty-three pages of assumption.
""", ["The marketing site", "Traction"]),

    ("Correction — LeadBack is not the dealership idea", "note", """
Load-bearing, because the wrong version was discussed here at length.

In September 2026 a different business was worked through in detail: recovering
dead leads for car dealerships on a 30/60/90 day cycle, kill-tested, with
conclusions about American TCPA consent, competitors like AutoAlert, and why
performance-only pricing is a trap.

LeadBack is not that. Different customer, different country, different
mechanism — replying to a live inbound call, not chasing a cold one.

That analysis does not transfer. If a dealership conclusion is ever reached
for, it is the wrong file.
""", ["LeadBack"]),

    # ── the machinery ───────────────────────────────────────────
    ("Hosting", "note", """
Vercel is primary and serves leadback.tech, moved there on 25 September. The
Vercel connector would not create projects, so a spare project was taken over
instead.

The droplet runs as the backup. See [[The droplet cannot build]].
""", ["The product", "The droplet", "The droplet cannot build"]),

    ("The droplet cannot build", "note", """
During the October gap something deleted the app's dependencies, and the
droplet lost the ability to rebuild: 900MB of usable RAM will not compile
Next 16.

Worked around on 25 November by rewriting the Twilio fallback in plain Python,
so the backup works without a build step. Twenty-one checks pass.

The underlying cause is the box being too small. A resize to 2GB has been the
right call since September.
""", ["The droplet", "Hosting", "The webhooks"]),

    ("JARVIS", "project", """
This system. A Claude Code front end with a memory vault, reachable three
ways: Telegram, the HUD over Tailscale, and the console on the droplet.

Runs on a Claude subscription through the CLI — never an API key, which would
bypass the subscription and bill per token.

/status in Telegram reports what it is doing, disk and memory, and what it
last built.
""", ["The droplet", "Outage history", "Hermes", "Trading lab"]),

    ("The droplet", "note", """
One DigitalOcean box in NYC1 running JARVIS, the Telegram bridge, the LeadBack
backup and Hermes.

1GB RAM, 24GB disk, one CPU. Undersized — swap sits around 40% at idle, and it
can no longer build the app. A resize to 2GB/50GB has been right since
September and has not been done.

Owner is in Brisbane, UTC+10, so the box's UTC clock reads ten hours behind
local. OpenRouter's free quota resets at midnight UTC, which is 10am local.
""", ["JARVIS", "Outage history", "Hermes", "The droplet cannot build"]),

    ("Outage history", "note", """
What has actually taken this system down, so it is not rediagnosed each time.

- **systemd BindsTo.** The bridge was bound to the server, so when the server
  died systemd *stopped* the bridge, and Restart=always does not apply to a
  deliberate stop. Fixed with Wants.
- **Disk full.** Hit 100%. Not logs, not the vault: 11GB of container images
  from Hermes plus a 4.6GB npm cache. A full disk is worse than a crash,
  because JARVIS keeps answering while every write fails.
- **Expired login.** The Claude CLI session expired and every turn failed for
  five weeks, showing "API Usage Billing". Fixed with /login.
- **Silent long turns.** A build past the bridge timeout reported "timed out"
  while still working, then HTTP 409 on the next message.
- **Un-rotated logs.** Services appended to logs/*.log with nothing rotating
  them. Now the journal, which caps itself.

The pattern: in every case JARVIS looked broken and mostly was not. The
failures were in how it reported itself.
""", ["JARVIS", "The droplet"]),

    ("Hermes", "project", """
A separate Discord bot on the same droplet — Nous Research's Hermes agent in
Docker, about 10GB of images. Nothing to do with LeadBack; it just shares the
machine, which is why it died when the disk filled.

Rationed rather than broken: three to ten model calls per message against free
tiers built to stop exactly that. Groq's free tier cannot run it at all —
8,000 tokens a minute against an agent needing more than that for one message.
$10 of OpenRouter credit fixes it.
""", ["The droplet", "JARVIS"]),

    ("Trading lab", "project", """
Separate from LeadBack. A strategy called Razz's Odds (v3 SIM), forward-tested
in TradingView since 12 October 2026, judged on trades, profit factor and
drawdown under a 40-trade kill rule.

LeadBack was paused on 4 October for this and restarted on 11 November.

The kill rule is the good part. Below about 40 trades profit factor is mostly
noise, and tuning a strategy on the sample you measured it with is how a
working system gets destroyed. JARVIS runs the weekly check.
""", ["JARVIS", "LeadBack"]),
]


def body_for(title, ntype, text, links):
    link_line = ("\n\n" + " ".join(f"[[{l}]]" for l in links)) if links else ""
    return (f"---\ntype: {ntype}\nupdated: {TODAY}\n---\n\n"
            f"# {title}\n{text.rstrip()}{link_line}\n")


def main():
    write = "--yes" in sys.argv
    vault = pathlib.Path(sys.argv[sys.argv.index("--vault") + 1]
                         if "--vault" in sys.argv else VAULT)
    if not vault.is_dir():
        sys.exit(f"  No vault at {vault}")

    existing = {p.name for p in vault.rglob("*.md")}
    print(f"\n  vault   {vault}")
    print(f"  has     {len(existing)} notes\n")
    for title, ntype, text, links in NOTES:
        mark = "overwrite" if f"{title}.md" in existing else "new"
        print(f"    {mark:<10} {title}")
        if write:
            (vault / f"{title}.md").write_text(body_for(title, ntype, text, links),
                                               encoding="utf-8")
    # The Build log hangs off [[Agency]] in older vaults — a note the sample
    # provided. With the sample cleared that link dangles and the one genuine
    # record of what JARVIS built floats unconnected. journal.py migrates it on
    # its next write, but that may be days away, so do it now.
    log = vault / "Build log.md"
    if log.exists():
        text = log.read_text(encoding="utf-8")
        if "[[Agency]]" in text:
            print(f"    {'migrate':<10} Build log  ([[Agency]] -> [[JARVIS]])")
            if write:
                log.write_text(text.replace("[[Agency]]", "[[JARVIS]]"),
                               encoding="utf-8")

    print()
    if not write:
        print(f"  Dry run. To write these {len(NOTES)} notes:")
        print(f"      python3 {pathlib.Path(__file__).name} --yes\n")
        return
    print(f"  Wrote {len(NOTES)} notes. Run /graph in the HUD to reload memory.\n")


if __name__ == "__main__":
    main()
