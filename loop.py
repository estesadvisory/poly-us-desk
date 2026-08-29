#!/usr/bin/env python3
"""Idle cadence. Empty tape is patience, not a 90-minute nap.
  python3 loop.py
Desk TUI owns this. Do not run a second copy.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lock as desklock
import risk

DESK = Path.home() / ".grok/desk"
HUM = DESK / "hum.py"
TAPE = DESK / "tape.json"


def opens_from_last(text: str) -> int:
    for line in reversed((text or "").splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            o = json.loads(line)
        except Exception:
            continue
        if "open" in o:
            return len(o.get("open") or [])
        if o.get("action") in ("HOLD", "BUY", "CUT"):
            return 1 if o.get("action") != "HOLD" else 0
    return 0


def main():
    desklock.claim("loop")
    print(json.dumps({"ok": True, "role": "loop", "version": risk.VERSION, "pid": os.getpid()}), flush=True)
    while True:
        r = subprocess.run(["python3", str(HUM)], capture_output=True, text=True, timeout=90)
        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()
        if out:
            print(out.splitlines()[-1], flush=True)
        elif err:
            print(err[-200], flush=True)
        n = opens_from_last(out)
        if n <= 0 and TAPE.exists():
            try:
                t = json.loads(TAPE.read_text())
                n = 0 if not (t.get("live") or t.get("soon")) else n
            except Exception:
                pass
        time.sleep(risk.OPEN_SCAN_SEC if n else risk.IDLE_SCAN_SEC)


if __name__ == "__main__":
    main()
