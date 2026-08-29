#!/usr/bin/env python3
"""Venue-agnostic risk. Polymarket US is the first adapter, not the policy.

Desk version v11 (see ~/.grok/desk/VERSION).
Python loop is the only buyer (never sells). Python watch is the only seller.
Dogs 18–42¢ only. No fav band (TCU/Idaho were a fee trap).
"""
from __future__ import annotations

VERSION = "v11"
RING_USD = 10.0
CLIP_USD = 2.0
MAX_USD = 2.0
MAX_OPEN = 2
SOON_MIN = 20  # TTR for leftovers only; we do not buy SOON
ASK_DOG = (0.18, 0.42)
MAX_SPREAD_LIVE = 0.01
HARD_STOP = 0.03
TRAIL_ARM = 0.05
TRAIL_GIVEBACK = 0.03
IDLE_SCAN_SEC = 30
OPEN_SCAN_SEC = 8
TAPE_STALE_SEC = 90
TWO_WAY_PREFIX = "aec-"
BAN_PREFIX = "atc-"
FEE_COEF = 0.06
MIN_DELTA_DOG = 2.0
MIN_DELTA2 = 1.0  # prior tick also up — two prints, not one bounce
MAX_CHASE_CENTS = 8.0  # last 30s already ran; we are late
MIN_OI = 5000.0
MIN_BID_DEPTH = 5
BUY_COOLDOWN_SEC = 900  # after a *losing* cut only
MAX_DAY_LOSS = 2.0
LATE_PERIOD = ("5th", "6th", "7th", "8th", "9th", "Q4", "4Q", "2H")


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


def is_late(period) -> bool:
    p = period or ""
    pu = p.upper()
    return any(m in p for m in LATE_PERIOD) or "Q4" in pu or "4Q" in pu


def rank(row: dict) -> float | None:
    """None = do not buy. LIVE 2-way dogs 18–42¢, two upticks, fat book. Never favs, never SOON, never 3-way."""
    slug = row.get("slug") or ""
    if not slug.startswith(TWO_WAY_PREFIX):
        return None
    if not bool(row.get("live")):
        return None
    ask = float(row.get("ask") or 0)
    spr = row.get("spr")
    if spr is None or spr > MAX_SPREAD_LIVE:
        return None
    oi = _f(row.get("oi"))
    if oi is not None and oi < MIN_OI:
        return None
    depth = _f(row.get("bid_depth"))
    if depth is not None and depth < MIN_BID_DEPTH:
        return None
    delta = _f(row.get("delta_c"))
    delta2 = _f(row.get("delta2_c"))
    if delta is None or delta2 is None:
        return None
    if delta2 < MIN_DELTA2:
        return None
    if delta > MAX_CHASE_CENTS:
        return None
    lo_d, hi_d = ASK_DOG
    if not (lo_d <= ask <= hi_d):
        return None
    if delta < MIN_DELTA_DOG:
        return None
    if is_late(row.get("period")) and ask < 0.35 and delta < 4:
        return None
    return 50.0 + delta + delta2 + (hi_d - ask) * 20.0


def watch_exit(avg: float, bid: float, peak: float, live: bool) -> str | None:
    """Hard stop always. LIVE: trail after +5¢, give back 3¢ from peak. No hard reap."""
    if not (avg and bid):
        return None
    if bid <= avg - HARD_STOP:
        return "EXIT_DOWN"
    if not live:
        return None
    if peak >= avg + TRAIL_ARM and bid <= peak - TRAIL_GIVEBACK:
        return "EXIT_UP"
    return None
