#!/usr/bin/env python3
"""Desk v16. $10 ring, all US sports, fire without starving, trail winners.

Not a dog-band religion. 12–88¢ is so there is a book to exit.
Dumping bids are rejected; a first print (no delta yet) is allowed so new
games still trade. Rank prefers a tight book and a lower taker fee — not the
50¢ coin-flip that ate 2026-08-29.
"""
from __future__ import annotations

VERSION = "v16"
RING_USD = 10.0
CLIP_USD = 2.0
MAX_USD = 2.0
MAX_OPEN = 2
SOON_MIN = 20
# Tradable two-way: dust (<12¢) and locks (>88¢) cannot be micro-reaped.
ASK_TRADE = (0.12, 0.88)
MAX_SPREAD_LIVE = 0.04
HARD_STOP = 0.03
TRAIL_ARM = 0.05
TRAIL_GIVEBACK = 0.03
IDLE_SCAN_SEC = 10
OPEN_SCAN_SEC = 5
TAPE_STALE_SEC = 90
HOT_MAX_AGE_SEC = 20
TWO_WAY_PREFIX = "aec-"
BAN_PREFIX = "atc-"
FEE_COEF = 0.06
BUY_COOLDOWN_SEC = 15 * 60
MAX_DAY_LOSS = 2.0
BOUNCE_PRIOR_C = -2.0


def taker_fee_per_share(p: float) -> float:
    p = min(max(float(p), 0.01), 0.99)
    return FEE_COEF * p * (1.0 - p)


def round_trip_cents(ask: float) -> float:
    return 100.0 * (taker_fee_per_share(ask) + taker_fee_per_share(min(ask + TRAIL_ARM, 0.99)))


def bucket(live: bool, minutes_to_start) -> str:
    if live:
        return "LIVE"
    try:
        m = float(minutes_to_start)
    except (TypeError, ValueError):
        return "LATER"
    if -SOON_MIN <= m <= SOON_MIN:
        return "SOON"
    return "LATER"


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def in_dog_band(ask: float) -> bool:
    """Name kept for loop hot-cadence. Means tradable 12–88, not 18–42."""
    lo, hi = ASK_TRADE
    return lo <= float(ask or 0) <= hi


def rank(row: dict) -> float | None:
    """LIVE aec- with an exit-able book. Reject dumps and bounce-backs."""
    slug = row.get("slug") or ""
    if not slug.startswith(TWO_WAY_PREFIX):
        return None
    if not bool(row.get("live")):
        return None
    ask = float(row.get("ask") or 0)
    bid = _f(row.get("bid"))
    spr = row.get("spr")
    if spr is None and bid and ask:
        spr = round(ask - bid, 4)
    if not ask or bid is None:
        return None
    if spr is None or spr > MAX_SPREAD_LIVE:
        return None
    if not in_dog_band(ask):
        return None
    delta = _f(row.get("delta_c"))
    if delta is not None and delta < 0:
        return None
    delta2 = _f(row.get("delta2_c"))
    if delta2 is not None and delta2 <= BOUNCE_PRIOR_C and (delta or 0) > 0:
        return None
    fee = taker_fee_per_share(ask)
    tick = 0.0 if delta is None else max(delta, 0.0)
    return 100.0 - spr * 200.0 - fee * 800.0 + min(tick, 3.0) * 2.0


def watch_exit(avg: float, bid: float, peak: float, live: bool) -> str | None:
    """Cut losers at −3¢. Trail winners after +5¢; give back 3¢ from peak."""
    if not (avg and bid):
        return None
    if bid <= avg - HARD_STOP:
        return "EXIT_DOWN"
    if not live:
        return None
    if peak >= avg + TRAIL_ARM and bid <= peak - TRAIL_GIVEBACK:
        return "EXIT_UP"
    return None
