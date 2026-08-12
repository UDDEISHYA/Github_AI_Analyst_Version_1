# NovaMart Schema — BOOTCAMP_DB.NOVAMART (Snowflake)

> Auto-profiled 2026-06-14 · 13 tables · ~8.1M total rows

---

## USERS (50,000 rows)
User registration and demographic attributes.

| Column | Type | Notes |
|--------|------|-------|
| USER_ID | NUMBER | PK |
| SIGNUP_DATE | DATE | |
| SIGNUP_TIMESTAMP | TIMESTAMP_NTZ | |
| ACQUISITION_CHANNEL | VARCHAR | |
| COUNTRY | VARCHAR | |
| DEVICE_PRIMARY | VARCHAR | |
| AGE_BUCKET | VARCHAR | |
| GENDER | VARCHAR | |

---

## SESSIONS (1,383,467 rows)
User browsing sessions with engagement metrics.

| Column | Type | Notes |
|--------|------|-------|
| SESSION_ID | VARCHAR | PK |
| USER_ID | NUMBER | FK → USERS |
| SESSION_START | TIMESTAMP_NTZ | |
| SESSION_END | TIMESTAMP_NTZ | |
| SESSION_DATE | DATE | |
| DEVICE | VARCHAR | |
| LANDING_PAGE | VARCHAR | |
| PAGE_VIEWS | NUMBER | |
| EVENTS_COUNT | NUMBER | |
| HAD_PURCHASE | BOOLEAN | |

---

## EVENTS (6,510,093 rows)
Granular user interaction events (page views, clicks, searches, purchases, etc.).

| Column | Type | Notes |
|--------|------|-------|
| EVENT_ID | NUMBER | PK |
| USER_ID | NUMBER | FK → USERS |
| SESSION_ID | VARCHAR | FK → SESSIONS |
| EVENT_TIMESTAMP | TIMESTAMP_NTZ | |
| EVENT_DATE | DATE | |
| EVENT_TYPE | VARCHAR | Funnel step indicator |
| DEVICE | VARCHAR | |
| PRODUCT_ID | FLOAT | FK → PRODUCTS (nullable) |
| PAGE_URL | VARCHAR | |
| SEARCH_QUERY | VARCHAR | Populated on search events |
| APP_VERSION | VARCHAR | |

---

## ORDERS (47,199 rows)
Completed orders with revenue breakdown.

| Column | Type | Notes |
|--------|------|-------|
| ORDER_ID | NUMBER | PK |
| USER_ID | NUMBER | FK → USERS |
| ORDER_TIMESTAMP | TIMESTAMP_NTZ | |
| ORDER_DATE | DATE | |
| SUBTOTAL | FLOAT | |
| DISCOUNT_AMOUNT | FLOAT | |
| SHIPPING_AMOUNT | FLOAT | |
| TOTAL_AMOUNT | FLOAT | |
| STATUS | VARCHAR | |
| PROMO_ID | FLOAT | FK → PROMOTIONS (nullable) |
| IS_PLUS_MEMBER_ORDER | BOOLEAN | |
| DEVICE | VARCHAR | |
| SESSION_ID | VARCHAR | FK → SESSIONS |

---

## ORDER_ITEMS (75,447 rows)
Line items within each order.

| Column | Type | Notes |
|--------|------|-------|
| ORDER_ITEM_ID | NUMBER | PK |
| ORDER_ID | NUMBER | FK → ORDERS |
| PRODUCT_ID | NUMBER | FK → PRODUCTS |
| QUANTITY | NUMBER | |
| UNIT_PRICE | FLOAT | |
| DISCOUNT_AMOUNT | FLOAT | |
| LINE_TOTAL | FLOAT | |

---

## PRODUCTS (500 rows)
Product catalog with pricing and cost.

