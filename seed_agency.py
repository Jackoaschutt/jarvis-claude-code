"""
Seed the vault for a dealership lost-lead recovery agency.

    python3 seed_agency.py --force

Writes vault-agency/. Nothing outside that folder is touched.

These notes include the kill test — the objections that nearly sank the idea
and what has to be true for it to survive. Keep them. A vault holding only the
optimistic case makes JARVIS a yes-man, and you already have enough of those.

Every figure here is a placeholder until you replace it with one you measured.
"""
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "vault-agency"
TODAY = "2026-09-22"

NOTES = {
"Agency": ("project", """
One operator, one offer, one industry: recovering dealership sales leads that
were paid for, abandoned, and never contacted again.

The edge is not the idea. It is that I sold cars on a dealership floor and know
what actually happens to a lead after the second unanswered call. AI vendors
selling into dealerships almost never have that.

Stage: no clients, idea survived a kill test with conditions. Before anything
else, [[Risk — Compliance]] has to be answered, because it is the one that can
end this.

[[Positioning]] [[Offer — Lost lead recovery]] [[Kill test]] [[Week one]]
"""),

"Positioning": ("concept", """
The sentence.

"I don't answer your phones. I chase the people you already stopped chasing."

It works because it is the opposite of what every other AI vendor walks in
with. They all sell inbound — catching what comes in. This is outbound against
data the dealership already owns and already paid for.

Say it to a sales manager and he knows immediately what you mean, because he
knows what his CRM looks like.

[[Offer — Lost lead recovery]] [[Competitors]]
"""),

"Offer — Lost lead recovery": ("proposal", """
Two versions. The second is the business.

The clean-out: a one-off pass over every lead in the CRM marked lost. Big
number, good demo, and then the database is burned. This is a project, not a
business — see [[Kill test]].

The recurring one: every lead the floor marks lost gets worked again at
thirty, sixty and ninety days. Smaller volume, arrives every month, consent is
fresher, and it does not compete with the salespeople for anything live.

Lead with the clean-out to prove it. Sell the recurring one.

[[Pricing]] [[Risk — Salespeople]] [[SOP — Sales manager conversation]]
"""),

"ICP — Dealership sales departments": ("concept", """
Sales, not service. Service is a different department with a different language
and I have not worked in it.

Independents and single-site franchise dealers first. Groups have a head office
that will slow everything to a crawl and ask for a security review.

Who signs: the sales manager if the number is small enough. Above roughly a
thousand a month, or the moment customer data leaves the building, the dealer
principal gets involved. Assume he will.

[[SOP — Sales manager conversation]] [[Risk — Compliance]]
"""),

"Kill test": ("concept", """
What nearly killed this, honestly recorded.

Survives, with conditions. The three that must be answered:

One. Consent. Ringing or texting people who enquired eight months ago may not
be legal. See [[Risk — Compliance]]. This is the one that ends it if ignored.

Two. Performance-only pricing is a trap. It sounds like it removes the
dealer's risk, and it does — by moving all of it onto the person with no money.
See [[Risk — Performance pricing]].

Three. It is a project, not a subscription, unless it becomes the recurring
version in [[Offer — Lost lead recovery]]. Burn the database once and the
revenue stops.

Also true and worth knowing: this is not virgin territory. See
[[Competitors]].

What genuinely survived: dealers do buy AI, the products they are buying are
shallow, dead leads really are neglected at individual dealers, and I have
floor experience that vendors do not.

[[Risk — Compliance]] [[Risk — Performance pricing]] [[Risk — Salespeople]]
"""),

"Risk — Compliance": ("concept", """
The one that can actually end this. Answer it before spending a dollar.

Contacting a database of people who enquired months ago runs into do-not-call
and spam rules. In the US the TCPA carries statutory damages per message, and
automated calls to mobiles without consent are catastrophic rather than
expensive. Elsewhere the equivalents have real teeth.

Questions that need real answers, not assumptions:
Does the original enquiry consent still cover contact this much later?
Who is legally the sender — the dealership or me?
Is the list scrubbed against the do-not-call register, and by whom?
What does the dealer's own privacy policy promise these people?

Cheapest resolution: contact goes out under the dealership's name and number,
from their system, with them as sender. I operate it. That keeps consent where
it was given. Verify this with someone qualified rather than with a model.

The recurring thirty-sixty-ninety version in [[Offer — Lost lead recovery]] is
safer on every one of these points, because the enquiry is recent.

[[Kill test]] [[Offer — Lost lead recovery]]
"""),

"Risk — Performance pricing": ("concept", """
Pay per appointment sounds like the way to land a first client without a track
record. It is also how you work three weeks for nothing.

What goes wrong: cash flow dies while you wait on results. Attribution gets
argued — "he was coming in anyway", "that's a house lead", "he didn't show".
Shows are disputable and the dealer is the one counting. You have no leverage
to enforce any of it.

Better structure: a small fixed fee that covers the work, plus a bonus on
results. The fixed part proves he is serious and keeps the lights on. The bonus
gives him the upside story he needs to say yes.

Never pure performance. Not for the first client, and especially not for the
first client.

[[Pricing]] [[Kill test]]
"""),

"Risk — Salespeople": ("concept", """
The structural problem nobody mentions.

Appointments get handed to the floor, and the floor is on commission. They do
not want an outsider's leads competing with their own, they will claim the good
ones as house customers, and they will not work the rest properly.

Results then depend entirely on people with an incentive to make it fail or to
take credit when it works.

Mitigations worth testing: book into a specific slot rather than handing leads
out. Report to the sales manager, not the salespeople. Agree attribution rules
in writing before the first call goes out, while everyone is still friendly.

Having been one of those salespeople is the advantage here. I know exactly how
this gets quietly sabotaged.

[[Offer — Lost lead recovery]] [[SOP — Sales manager conversation]]
"""),

"Competitors": ("note", """
Honest correction to my own optimism: database mining in automotive is an
established category, not an empty field. Equity mining products and outsourced
call centres both already sell into dealerships.

What is still open: those are sold to groups, priced for groups, and run by
people who have never stood on a sales floor. The single-site dealer who cannot
justify enterprise software is genuinely unserved.

Do the homework before the first pitch. Walking in claiming nobody does this,
to a manager who has already been pitched by someone who does, ends the meeting.

[[Positioning]] [[Kill test]]
"""),

"Pricing": ("concept", """
Fixed fee plus a bonus. Never pure performance — see
[[Risk — Performance pricing]].

Opening position: a small fixed monthly that covers the work, plus a bonus per
appointment that shows. Discount the fixed part to land the first one if you
must. Do not drop it to zero.

Anchor against gross on one car. If front-end gross on a used unit is a few
thousand, one recovered sale covers months. That is the whole argument and the
manager can do the arithmetic himself.

[[Risk — Performance pricing]] [[Offer — Lost lead recovery]]
"""),

"Proof": ("concept", """
Two questions. Do not pitch before asking them.

"How many leads in your CRM are sitting marked lost?"
"When did anyone last ring one?"

He knows the answer to the second one is never. Let him say it. The silence
after is the pitch.

If he does not know the first number, better again — ask him to pull it while
you are sitting there.

[[SOP — Sales manager conversation]]
"""),

"SOP — Sales manager conversation": ("sop", """
Open as someone who has done the job, not as a vendor.

"I sold cars for a while. Every lead I didn't get hold of in two calls I never
rang again, because there was always a fresh one. Is it still like that here?"

He will agree, because it is universally true and nobody says it out loud.

Then [[Proof]] — the two questions. Then one sentence on the offer and nothing
more. Detail kills it.

Do not say AI unless he says it first. He has been pitched AI. He has possibly
already bought some that underdelivered — that is the opening, not a problem.
Ask what they tried and what happened.

[[Proof]] [[Offer — Lost lead recovery]] [[Objections]]
"""),

"Objections": ("concept", """
"We already tried an AI phone thing." — Good, what happened? It probably
answered calls and chased nobody. That gap is the offer.

"Those leads are dead." — Some are. They cost you nothing now either way, and
the ones who bought elsewhere tell us that in one message.

"My guys already follow up." — For how long? Two calls, then a fresh lead comes
in. No criticism, it is how commission works.

"I'd need to ask the dealer principal." — Expected. See
[[ICP — Dealership sales departments]]. Offer to put it in writing for him
rather than trying to close around it.

"Can't hand over customer data." — Fair, and the answer is that it goes out
under the dealership's name from the dealership's system. See
[[Risk — Compliance]].

[[SOP — Sales manager conversation]]
"""),

"Week one": ("project", """
New job starts this week. This fits around it, not instead of it.

Before anything is built:
Answer [[Risk — Compliance]]. One conversation with someone qualified. Nothing
else matters until this is settled.
Do the homework in [[Competitors]] so the first pitch is not embarrassed.
Write the two questions from [[Proof]] somewhere they can be said without
reading them.

Then, and only then: one conversation with one sales manager at a dealership
that is not a competitor to the new job. Not a pitch. Ask the two questions and
listen.

Success this week is one honest conversation and a compliance answer. Not a
client.

[[Goal]] [[Risk — Compliance]]
"""),

"Goal": ("note", """
First paying dealer inside ninety days, working around a full-time job.

Ninety, not thirty. The thirty-day version was written for a sole trader who
answers his own phone. Dealerships have a dealer principal, a compliance
question and a slower cycle. Pretending otherwise leads to quitting in week
three when nothing has closed.

The real goal for the first month is narrower: know whether the compliance
answer kills it. Everything else is downstream of that.

[[Agency]] [[Week one]] [[Risk — Compliance]]
"""),
}


def main():
    if OUT.exists() and any(OUT.glob("*.md")):
        if "--force" not in sys.argv:
            sys.exit(f"{OUT} already has notes. Re-run with --force to replace them.")
        shutil.rmtree(OUT)
    OUT.mkdir(exist_ok=True)
    for title, (kind, body) in NOTES.items():
        text = f"---\ntype: {kind}\nupdated: {TODAY}\n---\n\n# {title}\n{body.rstrip()}\n"
        (OUT / f"{title}.md").write_text(text, encoding="utf-8")
    print(f"  wrote {len(NOTES)} notes to {OUT}")
    print("\n  Point JARVIS at it (once):")
    print("    echo 'JARVIS_VAULT=./vault-agency' >> .env")
    print("  Then restart:")
    print("    pkill -f server.py; ./start.sh\n")


if __name__ == "__main__":
    main()
