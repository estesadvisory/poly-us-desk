#!/usr/bin/env python3
"""Venue-agnostic risk. Polymarket US is the first adapter, not the policy.

Desk version v13 (see ~/.grok/desk/VERSION).
Loop buys; watch sells. LIVE dogs 18–42¢ on a +2¢ *bid* tick (v11 fire path).
Last-trade is optional confirmation. No 3-way, no 43–57, no 0–0 Q1.
"""
from __future__ import annotations

VERSION = "v13"
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
MIN_DELTA_DOG = 2.0
BOUNCE_DUMP = -2.0  # prior bid tick this red → bounce, skip
MAX_CHASE_CENTS = 8.0
MIN_OI = 5000.0
MIN_BID_DEPTH = 3
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
    """Ban 0-0 in Q1/1st. Missing score is OK if period is already in play (not Q1/NS)."""
    p = period or ""
    early = any(x in p for x in ("Q1", "1st", "NS", "1H", "Top 1st", "Bot 1st"))
    if not score or not isinstance(score, str) or "-" not in score.replace("–", "-"):
        return not early
    try:
        a, b = score.replace("–", "-").split("-", 1)
        a, b = int(a.strip()), int(b.strip())
    except Exception:
        return not early
    if a == 0 and b == 0 and early:
        return False
    return True


def in_dog_band(ask: float) -> bool:
    lo, hi = ASK_DOG
    return lo <= float(ask or 0) <= hi


def rank(row: dict) -> float | None:
    """None = do not buy. LIVE aec- dog 18–42¢, +2¢ bid tick, not a bounce, book ≤2¢."""
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
    delta = _f(row.get("delta_c"))
    if delta is None:
        delta = _f(row.get("last_delta_c"))
    delta2 = _f(row.get("delta2_c"))
    if delta2 is None:
        delta2 = _f(row.get("last_delta2_c"))
    if delta is None:
        return None
    if delta < MIN_DELTA_DOG:
        return None
    if delta > MAX_CHASE_CENTS:
        return None
    if delta2 is not None and delta2 <= BOUNCE_DUMP:
        return None
    if not in_dog_band(ask):
        return None
    if is_late(row.get("period")) and ask < 0.35 and delta < 4:
        return None
    extra = delta2 if delta2 is not None else 0.0
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
