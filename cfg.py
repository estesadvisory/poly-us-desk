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
    "clip_min_usd",
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

INT_KEYS = frozenset({"max_open", "bbo_per_league"})

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


def coerce(key: str, raw: str):
    """Parse a typed knob from the desk `set` command."""
    if key not in KEYS:
        raise KeyError(key)
    text = str(raw).strip()
    if key in INT_KEYS:
        return int(float(text))
    return float(text)


def set_overlay(key: str, raw: str, dest: Path | None = None) -> tuple[object, Path]:
    """Write one knob to the overlay file (not git). Returns (value, path)."""
    val = coerce(key, raw)
    path = dest or OVERLAY_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _read(path)
    data[key] = val
    path.write_text(json.dumps(data, indent=2) + "\n")
    return val, path
