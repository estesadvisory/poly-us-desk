#!/usr/bin/env python3
"""Desk v26. Knobs in desk.json. Ring 0 + 10% profit reserve.

Not a dog-band religion. 20–75¢ is so there is a book to exit.
Dumping bids are rejected. LIVE leftover NS is not a buy. LIVE and SOON
both need a bid uptick. Rank prefers a playable 25–70¢ book with an uptick.
Trail arms at +8¢ so a winner can clear taker fees; never sell through entry.
If working is below clip but at least clip_min, buy a smaller ticket.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone

import cfg
import paths

VERSION = "v26"
TWO_WAY_PREFIX = "aec-"
BAN_PREFIX = "atc-"
RESERVE_FILE = paths.DESK / "reserve.json"

RING_USD = 0.0
PROFIT_RESERVE_PCT = 0.10
CLIP_USD = 2.0
CLIP_MIN_USD = 1.0
MAX_USD = 2.0
MAX_OPEN = 20
BBO_PER_LEAGUE = 8
SOON_MIN = 45
OVERDUE_LIVE_MIN = 90
ASK_TRADE = (0.20, 0.75)
MAX_SPREAD_LIVE = 0.04
HARD_STOP = 0.10
FAST_CRASH = 0.08
TRAIL_ARM = 0.08
TRAIL_GIVEBACK = 0.03
IDLE_SCAN_SEC = 10
OPEN_SCAN_SEC = 5
TAPE_STALE_SEC = 90
HOT_MAX_AGE_SEC = 20
FEE_COEF = 0.06
BUY_COOLDOWN_SEC = 15 * 60
MAX_DAY_LOSS = 5.0
BOUNCE_PRIOR_C = -2.0
PLAYABLE = (0.25, 0.70)


def apply_config(data=None) -> dict:
    """Copy desk.json into module globals. Reload after editing the file."""
    global RING_USD, PROFIT_RESERVE_PCT, CLIP_USD, CLIP_MIN_USD, MAX_USD, MAX_OPEN, BBO_PER_LEAGUE
    global SOON_MIN, OVERDUE_LIVE_MIN, ASK_TRADE, MAX_SPREAD_LIVE, HARD_STOP, FAST_CRASH
    global TRAIL_ARM, TRAIL_GIVEBACK, IDLE_SCAN_SEC, OPEN_SCAN_SEC, TAPE_STALE_SEC
    global HOT_MAX_AGE_SEC, FEE_COEF, BUY_COOLDOWN_SEC, MAX_DAY_LOSS, BOUNCE_PRIOR_C, PLAYABLE
    c = data if data is not None else cfg.load()
    RING_USD = float(c.get("ring_usd", RING_USD))
    PROFIT_RESERVE_PCT = float(c.get("profit_reserve_pct", PROFIT_RESERVE_PCT))
    CLIP_USD = float(c.get("clip_usd", CLIP_USD))
    CLIP_MIN_USD = float(c.get("clip_min_usd", CLIP_MIN_USD))
    if CLIP_MIN_USD > CLIP_USD:
        CLIP_MIN_USD = CLIP_USD
    MAX_USD = CLIP_USD
    MAX_OPEN = int(c.get("max_open", MAX_OPEN))
    BBO_PER_LEAGUE = int(c.get("bbo_per_league", BBO_PER_LEAGUE))
    SOON_MIN = float(c.get("soon_min", SOON_MIN))
    OVERDUE_LIVE_MIN = float(c.get("overdue_live_min", OVERDUE_LIVE_MIN))
    ASK_TRADE = (float(c.get("ask_lo", ASK_TRADE[0])), float(c.get("ask_hi", ASK_TRADE[1])))
    MAX_SPREAD_LIVE = float(c.get("max_spread", MAX_SPREAD_LIVE))
    HARD_STOP = float(c.get("hard_stop", HARD_STOP))
    FAST_CRASH = float(c.get("fast_crash", FAST_CRASH))
    TRAIL_ARM = float(c.get("trail_arm", TRAIL_ARM))
    TRAIL_GIVEBACK = float(c.get("trail_giveback", TRAIL_GIVEBACK))
    IDLE_SCAN_SEC = float(c.get("idle_scan_sec", IDLE_SCAN_SEC))
    OPEN_SCAN_SEC = float(c.get("open_scan_sec", OPEN_SCAN_SEC))
    TAPE_STALE_SEC = float(c.get("tape_stale_sec", TAPE_STALE_SEC))
    HOT_MAX_AGE_SEC = float(c.get("hot_max_age_sec", HOT_MAX_AGE_SEC))
    FEE_COEF = float(c.get("fee_coef", FEE_COEF))
    BUY_COOLDOWN_SEC = float(c.get("buy_cooldown_sec", BUY_COOLDOWN_SEC))
    MAX_DAY_LOSS = float(c.get("max_day_loss_usd", MAX_DAY_LOSS))
    BOUNCE_PRIOR_C = float(c.get("bounce_prior_c", BOUNCE_PRIOR_C))
    PLAYABLE = (float(c.get("playable_lo", PLAYABLE[0])), float(c.get("playable_hi", PLAYABLE[1])))
    return c


def ring_from_state(ring_usd, pct, waterline, reserved, equity, bp, clip):
    """Ratchet 10% of profit above waterline. Never shrink. Leave one clip of working."""
    ring_usd = float(ring_usd or 0)
    pct = float(pct or 0)
    waterline = float(waterline)
    reserved = float(reserved or 0)
    equity = float(equity or 0)
    bp = float(bp or 0)
    clip = float(clip or 0)
    profit = max(0.0, equity - waterline)
    reserved = max(reserved, round(profit * pct, 4))
    if bp < clip:
        return 0.0, reserved
    cap = max(0.0, bp - clip)
    return min(ring_usd + reserved, cap), reserved


def _load_reserve() -> dict:
    if not RESERVE_FILE.exists():
        return {}
    try:
        d = json.loads(RESERVE_FILE.read_text())
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _save_reserve(rec: dict) -> None:
    paths.ensure_desk()
    rec = dict(rec)
    rec["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    RESERVE_FILE.write_text(json.dumps(rec) + "\n")


def compute_ring(bp: float, marked: float = 0.0, persist: bool = False) -> tuple[float, dict]:
    """Effective park: ring_usd + ratcheted profit reserve. Overlay/repo knobs already applied."""
    bp = float(bp or 0)
    marked = float(marked or 0)
    equity = bp + marked
    rec = _load_reserve()
    if rec.get("waterline") is None:
        rec["waterline"] = round(equity, 4)
        rec["reserved"] = 0.0
    ring, reserved = ring_from_state(
        RING_USD,
        PROFIT_RESERVE_PCT,
        rec["waterline"],
        rec.get("reserved") or 0,
        equity,
        bp,
        CLIP_USD,
    )
    rec["reserved"] = reserved
    rec["equity"] = round(equity, 4)
    rec["ring"] = round(ring, 4)
    if persist:
        _save_reserve(rec)
    return ring, rec


def reset_reserve() -> bool:
    """Delete the profit-reserve waterline (use after a deposit)."""
    if not RESERVE_FILE.exists():
        return False
    RESERVE_FILE.unlink()
    return True


def ticket_usd(working: float) -> float | None:
    """Full clip when there is room; a smaller ticket down to clip_min otherwise."""
    cash = float(working or 0)
    if cash < CLIP_MIN_USD:
        return None
    return round(min(CLIP_USD, cash), 2)


apply_config()


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
    """Name kept for loop hot-cadence. Means tradable ask band, not 18–42."""
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
