# HOME: Corrections (Home 6) — the communal store's corrections home.

# NovaMart corrections (human-learned fixes)

The gotchas and quirks the raw data will never tell you on its own. A human hit each of these
the hard way and wrote it down here so the analyst stops walking into the same trap twice. None
of this is in the schema; it is not derivable from the tables. This is the crisp answer to "is
that a correction?" — yes, if it lives here.

**One live version, gated.** Corrections come in by pull request and get reviewed like any other
definition. If two corrections ever disagree, the tie-break is locality and authority first,
recency second — not "whichever was written last wins."

Scope note: these are the human-prose fixes. The *structural* consequences of some of them are
also encoded where the semantic layer enforces them (join cardinality in `semantic/relationships.yaml`,
entity grain caveats in `semantic/entities.yaml`, rejected readings in `semantic/measures.yaml`).
This file is the plain-language record of what a human learned; the semantic layer is where the
machine enforces it. The schema facts themselves (column names, types, catalog) are analyst-side
local, not here.

---

## had_purchase is unreliable for Nov-Dec 2024

Do not trust `sessions.had_purchase` for Nov-Dec 2024. 1,089 sessions have a `purchase_complete`
event AND a completed order but `had_purchase = false` (concentrated around Black Friday). Derive
purchase outcome from `events.event_type = 'purchase_complete'`, or by joining orders on
`session_id`. Never trust `had_purchase` for Q4 2024.

## Fan-out on the orders-to-order_items join

Never sum an order-level column (e.g. `orders.total_amount`) across an `orders -> order_items`
join: many line items per order multiply the rows and inflate the total (proven: 3.15M correct
vs 5.9M fanned, about 1.88x). Aggregate order-level measures at the order grain.

## Device / app_version quirk

`events.app_version IS NULL` ~ web sessions; `2.4.0` / `3.2.0` are the mobile app versions.
`sessions.device` values are `web` / `ios` / `android` (NOT desktop / mobile / tablet). The raw
column will not tell you the web-equals-null mapping; a human profiled it.
