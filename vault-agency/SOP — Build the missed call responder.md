---
type: sop
updated: 2026-09-22
---

# SOP — Build the missed call responder

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
