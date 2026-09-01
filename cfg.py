#!/usr/bin/env python3
"""Load desk.json knobs. Repo file, then optional ~/.grok/desk/desk.json overlay."""
from __future__ import annotations
import json
from pathlib import Path

import paths

KEYS = (
    "ring_usd",
    "profit_reserve_pct",
    "clip_usd",
    "max_open",
    "bbo_per_league",
    "soon_min",
    "overdue_live_min",
    "ask_lo",
    "ask_hi",
    "max_spread",
    "hard_stop",
    "fast_crash",
    "trail_arm",
    "trail_giveback",
    "idle_scan_sec",
    "open_scan_sec",
    "tape_stale_sec",
    "hot_max_age_sec",
    "fee_coef",
    "buy_cooldown_sec",
    "max_day_loss_usd",
    "bounce_prior_c",
    "playable_lo",
    "playable_hi",
)

REPO_FILE = paths.REPO / "desk.json"
OVERLAY_FILE = paths.DESK / "desk.json"


def _read(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text())
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    return {k: raw[k] for k in KEYS if k in raw}


def load() -> dict:
    data = _read(REPO_FILE)
    data.update(_read(OVERLAY_FILE))
    return data
