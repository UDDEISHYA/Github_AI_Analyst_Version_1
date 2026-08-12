# NovaMart — Purchase Funnel Definition

## Funnel Steps (fixed order)

| Step | event_type | Description |
|------|-----------|-------------|
| 1 | `page_view` | User views any page |
| 2 | `product_view` | User views a product detail page |
| 3 | `add_to_cart` | User adds an item to cart |
| 4 | `checkout_started` | User begins the checkout flow |
| 5 | `payment_attempted` | User submits a payment method |
| 6 | `purchase_complete` | Order is confirmed and recorded |

## Measurement Method

Each step is measured as `COUNT(DISTINCT user_id)` — the number of unique
users who performed that event at least once in the analysis period. This is
a per-step distinct-user funnel, not a strict per-user sequence. A user who
did `add_to_cart` on Monday and `page_view` on Tuesday counts in both steps
independently.

## Event Filtering

The `events` table contains 10 event types. Only the six listed above belong
in the funnel. Always filter with:

```sql
WHERE event_type IN (
  'page_view', 'product_view', 'add_to_cart',
  'checkout_started', 'payment_attempted', 'purchase_complete'
)
```

The other four (`login`, `app_open`, `search`, `save_for_later`) are not
funnel steps.

## Why payment_attempted Is Included

Leadership confirmed `payment_attempted` belongs between `checkout_started`
and `purchase_complete`. Without it, the drop-off between checkout and
purchase appears as one large gap. With it, we can see that ~8,000 users
start payment but never complete — a distinct leak from users who never
start payment at all.