| Column | Type | Notes |
|--------|------|-------|
| PRODUCT_ID | NUMBER | PK |
| PRODUCT_NAME | VARCHAR | |
| CATEGORY | VARCHAR | |
| SUBCATEGORY | VARCHAR | |
| PRICE | FLOAT | |
| COST | FLOAT | |
| IS_PLUS_ELIGIBLE | BOOLEAN | |

---

## MEMBERSHIPS (5,513 rows)
NovaMart Plus membership records.

| Column | Type | Notes |
|--------|------|-------|
| MEMBERSHIP_ID | NUMBER | PK |
| USER_ID | NUMBER | FK → USERS |
| PLAN_TYPE | VARCHAR | |
| STARTED_AT | TIMESTAMP_NTZ | |
| ENDED_AT | TIMESTAMP_NTZ | Nullable — NULL if still active |
| STATUS | VARCHAR | |
| CANCEL_REASON | VARCHAR | |
| IS_CURRENT | BOOLEAN | |

---

## PROMOTIONS (5 rows)
Promotional campaigns.

| Column | Type | Notes |
|--------|------|-------|
| PROMO_ID | NUMBER | PK |
| PROMO_NAME | VARCHAR | |
| PROMO_TYPE | VARCHAR | |
| DISCOUNT_PCT | FLOAT | |
| START_DATE | DATE | |
| END_DATE | DATE | |
| TARGET_SEGMENT | VARCHAR | |

---

## EXPERIMENTS (2 rows)
A/B test definitions.

| Column | Type | Notes |
|--------|------|-------|
| EXPERIMENT_ID | NUMBER | PK |
| EXPERIMENT_NAME | VARCHAR | |
| HYPOTHESIS | VARCHAR | |
| PRIMARY_METRIC | VARCHAR | |
| GUARDRAIL_METRICS | VARCHAR | |
| START_DATE | DATE | |
| END_DATE | DATE | |
| STATUS | VARCHAR | |

---

## EXPERIMENT_ASSIGNMENTS (20,000 rows)
User-to-variant assignments for experiments.

| Column | Type | Notes |
|--------|------|-------|
| ASSIGNMENT_ID | NUMBER | PK |
| EXPERIMENT_ID | NUMBER | FK → EXPERIMENTS |
| USER_ID | NUMBER | FK → USERS |
| VARIANT | VARCHAR | |
| ASSIGNED_DATE | DATE | |
| FIRST_EXPOSURE_DATE | DATE | |

---

## NPS_RESPONSES (8,000 rows)
Net Promoter Score survey responses.

| Column | Type | Notes |
|--------|------|-------|
| RESPONSE_ID | NUMBER | PK |
| USER_ID | NUMBER | FK → USERS |
| RESPONSE_DATE | DATE | |
| SCORE | NUMBER | 0–10 NPS scale |
| USER_SEGMENT | VARCHAR | |
| DEVICE | VARCHAR | |
| COMMENT | VARCHAR | |

---

## SUPPORT_TICKETS (21,587 rows)
Customer support interactions.

| Column | Type | Notes |
|--------|------|-------|
| TICKET_ID | NUMBER | PK |
| USER_ID | NUMBER | FK → USERS |
| CREATED_AT | TIMESTAMP_NTZ | |
| CREATED_DATE | DATE | |
| CATEGORY | VARCHAR | |
| SEVERITY | VARCHAR | |
| STATUS | VARCHAR | |
| RESOLVED_AT | TIMESTAMP_NTZ | Nullable |
| DEVICE | VARCHAR | |
| APP_VERSION | VARCHAR | |
| ORDER_ID | FLOAT | FK → ORDERS (nullable) |

---

## CALENDAR (366 rows)
Date dimension table for joins and filtering.

| Column | Type | Notes |
|--------|------|-------|
| DATE | DATE | PK |
| DAY_OF_WEEK | VARCHAR | |
| IS_WEEKEND | BOOLEAN | |
| MONTH | NUMBER | |
| QUARTER | NUMBER | |
| IS_HOLIDAY | BOOLEAN | |
| HOLIDAY_NAME | VARCHAR | |
