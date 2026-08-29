#!/usr/bin/env python3
"""Code lives in the git repo. State/logs live under POLY_DESK (default ~/.grok/desk)."""
from __future__ import annotations
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent
DESK = Path(os.environ.get("POLY_DESK", Path.home() / ".grok/desk"))
ENVP = Path(os.environ.get("POLY_ENV", Path.home() / ".grok/secrets/polymarket-us.env"))
LOGS = DESK / "logs"
HOLD = DESK / "HOLD"
EVENTS = LOGS / "events.jsonl"
PAPER = os.environ.get("POLY_PAPER", "").lower() in ("1", "true", "yes")


def ensure_desk() -> Path:
    DESK.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    return DESK
