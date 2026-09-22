"""
Seed a starter vault for a missed-call-rescue agency.

    python3 seed_agency.py

Writes vault-agency/ next to the demo vault. Nothing is deleted — point
JARVIS at it with JARVIS_VAULT and the demo stays where it is.

These are opinionated starting notes, not filler. Every number in them is a
placeholder you should replace with a real one the moment you learn it: the
whole point of the vault is that JARVIS reasons about your actual business,
and it cannot tell the difference between a figure you verified and one that
came from here.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "vault-agency"
TODAY = "2026-09-22"

NOTES = {
"Agency": ("project", """
The business. One operator, one offer, one industry: recovering jobs that
high-ticket trades lose to missed calls.

Not "AI automation for small businesses". That sentence gets no meetings
because nobody hears themselves in it. See [[Positioning]].

Current stage: no clients. The only thing that matters this week is
[[SOP — After hours call test]], because it produces proof and a prospect
list at the same time.

[[Positioning]] [[Offer — Missed call rescue]] [[Week one]] [[Goal]]
"""),

"Positioning": ("concept", """
The sentence people repeat when they describe you to someone else.

Bad: I do AI automation for small businesses.
Good: I stop roofers losing jobs to missed calls.

The good one names who and names a problem they already feel. It is narrower
than the work you can actually do, and that is the point — narrow gets the
meeting, and the meeting is where the rest comes out.

Pick one trade and say only that until it stops working.

[[ICP — High ticket home services]] [[Offer — Missed call rescue]]
"""),

"ICP — High ticket home services": ("concept", """
Who this is for. Roofing, HVAC, electrical, plumbing, solar — anywhere a
single job is thousands rather than hundreds.

Filters that matter:
Owner-operated, two to fifteen staff. A mobile number on the website rather
than a switchboard. No dedicated receptionist. Job value above two thousand.

Signs they are bleeding: reviews that mention nobody called back, a voicemail
that is full, a contact form that goes nowhere.

Ruled out deliberately: salons, cafes, anything where a lost customer is
worth under two hundred. The arithmetic never gets compelling enough to pay
for the service. See [[ROI maths]].

[[Positioning]] [[Prospect list]] [[ROI maths]]
"""),

"Offer — Missed call rescue": ("proposal", """
One offer. Resist adding a second until this one has sold three times.

When a call comes in and nobody answers, a text goes out inside sixty
seconds: apologises, asks what the job is and where. The reply lands
somewhere the owner actually looks. Urgent jobs escalate straight to him.

Weekly summary: calls missed, conversations recovered, jobs booked.

What it is not: a chatbot on the website, a receptionist replacement, or
anything that pretends to be human. Trades customers tolerate an honest
automated text. They hate a robot pretending to be Dave.

[[Pricing]] [[SOP — Build the missed call responder]] [[Proof]]
"""),

"Pricing": ("concept", """
Setup fee plus monthly. Never hourly — hourly invites a conversation about
how long it took, which is the wrong conversation.

Opening numbers: seven hundred fifty to set up, four hundred a month.

Anchor against one job, not against other software. "One recovered job pays
for the year" is the whole argument, and for a roofer it is literally true.

Do not discount the monthly to win the first client. Discount the setup if
you must — it is one-off, and it does not teach them that your price moves.

[[ROI maths]] [[Offer — Missed call rescue]] [[Objections]]
"""),

"ROI maths": ("concept", """
The argument that does the selling. Run it with their numbers, out loud, on
the first call.

Ask: what is an average job worth? How many calls come in on a normal week?
Roughly how many get missed?

Then: eleven missed calls a week, one in five was a real job, average job
four thousand. That is a recovered job most weeks. The service is four
hundred a month.

Never present this as a projection. Present it as a question and let them do
the multiplication themselves — the number they say out loud is the one they
believe.

[[Pricing]] [[SOP — First call]]
"""),

"Proof": ("concept", """
The demo that closes, and it takes nine seconds.

Ring their business number while sitting in front of them. Nobody answers.
Let the silence run a beat longer than is comfortable.

Then: that just happened to eleven people this week, and none of them rang
back.

No slides. No mention of models, agents or automation. The product is the
text that arrives; the pitch is the call that does not get answered.

[[SOP — After hours call test]] [[SOP — First call]]
"""),

"SOP — After hours call test": ("sop", """
Do this before building anything. One hour, costs nothing, and it is the
highest-value hour available to you right now.

Pick twenty businesses from one trade in one area. Ring each between six and
eight in the evening. Log: answered, voicemail, full mailbox, dead line.

What you get:
Proof the problem is real, with a number you measured rather than assumed.
A prospect list where you already know who is losing money.
An opening line that is not a cold pitch — "I rang you Tuesday at 6:40 and
nobody picked up, does that happen a lot?"

Almost nobody starting an agency does this. It is most of the edge.

