#!/usr/bin/env python3
"""
Generate sample data for all empty NovaMart practice tables.

Populates the local DuckDB (data/practice/novamart_practice.duckdb) with
realistic, referentially-consistent data for the 7 tables that ship empty:
  sessions, events, order_items, memberships, experiments,
  experiment_assignments, nps_responses

Reads existing users, orders, products, and promotions to build foreign keys.
Uses row counts from the manifest as targets (scaled down by default).

Usage:
    python scripts/generate_all.py              # Default: 10% scale
    python scripts/generate_all.py --scale 1.0  # Full manifest row counts
    python scripts/generate_all.py --scale 0.01 # 1% for quick testing
    python scripts/generate_all.py --seed 123   # Custom seed
    python scripts/generate_all.py --dry-run    # Print plan, don't write
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
import uuid

import numpy as np
import pandas as pd
import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "practice" / "novamart_practice.duckdb"

MANIFEST_ROWS = {
    "sessions": 1_383_467,
    "events": 6_510_093,
    "order_items": 75_447,
    "memberships": 5_513,
    "experiments": 2,
    "experiment_assignments": 20_000,
    "nps_responses": 8_000,
}

DATE_START = datetime(2024, 1, 1)
DATE_END = datetime(2024, 12, 31)
DAYS = (DATE_END - DATE_START).days + 1

EVENT_TYPES = [
    "page_view", "product_view", "add_to_cart",
    "checkout_start", "purchase_complete", "search",
]
LANDING_PAGES = ["/", "/deals", "/category", "/search", "/product", "/account"]
PAGE_URLS = [
    "/home", "/deals", "/category/electronics", "/category/clothing",
    "/category/home", "/category/books", "/product/detail",
    "/cart", "/checkout", "/search", "/account", "/help",
]
SEARCH_QUERIES = [
    "laptop", "shoes", "headphones", "book", "kitchen",
    "gift", "sale", "phone case", "backpack", "vitamins",
    None, None, None, None, None,
]
APP_VERSIONS = [None, None, None, "2.4.0", "3.2.0"]
DEVICES = ["desktop", "mobile", "tablet"]
DEVICE_WEIGHTS = [0.45, 0.40, 0.15]

PLAN_TYPES = ["monthly", "annual"]
CANCEL_REASONS = [
    "too_expensive", "not_using", "found_alternative",
    "missing_features", "poor_experience", None,
]

NPS_SEGMENTS = ["new", "active", "power", "dormant"]
NPS_COMMENTS = [
    "Great experience!", "Could be better", "Love the fast shipping",
    "Too many bugs", "Good value for money", "Customer service was slow",
    "Easy to use", "Needs more products", "Will recommend to friends",
    "Disappointed with quality", None, None, None,
]


def load_existing(conn):
    """Load existing tables needed for foreign key references."""
    users = conn.execute("SELECT USER_ID, SIGNUP_DATE, DEVICE_PRIMARY FROM users").fetchdf()
    orders = conn.execute(
        "SELECT ORDER_ID, USER_ID, ORDER_DATE, ORDER_TIMESTAMP, "
        "TOTAL_AMOUNT, DISCOUNT_AMOUNT, STATUS, DEVICE, SESSION_ID, PROMO_ID "
        "FROM orders"
    ).fetchdf()
    products = conn.execute("SELECT PRODUCT_ID, PRICE, CATEGORY FROM products").fetchdf()
    promotions = conn.execute("SELECT PROMO_ID, DISCOUNT_PCT, START_DATE, END_DATE FROM promotions").fetchdf()
    return users, orders, products, promotions


def target_rows(table, scale):
    """Scale manifest target, but always use exact count for tiny tables."""
    base = MANIFEST_ROWS[table]
    if base <= 100:
        return base
    return max(100, int(base * scale))


def gen_sessions(rng, users, orders, n):
    """Generate sessions with realistic engagement patterns."""
    print(f"  sessions: {n:,} rows ...", end=" ", flush=True)
    user_ids = users["USER_ID"].values
    signup_dates = pd.to_datetime(users["SIGNUP_DATE"]).values

    user_idx = rng.choice(len(user_ids), size=n, p=_user_activity_weights(rng, len(user_ids)))
    chosen_users = user_ids[user_idx]
    chosen_signups = signup_dates[user_idx]

    session_dates = _random_dates_after(rng, chosen_signups, DATE_START, DATE_END, n)
    devices = rng.choice(DEVICES, size=n, p=DEVICE_WEIGHTS)
    page_views = rng.poisson(5, size=n).clip(1, 50)
    events_count = (page_views * rng.uniform(1.0, 2.5, size=n)).astype(int).clip(1, 100)

    hours = rng.choice(24, size=n, p=_hour_weights())
    minutes = rng.integers(0, 60, size=n)
    base_dates = pd.to_datetime(session_dates)
    starts = base_dates + pd.to_timedelta(hours * 3600 + minutes * 60, unit="s")
    durations_min = rng.exponential(10, size=n).clip(1, 120)
    ends = starts + pd.to_timedelta(durations_min, unit="m")

    session_ids = [f"s-{uuid.uuid4().hex[:12]}" for _ in range(n)]

    had_purchase = np.zeros(n, dtype=bool)
    purchase_rate = 47199 / 1_383_467
    had_purchase = rng.random(n) < purchase_rate

    # Quirk: ~1089 Nov-Dec sessions should have had_purchase=False despite purchase
    session_months = base_dates.month
    nov_dec_mask = np.isin(session_months, [11, 12])
    quirk_candidates = np.where(nov_dec_mask & had_purchase)[0]
    if len(quirk_candidates) > 0:
        n_quirk = min(int(1089 * (n / 1_383_467)), len(quirk_candidates))
        if n_quirk > 0:
            quirk_idx = rng.choice(quirk_candidates, size=n_quirk, replace=False)
            had_purchase[quirk_idx] = False

    df = pd.DataFrame({
        "SESSION_ID": session_ids,
        "USER_ID": chosen_users,
        "SESSION_START": starts,
        "SESSION_END": ends,
        "SESSION_DATE": base_dates.date,
        "DEVICE": devices,
        "LANDING_PAGE": rng.choice(LANDING_PAGES, size=n),
        "PAGE_VIEWS": page_views,
        "EVENTS_COUNT": events_count,
        "HAD_PURCHASE": had_purchase,
    })
    print("done")
    return df


def gen_events(rng, sessions_df, products, n):
    """Generate granular events tied to sessions."""
    print(f"  events: {n:,} rows ...", end=" ", flush=True)

    sess_ids = sessions_df["SESSION_ID"].values
    sess_starts = pd.to_datetime(sessions_df["SESSION_START"]).values
    sess_devices = sessions_df["DEVICE"].values
    sess_users = sessions_df["USER_ID"].values
    sess_dates = pd.to_datetime(sessions_df["SESSION_DATE"]).values
    product_ids = products["PRODUCT_ID"].values

    event_type_weights = [0.35, 0.25, 0.15, 0.10, 0.05, 0.10]
    sess_idx = rng.choice(len(sess_ids), size=n, replace=True)

    event_types = rng.choice(EVENT_TYPES, size=n, p=event_type_weights)
    devices = sess_devices[sess_idx]
    user_ids = sess_users[sess_idx]

    offsets_sec = rng.exponential(120, size=n).clip(0, 3600)
    base_ts = pd.to_datetime(sess_starts[sess_idx])
    timestamps = base_ts + pd.to_timedelta(offsets_sec, unit="s")

    prod_mask = np.isin(event_types, ["product_view", "add_to_cart", "purchase_complete"])
    prod_ids = np.full(n, np.nan)
    prod_ids[prod_mask] = rng.choice(product_ids, size=prod_mask.sum())

    search_mask = event_types == "search"
    search_qs = np.full(n, None, dtype=object)
    search_qs[search_mask] = rng.choice(
        [q for q in SEARCH_QUERIES if q is not None], size=search_mask.sum()
    )

    app_versions = np.array([
        rng.choice(["2.4.0", "3.2.0"]) if d == "mobile" else None
        for d in devices
    ], dtype=object)

    page_urls = rng.choice(PAGE_URLS, size=n)

    df = pd.DataFrame({
        "EVENT_ID": np.arange(1, n + 1),
        "USER_ID": user_ids,
        "SESSION_ID": sess_ids[sess_idx],
        "EVENT_TIMESTAMP": timestamps,
        "EVENT_DATE": pd.to_datetime(sess_dates[sess_idx]).date,
        "EVENT_TYPE": event_types,
        "DEVICE": devices,
        "PRODUCT_ID": prod_ids,
        "PAGE_URL": page_urls,
        "SEARCH_QUERY": search_qs,
        "APP_VERSION": app_versions,
    })
    print("done")
    return df


def gen_order_items(rng, orders, products, n_target):
    """Generate order line items. Each order gets 1-5 items."""
    print(f"  order_items: ~{n_target:,} target rows ...", end=" ", flush=True)
    order_ids = orders["ORDER_ID"].values
    product_ids = products["PRODUCT_ID"].values
    prices = dict(zip(products["PRODUCT_ID"], products["PRICE"]))

    items_per_order = rng.choice([1, 1, 1, 2, 2, 3], size=len(order_ids))
    avg_ratio = n_target / len(order_ids)
    items_per_order = rng.poisson(avg_ratio, size=len(order_ids)).clip(1, 5)

    rows = []
    item_id = 1
    for oid, n_items in zip(order_ids, items_per_order):
        chosen_prods = rng.choice(product_ids, size=n_items, replace=False)
        for pid in chosen_prods:
            qty = int(rng.choice([1, 1, 1, 2, 2, 3]))
            unit_price = prices.get(pid, 25.0)
            discount = round(float(rng.choice([0, 0, 0, 0, unit_price * 0.1, unit_price * 0.15])), 2)
            line_total = round(qty * unit_price - discount, 2)
            rows.append({
                "ORDER_ITEM_ID": item_id,
                "ORDER_ID": oid,
                "PRODUCT_ID": pid,
                "QUANTITY": qty,
                "UNIT_PRICE": unit_price,
                "DISCOUNT_AMOUNT": discount,
                "LINE_TOTAL": max(line_total, 0),
            })
            item_id += 1

    df = pd.DataFrame(rows)
    print(f"done ({len(df):,} actual)")
    return df


def gen_memberships(rng, users, n):
    """Generate NovaMart Plus membership records."""
    print(f"  memberships: {n:,} rows ...", end=" ", flush=True)
    user_ids = users["USER_ID"].values
    chosen = rng.choice(user_ids, size=n, replace=False) if n <= len(user_ids) else rng.choice(user_ids, size=n)

    started = _random_timestamps(rng, DATE_START, DATE_END, n)

    statuses = rng.choice(["active", "cancelled", "expired"], size=n, p=[0.55, 0.30, 0.15])
    plan_types = rng.choice(PLAN_TYPES, size=n, p=[0.6, 0.4])

    ended = []
    cancel_reasons = []
    is_current = []
    for i in range(n):
        if statuses[i] == "active":
            ended.append(None)
            cancel_reasons.append(None)
            is_current.append(True)
        else:
            days_active = int(rng.exponential(120)) + 7
            end_dt = started[i] + timedelta(days=days_active)
            if end_dt > DATE_END:
                end_dt = DATE_END
            ended.append(end_dt)
            cancel_reasons.append(rng.choice([r for r in CANCEL_REASONS if r is not None]))
            is_current.append(False)

    df = pd.DataFrame({
        "MEMBERSHIP_ID": np.arange(1, n + 1),
        "USER_ID": chosen,
        "PLAN_TYPE": plan_types,
        "STARTED_AT": started,
        "ENDED_AT": ended,
        "STATUS": statuses,
        "CANCEL_REASON": cancel_reasons,
        "IS_CURRENT": is_current,
    })
    print("done")
    return df


def gen_experiments(rng):
    """Generate the 2 experiment definitions."""
    print("  experiments: 2 rows ...", end=" ", flush=True)
    df = pd.DataFrame([
        {
            "EXPERIMENT_ID": 1,
            "EXPERIMENT_NAME": "checkout_redesign_v2",
            "HYPOTHESIS": "Simplified checkout flow increases purchase completion rate",
            "PRIMARY_METRIC": "purchase_completion_rate",
            "GUARDRAIL_METRICS": "cart_abandonment_rate,avg_order_value",
            "START_DATE": datetime(2024, 9, 1).date(),
            "END_DATE": datetime(2024, 10, 15).date(),
            "STATUS": "completed",
        },
        {
            "EXPERIMENT_ID": 2,
            "EXPERIMENT_NAME": "search_ranking_ml_v1",
            "HYPOTHESIS": "ML-based search ranking increases search-to-purchase conversion",
            "PRIMARY_METRIC": "search_conversion_rate",
            "GUARDRAIL_METRICS": "pages_per_session,bounce_rate",
            "START_DATE": datetime(2024, 10, 20).date(),
            "END_DATE": datetime(2024, 12, 15).date(),
            "STATUS": "completed",
        },
    ])
    print("done")
    return df


def gen_experiment_assignments(rng, users, n):
    """Generate experiment assignments with 50/50 split."""
    print(f"  experiment_assignments: {n:,} rows ...", end=" ", flush=True)
    user_ids = users["USER_ID"].values

    n_exp1 = n // 2
    n_exp2 = n - n_exp1

    exp1_users = rng.choice(user_ids, size=n_exp1, replace=False)
    exp1_variants = rng.choice(["control", "treatment"], size=n_exp1)
    exp1_dates = _random_date_range(rng, datetime(2024, 9, 1), datetime(2024, 10, 15), n_exp1)

    exp2_users = rng.choice(user_ids, size=n_exp2, replace=False)
    exp2_variants = rng.choice(["control", "treatment"], size=n_exp2)
    exp2_dates = _random_date_range(rng, datetime(2024, 10, 20), datetime(2024, 12, 15), n_exp2)

    exposure_offset_1 = [d + timedelta(days=int(rng.integers(0, 4))) for d in exp1_dates]
    exposure_offset_2 = [d + timedelta(days=int(rng.integers(0, 4))) for d in exp2_dates]

    df = pd.DataFrame({
        "ASSIGNMENT_ID": np.arange(1, n + 1),
        "EXPERIMENT_ID": [1] * n_exp1 + [2] * n_exp2,
        "USER_ID": np.concatenate([exp1_users, exp2_users]),
        "VARIANT": np.concatenate([exp1_variants, exp2_variants]),
        "ASSIGNED_DATE": [d.date() for d in exp1_dates] + [d.date() for d in exp2_dates],
        "FIRST_EXPOSURE_DATE": [d.date() for d in exposure_offset_1 + exposure_offset_2],
    })
    print("done")
    return df


def gen_nps_responses(rng, users, n):
    """Generate NPS survey responses with realistic score distribution."""
    print(f"  nps_responses: {n:,} rows ...", end=" ", flush=True)
    user_ids = rng.choice(users["USER_ID"].values, size=n, replace=True)
    dates = _random_date_range(rng, DATE_START, DATE_END, n)
    # Bimodal NPS: promoters (9-10) and detractors (0-6) with fewer passives (7-8)
    scores = rng.choice(
        range(11), size=n,
        p=[0.03, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.10, 0.12, 0.22, 0.26],
    )
    segments = rng.choice(NPS_SEGMENTS, size=n, p=[0.25, 0.40, 0.20, 0.15])
    devices = rng.choice(DEVICES, size=n, p=DEVICE_WEIGHTS)
    comments = rng.choice(NPS_COMMENTS, size=n)

    df = pd.DataFrame({
        "RESPONSE_ID": np.arange(1, n + 1),
        "USER_ID": user_ids,
        "RESPONSE_DATE": [d.date() for d in dates],
        "SCORE": scores,
        "USER_SEGMENT": segments,
        "DEVICE": devices,
        "COMMENT": comments,
    })
    print("done")
    return df


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user_activity_weights(rng, n):
    """Power-law activity: some users are much more active."""
    w = rng.pareto(1.5, size=n)
    return w / w.sum()


def _hour_weights():
    """Realistic hourly traffic pattern (peak afternoon, low overnight)."""
    hours = np.array([
        1, 1, 1, 1, 1, 2, 3, 5, 7, 8, 9, 9,
        10, 10, 9, 8, 7, 6, 5, 4, 3, 2, 2, 1,
    ], dtype=float)
    return hours / hours.sum()


def _random_dates_after(rng, signup_dates, start, end, n):
    """Random dates between max(signup, start) and end."""
    start_ts = np.datetime64(start)
    end_ts = np.datetime64(end)
    clipped_starts = np.maximum(signup_dates, start_ts)
    ranges = (end_ts - clipped_starts).astype("timedelta64[D]").astype(int)
    ranges = np.clip(ranges, 1, None)
    offsets = (rng.random(n) * ranges).astype(int)
    return clipped_starts + offsets.astype("timedelta64[D]")


def _random_timestamps(rng, start, end, n):
    """Random timestamps uniformly distributed between start and end."""
    span = (end - start).total_seconds()
    offsets = rng.random(n) * span
    return [start + timedelta(seconds=float(o)) for o in offsets]


def _random_date_range(rng, start, end, n):
    """Random datetimes within a date range."""
    span = (end - start).total_seconds()
    offsets = rng.random(n) * span
    return [start + timedelta(seconds=float(o)) for o in offsets]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate NovaMart practice data")
    parser.add_argument("--scale", type=float, default=0.1,
                        help="Fraction of manifest row counts (default: 0.1 = 10%%)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--dry-run", action="store_true", help="Print plan only")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite tables that already have data")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    print(f"NovaMart Practice Data Generator")
    print(f"  DB: {DB_PATH}")
    print(f"  Scale: {args.scale:.0%} of manifest targets")
    print(f"  Seed: {args.seed}")
    print()

    conn = duckdb.connect(str(DB_PATH))
    users, orders, products, promotions = load_existing(conn)
    print(f"Existing data: {len(users):,} users, {len(orders):,} orders, "
          f"{len(products):,} products, {len(promotions):,} promotions")
    print()

    plan = {}
    for table in MANIFEST_ROWS:
        current = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        target = target_rows(table, args.scale)
        skip = current > 0 and not args.force
        plan[table] = {"current": current, "target": target, "skip": skip}
        status = "SKIP (has data)" if skip else f"GENERATE {target:,}"
        if current > 0 and args.force:
            status = f"REPLACE → {target:,}"
        print(f"  {table:30s} current={current:>10,}   → {status}")

    if args.dry_run:
        print("\n--dry-run: exiting without writing.")
        return

    tables_to_gen = {t: p for t, p in plan.items() if not p["skip"]}
    if not tables_to_gen:
        print("\nAll tables already have data. Use --force to regenerate.")
        return

    print(f"\nGenerating {len(tables_to_gen)} tables ...")

    generated = {}

    if "experiments" in tables_to_gen:
        generated["experiments"] = gen_experiments(rng)

    if "memberships" in tables_to_gen:
        generated["memberships"] = gen_memberships(rng, users, plan["memberships"]["target"])

    if "nps_responses" in tables_to_gen:
        generated["nps_responses"] = gen_nps_responses(rng, users, plan["nps_responses"]["target"])

    if "experiment_assignments" in tables_to_gen:
        generated["experiment_assignments"] = gen_experiment_assignments(
            rng, users, plan["experiment_assignments"]["target"]
        )

    sessions_df = None
    if "sessions" in tables_to_gen:
        sessions_df = gen_sessions(rng, users, orders, plan["sessions"]["target"])
        generated["sessions"] = sessions_df

    if "events" in tables_to_gen:
        if sessions_df is None:
            sessions_df = conn.execute("SELECT * FROM sessions").fetchdf()
        generated["events"] = gen_events(
            rng, sessions_df, products, plan["events"]["target"]
        )

    if "order_items" in tables_to_gen:
        generated["order_items"] = gen_order_items(
            rng, orders, products, plan["order_items"]["target"]
        )

    print(f"\nWriting to DuckDB ...")
    for table, df in generated.items():
        if plan[table].get("skip"):
            continue
        if plan[table]["current"] > 0 and args.force:
            conn.execute(f"DELETE FROM {table}")
        conn.execute(f"INSERT INTO {table} SELECT * FROM df")
        final_count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {final_count:,} rows written")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
