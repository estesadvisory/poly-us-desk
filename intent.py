#!/usr/bin/env python3
"""CoS synthesis (no LLM). Reads tape.json + books. Writes intent.json.
  python3 intent.py
"""
from __future__ import annotations
import json, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import risk

DESK = Path.home() / ".grok/desk"
TAPE = DESK / "tape.json"
SKIP = DESK / "skip_slugs.txt"
OUT = DESK / "intent.json"
LAST_CUT = DESK / "last_cut"
SESSION = DESK / "session.json"
TICKET = risk.CLIP_USD
MAX_OPEN = risk.MAX_OPEN


def skips():
    if not SKIP.exists():
        return set()
    return {ln.strip() for ln in SKIP.read_text().splitlines() if ln.strip() and not ln.startswith("#")}


def books():
    r = subprocess.run(["python3", str(DESK / "trade.py"), "books"], capture_output=True, text=True, timeout=30)
    line = (r.stdout or "").strip().splitlines()
    if not line:
        return None
    return json.loads(line[-1])


def tape_age_sec() -> float:
    if not TAPE.exists():
        return 1e9
    try:
        t = json.loads(TAPE.read_text())
        asof = t.get("asof") or ""
        ts = datetime.fromisoformat(asof.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - ts).total_seconds()
    except Exception:
        return 1e9


def refresh_tape():
    age = tape_age_sec()
    args = [str(DESK / "research.py")]
    if age < risk.HOT_MAX_AGE_SEC:
        args.append("--hot")
    subprocess.run(["python3", *args], capture_output=True, text=True, timeout=40)


def pick_buy(tape, ban, open_slugs):
    scored = []
    for r in list(tape.get("live") or []):
        s = r.get("slug") or ""
        if not s or s in ban or s in open_slugs:
            continue
        sc = risk.rank(r)
        if sc is None:
            continue
        scored.append((sc, r))
    scored.sort(key=lambda x: -x[0])
    return scored[0] if scored else None


def cooling() -> bool:
    if not LAST_CUT.exists():
        return False
    try:
        age = time.time() - float(LAST_CUT.read_text().strip())
    except Exception:
        return False
    return age < risk.BUY_COOLDOWN_SEC


def ensure_session(bp: float) -> dict:
    """Sunk morning PnL does not halt a GO. Circuit is from this session's start BP."""
    rec = {}
    if SESSION.exists():
        try:
            rec = json.loads(SESSION.read_text())
        except Exception:
            rec = {}
    if rec.get("start_bp") is None:
        rec = {
            "version": risk.VERSION,
            "start_bp": bp,
            "started": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "max_loss": risk.MAX_DAY_LOSS,
        }
        SESSION.write_text(json.dumps(rec) + "\n")
    return rec


def session_halt(bp: float, opens) -> bool:
    rec = ensure_session(bp)
    start = float(rec.get("start_bp") or bp)
    marked = sum(float(o.get("mark") or o.get("cost") or 0) for o in (opens or []))
    equity = bp + marked
    return (start - equity) >= float(rec.get("max_loss") or risk.MAX_DAY_LOSS)


def dump(out):
    OUT.write_text(json.dumps(out) + "\n")
    print(json.dumps(out))


def main():
    refresh_tape()
    tape = json.loads(TAPE.read_text()) if TAPE.exists() else {}
    b = books()
    if not b:
        dump({"action": "HOLD", "reason": "books failed"})
        return
    opens = b.get("open") or []
    working = float(b.get("working") or 0)
    # Loop never sells. Watch owns stop / trail / LATER.
    if len(opens) >= MAX_OPEN or working < TICKET:
        dump(
            {
                "action": "HOLD",
                "reason": f"open={len(opens)} working={working}",
                "buyingPower": b.get("buyingPower"),
                "working": working,
                "open": [o.get("slug") for o in opens],
            }
        )
        return
    bp = float(b.get("buyingPower") or 0)
    if session_halt(bp, opens):
        dump({"action": "HOLD", "reason": "session loss circuit", "buyingPower": bp, "working": working})
        return
    if cooling():
        dump({"action": "HOLD", "reason": "15m cooldown after losing cut", "working": working})
        return
    pick = pick_buy(tape, skips(), {o["slug"] for o in opens})
    if not pick:
        dump(
            {
                "action": "HOLD",
                "reason": "no live name with momentum outside the fee-trap",
                "working": working,
                "open": [o.get("slug") for o in opens],
                "live_n": len(tape.get("live") or []),
            }
        )
        return
    sc, row = pick
    dump(
        {
            "action": "BUY",
            "slug": row["slug"],
            "usd": TICKET,
            "ask": row.get("ask"),
            "rank": round(sc, 3),
            "live": row.get("live"),
            "soon": row.get("soon"),
            "minutes_to_start": row.get("minutes_to_start"),
            "reason": f"{row.get('title')} ask {row.get('ask')} spr {row.get('spr')} d {row.get('delta_c')} score {sc:.2f}",
            "report": f"CoS BUY {row['slug']} ${TICKET} ask {row.get('ask')} score {sc:.1f}",
        }
    )


if __name__ == "__main__":
    main()
