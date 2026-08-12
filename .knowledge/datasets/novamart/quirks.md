# NovaMart — Dataset Quirks

## sessions.had_purchase is unreliable for Nov–Dec 2024
- 1,089 sessions (923 in 2024-11, 166 in 2024-12) have a `purchase_complete`
  event AND a `completed` order, but `had_purchase = false`.
- Concentrated around the Black Friday week (2024-11-25 onward).
- **Rule:** derive purchase outcomes from `events.event_type = 'purchase_complete'`
  or by joining `orders` on `session_id` — never trust `had_purchase` for Q4 2024.
- Found: 2026-06-09 during checkout-conversion root cause analysis (cross-verification step).

## orders includes cancelled/returned rows
- `orders.status`: completed 40,234 / cancelled 4,596 / returned 2,369.
- `purchase_complete` events match ALL orders (47,199), not just completed.
- Filter `status = 'completed'` for revenue; keep all statuses for funnel conversion.

## events.app_version is NULL for web
- `app_version IS NULL` ≈ web sessions; 2.4.0 / 3.2.0 are the mobile app versions.
