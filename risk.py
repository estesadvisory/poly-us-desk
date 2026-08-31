#!/usr/bin/env python3
"""Desk v24. $7 ring, all US sports, fire without starving, trail winners.

Not a dog-band religion. 20–88¢ is so there is a book to exit.
Dumping bids are rejected. LIVE leftover NS is not a buy. LIVE and SOON
both need a bid uptick — a flat first print was the 08-31 bleed. Rank
prefers a playable 25–70¢ book with an uptick. Trail arms at +8¢ so a
winner can clear taker fees; never sell through entry.
"""
from __future__ import annotations

VERSION = "v24"
RING_USD = 7.0
CLIP_USD = 2.0
MAX_USD = 2.0
# Working cash is the real cap ($2 clips). Do not sit on idle BP.
MAX_OPEN = 20
BBO_PER_LEAGUE = 8
SOON_MIN = 45  # buy the next hour, not only the next 20m
# Posted start passed + API still NS: keep as live this long (CHI-TEN hole).
OVERDUE_LIVE_MIN = 90
# Tradable two-way: sub-20¢ wrecks and locks (>88¢) cannot be micro-reaped.
ASK_TRADE = (0.20, 0.88)
MAX_SPREAD_LIVE = 0.04
HARD_STOP = 0.10  # 3¢ wiggle is hold; a dime hole is a crash
FAST_CRASH = 0.08  # one watch print (MIA 53→13)
TRAIL_ARM = 0.08  # +5¢ was a fee scratch (08-31 54→60)
TRAIL_GIVEBACK = 0.03
IDLE_SCAN_SEC = 10
OPEN_SCAN_SEC = 5
TAPE_STALE_SEC = 90
HOT_MAX_AGE_SEC = 20
TWO_WAY_PREFIX = "aec-"
BAN_PREFIX = "atc-"
FEE_COEF = 0.06
BUY_COOLDOWN_SEC = 15 * 60
MAX_DAY_LOSS = 5.0
BOUNCE_PRIOR_C = -2.0
PLAYABLE = (0.25, 0.70)


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


def league(slug: str) -> str:
    parts = (slug or "").split("-")
    return parts[1] if len(parts) > 2 else ""


def in_dog_band(ask: float) -> bool:
    """Name kept for loop hot-cadence. Means tradable 20–88, not 18–42."""
    lo, hi = ASK_TRADE
    return lo <= float(ask or 0) <= hi


def playable_bonus(ask: float) -> float:
    """25–70¢ movers paid on 08-30. Flat cheap edges did not."""
    lo, hi = PLAYABLE
    return 6.0 if lo <= float(ask or 0) <= hi else 0.0


def is_actionable(row: dict) -> bool:
    """LIVE, overdue NS, or SOON (kickoff within SOON_MIN). LATER is cash-wait."""
    if bool(row.get("live")):
        return True
    if bool(row.get("soon")):
        return True
    return bucket(False, row.get("minutes_to_start")) == "SOON"


def leftover_ns(row: dict) -> bool:
    """Kickoff passed and API still NS — not in-game. Pregame SOON (NS, m>0) can still tick."""
    if (row.get("period") or "").strip() != "NS":
        return False
    try:
        m = float(row.get("minutes_to_start"))
    except (TypeError, ValueError):
        return bool(row.get("live"))
    return m < 0


def unticked(delta) -> bool:
    """No bid uptick. A flat snapshot has no edge after spread + fee."""
    return delta is None or delta <= 0


def why_not(row: dict) -> str | None:
    """Why rank() is None. None means it would buy."""
    slug = row.get("slug") or ""
    if not slug.startswith(TWO_WAY_PREFIX):
        return "not_aec"
    if not is_actionable(row):
        return "later"
    ask = float(row.get("ask") or 0)
    bid = _f(row.get("bid"))
    spr = row.get("spr")
    if spr is None and bid and ask:
        spr = round(ask - bid, 4)
    if not ask or bid is None:
        return "no_bbo"
    if spr is None or spr > MAX_SPREAD_LIVE:
        return "wide"
    if not in_dog_band(ask):
        return "band"
    if leftover_ns(row):
        return "not_started"
    delta = _f(row.get("delta_c"))
    if delta is not None and delta < 0:
        return "dump"
    if unticked(delta):
        return "flat"
    delta2 = _f(row.get("delta2_c"))
    if delta2 is not None and delta2 <= BOUNCE_PRIOR_C and (delta or 0) > 0:
        return "bounce"
    return None


def rank(row: dict) -> float | None:
    """LIVE or ticking SOON aec- with an exit-able book. Reject dumps and bounce-backs."""
    slug = row.get("slug") or ""
    if not slug.startswith(TWO_WAY_PREFIX):
        return None
    if not is_actionable(row):
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
    if leftover_ns(row):
        return None
    delta = _f(row.get("delta_c"))
    if delta is not None and delta < 0:
        return None
    if unticked(delta):
        return None
    delta2 = _f(row.get("delta2_c"))
    if delta2 is not None and delta2 <= BOUNCE_PRIOR_C and (delta or 0) > 0:
        return None
    fee = taker_fee_per_share(ask)
    tick = 0.0 if delta is None else max(delta, 0.0)
    live_bonus = 5.0 if bool(row.get("live")) else 0.0
    return (
        100.0
        - spr * 200.0
        - fee * 800.0
        + min(tick, 3.0) * 3.0
        + playable_bonus(ask)
        + live_bonus
    )


def should_ttr(minutes_to_start) -> bool:
    """Dump only if later and kickoff already passed. A 50m-out soon ticket is not TTR."""
    try:
        return float(minutes_to_start) <= 0
    except (TypeError, ValueError):
        return True


def watch_exit(avg: float, bid: float, peak: float, live: bool, prev_bid=None) -> str | None:
    """Hold a 3¢ wiggle. Cut a −10¢ hole or an −8¢ one-print cliff. Trail +8/−3.

    Never EXIT_UP at or below entry.
    """
    if not (avg and bid):
        return None
    if bid <= avg - HARD_STOP:
        return "EXIT_DOWN"
    try:
        prev = float(prev_bid) if prev_bid is not None else None
    except (TypeError, ValueError):
        prev = None
    if prev is not None and bid <= prev - FAST_CRASH:
        return "EXIT_DOWN"
    if not live:
        return None
    if bid <= avg:
        return None
    if peak >= avg + TRAIL_ARM and bid <= peak - TRAIL_GIVEBACK:
        return "EXIT_UP"
    return None
