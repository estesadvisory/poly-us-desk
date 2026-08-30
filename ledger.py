#!/usr/bin/env python3
"""SoT for PnL: venue activities, not a books snapshot and not agent memory.
  python3 ledger.py
Writes fills.json + ledger.md. Sign path without query (see trade.signed).
"""
from __future__ import annotations
import json, sys, time, urllib.parse
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

CT = ZoneInfo("America/Chicago")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths
import risk
import trade

DESK = paths.DESK
FILLS = DESK / "fills.json"
LEDGER = DESK / "ledger.md"
BOOKS = DESK / "books.json"


def activities(e):
    rows, path, seen = [], "/v1/portfolio/activities", set()
    for _ in range(8):
        st, body = trade.signed("GET", path, e)
        if st != 200 or not isinstance(body, dict):
            break
        acts = body.get("activities") or []
        key = tuple(
            ((a.get("trade") or {}).get("id"), ((a.get("trade") or {}).get("aggressorExecution") or {}).get("id"))
            for a in acts
        )
        if key in seen:
            break
        seen.add(key)
        for a in acts:
            t = a.get("trade") or {}
            ag = t.get("aggressorExecution") or {}
            o = ag.get("order") or {}
            slug = o.get("marketSlug") or t.get("marketSlug")
            if not slug:
                continue
            rows.append(
                {
                    "t": o.get("createTime") or t.get("createTime"),
                    "id": o.get("id"),
                    "slug": slug,
                    "side": o.get("side"),
                    "px": float((ag.get("lastPx") or {}).get("value") or 0),
                    "qty": float(ag.get("lastShares") or 0),
                    "fee": float((ag.get("commissionNotionalCollected") or {}).get("value") or 0),
                    "cost": float((t.get("cost") or {}).get("value") or 0),
                    "outcome": (o.get("marketMetadata") or {}).get("outcome"),
                    "title": (o.get("marketMetadata") or {}).get("title"),
                }
            )
        cur = body.get("nextCursor")
        if body.get("eof") or not cur or not acts:
            break
        path = "/v1/portfolio/activities?" + urllib.parse.urlencode({"cursor": cur})
    return rows


def chicago_day(iso: str) -> str:
    if not iso:
        return ""
    try:
        core = iso.replace("Z", "").split(".")[0][:19]
        dt = datetime.fromisoformat(core).replace(tzinfo=timezone.utc).astimezone(CT)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return (iso or "")[:10]


def trips(rows):
    by = defaultdict(lambda: {"buy": 0.0, "sell": 0.0, "bq": 0.0, "sq": 0.0, "bfee": 0.0, "sfee": 0.0, "last": ""})
    for r in rows:
        k = r["slug"]
        by[k]["last"] = max(by[k]["last"] or "", r.get("t") or "")
        if r.get("side") == "ORDER_SIDE_BUY":
            by[k]["buy"] += r["cost"]
            by[k]["bq"] += r["qty"]
            by[k]["bfee"] += r["fee"]
        elif r.get("side") == "ORDER_SIDE_SELL":
            by[k]["sell"] += r["cost"]
            by[k]["sq"] += r["qty"]
            by[k]["sfee"] += r["fee"]
    out = []
    for k, v in by.items():
        closed = v["bq"] > 0 and abs(v["bq"] - v["sq"]) < 0.02
        pnl = round(v["sell"] - v["buy"], 4) if v["buy"] and v["sell"] else None
        day = chicago_day(v["last"])
        out.append(
            {
                "slug": k,
                "buy": round(v["buy"], 4),
                "sell": round(v["sell"], 4),
                "pnl": pnl,
                "fees": round(v["bfee"] + v["sfee"], 4),
                "qty": round(v["bq"], 2),
                "buy_px": round((v["buy"] - v["bfee"]) / v["bq"], 4) if v["bq"] else None,
                "sell_px": round((v["sell"] + v["sfee"]) / v["sq"], 4) if v["sq"] else None,
                "closed": closed,
                "day": day,
                "last": v["last"],
            }
        )
    out.sort(key=lambda x: x.get("last") or "")
    return out


def main():
    e = trade.load_env()
    rows = activities(e)
    ts = trips(rows)
    st, pos = trade.signed("GET", "/v1/portfolio/positions", e)
    open_slugs = list(((pos or {}).get("positions") or {}).keys()) if st == 200 else []
    st, bal = trade.signed("GET", "/v1/account/balances", e)
    bp = 0.0
    if st == 200:
        bp = float(((bal.get("balances") or [{}])[0] or {}).get("buyingPower") or 0)
    today = datetime.now(CT).strftime("%Y-%m-%d")
    today_closed = [t for t in ts if t.get("closed") and t.get("day") == today and t.get("pnl") is not None]
    day_pnl = round(sum(t["pnl"] for t in today_closed), 4)
    payload = {
        "asof": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "buyingPower": bp,
        "working": round(bp - 10, 4),
        "open": open_slugs,
        "day": today,
        "day_closed_n": len(today_closed),
        "day_pnl": day_pnl,
        "trips": ts,
        "fills_n": len(rows),
    }
    FILLS.write_text(json.dumps(payload, indent=2) + "\n")
    lines = [
        f"# ledger {payload['asof']}",
        f"BP {bp:.2f} working {payload['working']:.2f} open {open_slugs or '[]'}",
        f"{today} closed {len(today_closed)} pnl **{day_pnl:+.2f}** (venue cost, fees in)",
        "",
        "Open positions come from GET /v1/portfolio/positions, not memory.",
        "Closed PnL comes from GET /v1/portfolio/activities, not a books snapshot.",
        "",
        f"## {today} closed",
    ]
    for t in sorted(today_closed, key=lambda x: x["pnl"]):
        lines.append(f"- {t['slug']} {t['buy_px']}→{t['sell_px']} **{t['pnl']:+.2f}** fees {t['fees']}")
    by_lg: dict[str, float] = {}
    for t in today_closed:
        lg = risk.league(t["slug"]) or "?"
        by_lg[lg] = round(by_lg.get(lg, 0.0) + float(t["pnl"]), 4)
    if by_lg:
        lines += ["", "## by league"]
        for lg, pnl in sorted(by_lg.items(), key=lambda x: x[1]):
            lines.append(f"- {lg} **{pnl:+.2f}**")
    LEDGER.write_text("\n".join(lines) + "\n")
    if BOOKS.exists():
        try:
            b = json.loads(BOOKS.read_text())
            mem_open = [o.get("slug") for o in (b.get("open") or [])]
            ghost = [s for s in mem_open if s not in open_slugs]
            if ghost:
                print(json.dumps({"ok": True, "ghost": ghost, "open": open_slugs, "day_pnl": day_pnl}))
                return
        except Exception:
            pass
    print(json.dumps({"ok": True, "open": open_slugs, "day_pnl": day_pnl, "day_closed_n": len(today_closed), "bp": bp}))


if __name__ == "__main__":
    main()
