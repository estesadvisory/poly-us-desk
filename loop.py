#!/usr/bin/env python3
"""Idle cadence. Empty tape is patience, not a 90-minute nap.
  python3 loop.py
Desk TUI owns this. Do not run a second copy.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
from pathlib import Path
from subprocess import TimeoutExpired

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lock as desklock
import paths
import risk

DESK = paths.DESK
HUM = paths.REPO / "hum.py"
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


def live_dogs(tape: dict) -> bool:
    for r in tape.get("live") or []:
        ask = float(r.get("ask") or 0)
        if r.get("live") and risk.in_dog_band(ask):
            return True
    return False


def main():
    desklock.claim("loop")
    sess = DESK / "session.json"
    if sess.exists():
        try:
            sess.unlink()
        except Exception:
            pass
    print(json.dumps({"ok": True, "role": "loop", "version": risk.VERSION, "pid": os.getpid()}), flush=True)
    while True:
        out, err = "", ""
        try:
            r = subprocess.run(["python3", str(HUM)], capture_output=True, text=True, timeout=180)
            out = (r.stdout or "").strip()
            err = (r.stderr or "").strip()
        except TimeoutExpired as ex:
            out = (ex.stdout or b"").decode() if isinstance(ex.stdout, bytes) else (ex.stdout or "")
            print(json.dumps({"ok": False, "stage": "hum_timeout"}), flush=True)
        action_line, ledger_line = "", ""
        for ln in (out or "").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            if '"action"' in ln or '"stage"' in ln:
                action_line = ln
            ledger_line = ln
        if action_line:
            print(action_line, flush=True)
        if ledger_line and ledger_line != action_line:
            print(ledger_line, flush=True)
        elif err and not out:
            print(err[-200], flush=True)
        try:
            (DESK / "STATUS.md").write_text(
                f"# desk {risk.VERSION}\n\n"
                f"updated: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
                f"loop_pid: {os.getpid()}\n"
                f"action: {action_line or 'none'}\n"
                f"ledger: {ledger_line or 'none'}\n"
            )
        except Exception:
            pass
        n = opens_from_last(out)
        hot = False
        if TAPE.exists():
            try:
                t = json.loads(TAPE.read_text())
                hot = live_dogs(t) or any(risk.rank(r) is not None for r in (t.get("live") or []))
            except Exception:
                pass
        time.sleep(risk.OPEN_SCAN_SEC if (n or hot) else risk.IDLE_SCAN_SEC)


if __name__ == "__main__":
    main()
