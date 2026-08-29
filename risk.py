#!/usr/bin/env python3
"""Venue-agnostic risk. Polymarket US is the first adapter, not the policy.

Desk version v14 (see ~/.grok/desk/VERSION).
LIVE 18–42¢ aec- that is not dumping this scan. +2¢-in-8s was a starve.
No 3-way, no 43–57, no 0–0 Q1 football. Baseball 1st 0–0 is live.
"""
from __future__ import annotations

VERSION = "v14"
RING_USD = 10.0
CLIP_USD = 2.0
MAX_USD = 2.0
MAX_OPEN = 2
SOON_MIN = 20
ASK_DOG = (0.18, 0.42)
MAX_SPREAD_LIVE = 0.02
HARD_STOP = 0.03
TRAIL_ARM = 0.05
TRAIL_GIVEBACK = 0.03
IDLE_SCAN_SEC = 20
OPEN_SCAN_SEC = 8
TAPE_STALE_SEC = 90
HOT_MAX_AGE_SEC = 25
TWO_WAY_PREFIX = "aec-"
BAN_PREFIX = "atc-"
FEE_COEF = 0.06
MIN_DELTA_DOG = -0.5  # reject dumps; flat or up is enough
MAX_CHASE_CENTS = 8.0
MIN_OI = 3000.0
MIN_BID_DEPTH = 2
BUY_COOLDOWN_SEC = 900
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


def score_ok(score, period) -> bool:
    """Ban 0-0 only in football Q1 / NS / 1H. Baseball Top 1st 0-0 is a live game."""
    p = period or ""
    if not score or not isinstance(score, str) or "-" not in score.replace("–", "-"):
        return not (p in ("NS", "") or p == "Q1")
    try:
        a, b = score.replace("–", "-").split("-", 1)
        a, b = int(a.strip()), int(b.strip())
    except Exception:
        return True
    if a == 0 and b == 0 and ("Q1" in p or p in ("NS", "1H")):
        return False
    return True


def in_dog_band(ask: float) -> bool:
    lo, hi = ASK_DOG
    return lo <= float(ask or 0) <= hi


def rank(row: dict) -> float | None:
    """None = do not buy. LIVE aec- 18–42¢, book ≤2¢, not dumping this scan."""
    slug = row.get("slug") or ""
    if not slug.startswith(TWO_WAY_PREFIX):
        return None
    if not bool(row.get("live")):
        return None
    if not score_ok(row.get("score"), row.get("period")):
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
    if not in_dog_band(ask):
        return None
    delta = _f(row.get("delta_c"))
    if delta is None:
        delta = _f(row.get("last_delta_c"))
    if delta is None:
        delta = 0.0
    if delta < MIN_DELTA_DOG:
        return None
    if delta > MAX_CHASE_CENTS:
        return None
    extra = _f(row.get("delta2_c")) or 0.0
    lo_d, hi_d = ASK_DOG
    return 50.0 + delta + extra + (hi_d - ask) * 20.0


def watch_exit(avg: float, bid: float, peak: float, live: bool) -> str | None:
    """Hard stop always. LIVE: trail after +5¢, give back 3¢ from peak."""
    if not (avg and bid):
        return None
    if bid <= avg - HARD_STOP:
        return "EXIT_DOWN"
    if not live:
        return None
    if peak >= avg + TRAIL_ARM and bid <= peak - TRAIL_GIVEBACK:
        return "EXIT_UP"
    return None
