#!/usr/bin/env python3
"""Code lives in the git repo. State/logs live under POLY_DESK (default ~/.grok/desk)."""
from __future__ import annotations
import os
import subprocess
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


def code_rev() -> str:
    """Short SHA, '+' if the worktree is dirty. So HUD proves what is running."""
    try:
        r = subprocess.run(
            ["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        sha = (r.stdout or "").strip() or "?"
        d = subprocess.run(
            ["git", "-C", str(REPO), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if (d.stdout or "").strip():
            return sha + "+"
        return sha
    except Exception:
        return "?"
