#!/usr/bin/env python3
"""CoS synthesis (no LLM). Reads tape.json + books. Writes intent.json.
  python3 intent.py
"""
from __future__ import annotations
import json, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths
import risk

DESK = paths.DESK
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
    r = subprocess.run(["python3", str(paths.REPO / "trade.py"), "books"], capture_output=True, text=True, timeout=30)
    line = (r.stdout or "").strip().splitlines()
    if not line:
        return None
    data = json.loads(line[-1])
    if data.get("ok") is False or data.get("buyingPower") is None:
        return None
    return data


def tape_full_age_sec() -> float:
    if not TAPE.exists():
        return 1e9
    try:
        t = json.loads(TAPE.read_text())
        asof = t.get("full_asof") or t.get("asof") or ""
        ts = datetime.fromisoformat(asof.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - ts).total_seconds()
    except Exception:
        return 1e9


def refresh_tape():
    """Research child owns the tape. Do not --hot here — that collapsed the universe to CS2."""
    if tape_full_age_sec() <= risk.TAPE_STALE_SEC:
        return
    subprocess.run(["python3", str(paths.REPO / "research.py")], capture_output=True, text=True, timeout=60)


def pick_buy(tape, ban, open_slugs):
    scored = []
    rows = list(tape.get("live") or []) + list(tape.get("soon") or [])
    for r in rows:
        s = r.get("slug") or ""
        if not s or s in ban or s in open_slugs:
            continue
        sc = risk.rank(r)
        if sc is None:
            continue
        scored.append((sc, r))
    scored.sort(key=lambda x: -x[0])
    return scored[0] if scored else None


def cooling_slugs() -> set:
    """Per-slug 15m after a losing cut. Never freeze the whole desk (max 2 concurrent)."""
    if not LAST_CUT.exists():
        return set()
    raw = LAST_CUT.read_text().strip()
    now = time.time()
    out = set()
    try:
        d = json.loads(raw)
        if isinstance(d, dict):
            for s, ts in d.items():
                try:
                    if now - float(ts) < risk.BUY_COOLDOWN_SEC:
                        out.add(s)
                except (TypeError, ValueError):
                    continue
            return out
    except Exception:
        pass
    try:
        if now - float(raw) < risk.BUY_COOLDOWN_SEC:
            return {"*legacy*"}
    except Exception:
        return set()
    return set()


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
    gap = start - equity
    # In-flight fill: BP already down ~$2, position not in books yet. Not a day loss.
    if not opens and risk.CLIP_USD * 0.7 <= gap <= risk.CLIP_USD + 0.6:
        return False
    return gap >= float(rec.get("max_loss") or risk.MAX_DAY_LOSS)


def dump(out):
    OUT.write_text(json.dumps(out) + "\n")
    print(json.dumps(out))


def main():
    if paths.HOLD.exists():
        b = books() or {}
        dump(
            {
                "action": "HOLD",
                "reason": "operator hold",
                "buyingPower": b.get("buyingPower"),
                "working": b.get("working"),
                "open": [o.get("slug") for o in (b.get("open") or [])],
            }
        )
        return
    refresh_tape()
    tape = json.loads(TAPE.read_text()) if TAPE.exists() else {}
    b = books()
    if not b:
        dump({"action": "HOLD", "reason": "books failed"})
        return
    opens = b.get("open") or []
    working = float(b.get("working") or 0)
    # Loop never sells. Watch owns stop / trail / LATER.
    if len(opens) >= MAX_OPEN:
        dump(
            {
                "action": "HOLD",
                "reason": f"ticket_cap open={len(opens)}/{MAX_OPEN}",
                "buyingPower": b.get("buyingPower"),
                "working": working,
                "open": [o.get("slug") for o in opens],
            }
        )
        return
    if working < TICKET:
        dump(
            {
                "action": "HOLD",
                "reason": f"working ${working} < clip ${TICKET}",
                "buyingPower": b.get("buyingPower"),
                "working": working,
                "open": [o.get("slug") for o in opens],
            }
        )
        return
    bp = float(b.get("buyingPower") or 0)
    if session_halt(bp, opens):
        rec = ensure_session(bp)
        start = float(rec.get("start_bp") or bp)
        marked = sum(float(o.get("mark") or o.get("cost") or 0) for o in opens)
        gap = start - (bp + marked)
        cap = float(rec.get("max_loss") or risk.MAX_DAY_LOSS)
        dump(
            {
                "action": "HOLD",
                "reason": f"session loss circuit −${gap:.2f} / ${cap:.0f}",
                "buyingPower": bp,
                "working": working,
            }
        )
        return
    cool = cooling_slugs()
    ban = skips() | {s for s in cool if s != "*legacy*"}
    open_slugs = {o["slug"] for o in opens}
    pick = pick_buy(tape, ban, open_slugs)
    if not pick:
        later = list(tape.get("later") or [])
        live_rows = list(tape.get("live") or [])
        soon_rows = list(tape.get("soon") or [])
        unused = [r for r in live_rows + soon_rows if (r.get("slug") or "") not in open_slugs]
        why = []
        for r in unused + later[:6]:
            s = r.get("slug") or "?"
            w = risk.why_not(r)
            if w:
                why.append(f"{s[:36]}:{w}")
            elif s in ban:
                why.append(f"{s[:36]}:skip_or_cool")
        nxt = later[0] if later else {}
        if unused:
            reason = f"open={len(opens)}/{MAX_OPEN} unused {len(unused)} rejected"
        elif live_rows or soon_rows:
            reason = f"open={len(opens)}/{MAX_OPEN} all live/soon already held"
        else:
            reason = f"open={len(opens)}/{MAX_OPEN} tape empty of live/soon"
        dump(
            {
                "action": "HOLD",
                "reason": reason,
                "working": working,
                "open": [o.get("slug") for o in opens],
                "live_n": len(live_rows),
                "soon_n": len(soon_rows),
                "later_n": len(later),
                "next": nxt.get("title"),
                "next_min": nxt.get("minutes_to_start"),
                "why": why[:8],
                "version": risk.VERSION,
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
            "version": risk.VERSION,
        }
    )


if __name__ == "__main__":
    main()
