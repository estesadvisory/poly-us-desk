#!/usr/bin/env python3
"""One buyer cycle: tape → intent → BUY. Watch is the only seller."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

DESK = Path.home() / ".grok/desk"


def run(args):
    r = subprocess.run(["python3", *args], capture_output=True, text=True, timeout=60)
    out = (r.stdout or "").strip()
    if r.returncode != 0 and not out:
        print(json.dumps({"ok": False, "cmd": args, "err": (r.stderr or "")[-400]}))
        sys.exit(1)
    return out


def main():
    for _ in range(4):
        intent_raw = run([str(DESK / "intent.py")])
        line = intent_raw.splitlines()[-1]
        intent = json.loads(line)
        action = intent.get("action")
        slug = intent.get("slug")
        if action == "CUT":
            print(json.dumps({"ok": False, "stage": "loop_never_sells", "slug": slug}))
            break
        if action == "BUY" and slug:
            usd = str(intent.get("usd") or 2)
            raw = run([str(DESK / "trade.py"), "buy", slug, "--usd", usd])
            print(raw)
            print(intent.get("report") or line)
            try:
                fill = json.loads(raw.splitlines()[-1])
                if not fill.get("ok"):
                    break
            except Exception:
                break
            continue
        print(line)
        break
    print(run([str(DESK / "ledger.py")]))


if __name__ == "__main__":
    main()