[[Prospect list]] [[SOP — First call]] [[Proof]]
"""),

"SOP — First call": ("sop", """
Open with the observation, not the offer.

"I rang you Tuesday about quarter to seven, nobody picked up. Does that
happen much?"

Then shut up. He will tell you about being on a roof, about his wife taking
messages, about the mobile in the van. Let him.

Three questions, in this order:
What is an average job worth to you?
Roughly how many calls a week do you reckon you miss?
What happens to those people?

The last one is the important one. The answer is almost always "they ring
the next bloke", and he will say it himself. Do not say it for him.

Only then describe the offer, in one sentence. See
[[Offer — Missed call rescue]]. If he asks how it works, keep it boring:
"when a call drops, a text goes out". Detail kills it.

[[ROI maths]] [[Objections]] [[Proof]]
"""),

"Objections": ("concept", """
The four you will actually hear.

"I ring them back when I'm down." — You do, and the good ones are already
booked. The text goes out in sixty seconds; you ring back whenever suits.

"My customers hate automated stuff." — They hate being ignored more. The
text says it is automatic and that a human will follow up. Honest beats
clever.

"That's a lot per month." — What is one job worth? Wait for the number.
Then say nothing.

"My nephew does my website." — Good, this is not a website. It runs whether
or not anyone visits the site.

The one you cannot argue with: "I don't miss calls." Sometimes true. Thank
him, move on, do not try to prove him wrong. He is not the client.

[[SOP — First call]] [[Pricing]]
"""),

"SOP — Build the missed call responder": ("sop", """
Deliberately unglamorous. The value is that it runs, not that it is clever.

Call forwarding on a missed call triggers a webhook. The webhook fires an SMS
from a number the customer will recognise. Replies land in one place the
owner checks — his own phone, a shared inbox, whatever he already uses. Do
not make him learn a new app.

Escalation: anything containing "leak", "no power", "flooding", "emergency"
rings his mobile immediately rather than waiting.

Weekly report: a plain text message on Friday with three numbers. Missed,
recovered, booked.

Build it for the first client by hand. Do not build a platform for a customer
base you do not have yet.

[[Offer — Missed call rescue]] [[SOP — Onboarding]]
"""),

"SOP — Onboarding": ("sop", """
Target: live inside two hours of them saying yes, while they still feel the
thing they felt on the call.

Collect: business number, the number texts should come from, the owner's
mobile, average job value, the three words that mean emergency in their
trade.

Test it in front of them. Ring the business, let it drop, let the text land
on their own phone. That moment is what stops them cancelling in month two.

Set the expectation now: the first fortnight is tuning. You will change the
wording once you see real replies.

[[SOP — Build the missed call responder]] [[Offer — Missed call rescue]]
"""),

"Prospect list": ("note", """
Fill this from [[SOP — After hours call test]]. One line each:

Business · trade · number · rang when · answered or not · notes

Twenty is enough to start. Ten that did not answer is a pipeline.

Mark the ones with a full voicemail box separately. They are the warmest
conversations you will have, because the problem is already embarrassing
to them.

[[SOP — After hours call test]] [[SOP — First call]]
"""),

"Week one": ("project", """
One week, in order. Do not skip to the building — the building is the easy
part and it is not what is missing.

Monday: pick the trade and the area. Write the one sentence from
[[Positioning]] and do not change it again this week.
Tuesday evening: [[SOP — After hours call test]], twenty calls.
Wednesday: build the responder for one imaginary client so the demo is real.
Thursday and Friday: ring the ten that did not answer. Use
[[SOP — First call]] verbatim until it feels natural.
Weekend: whatever you learned that contradicts these notes, change these
notes.

Success for the week is not a client. It is ten real conversations and a
positioning sentence that survived them.

[[Goal]] [[Prospect list]]
"""),

"Goal": ("note", """
First paying client inside thirty days. One trade, one offer, one area.

The trap is building for three months and selling for none. Everything here
is arranged to make selling happen first, because selling is the part that
tells you what to build.

Second goal, only after the first: three clients in the same trade, so the
build is reused rather than rewritten. That is where this stops being a job
and starts being a business.

[[Agency]] [[Week one]]
"""),
}


def main():
    if OUT.exists() and any(OUT.glob("*.md")) and "--force" not in sys.argv:
        sys.exit(f"{OUT} already has notes. Re-run with --force to overwrite.")
    OUT.mkdir(exist_ok=True)
    for title, (kind, body) in NOTES.items():
        text = f"---\ntype: {kind}\nupdated: {TODAY}\n---\n\n# {title}\n{body.rstrip()}\n"
        (OUT / f"{title}.md").write_text(text, encoding="utf-8")
    print(f"  wrote {len(NOTES)} notes to {OUT}")
    print("\n  Point JARVIS at it:")
    print("    echo 'JARVIS_VAULT=./vault-agency' >> .env")
    print("    pkill -f server.py && ./start.sh\n")


if __name__ == "__main__":
    main()
