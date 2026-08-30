#!/usr/bin/env python3
"""Fast public tape. No LLM. Target <20s. Writes ~/.grok/desk/tape.md
  python3 research.py          # all operational US leagues
  python3 research.py --hot    # re-BBO live/soon slugs only
"""
from __future__ import annotations
import concurrent.futures, json, sys, urllib.request, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths
import risk

PUB = "https://gateway.polymarket.us"
# US venue, all operational leagues. Hardcoded FOCUS was the starve.
EXTRA_LEAGUES = ("atp", "wta")  # events exist; sometimes missing from /v2/leagues
EVENT_LIMIT = 40
BBO_CAP = 100
LIVE_KEEP = 24
SOON_KEEP = 12
SOON_MIN = risk.SOON_MIN  # capital may sit this long; not 90
SKIP = paths.DESK / "skip_slugs.txt"
OUT = paths.DESK / "tape.md"
OUTJ = paths.DESK / "tape.json"
QUOTES = paths.DESK / "quotes.json"
UA = {"User-Agent": "estes-desk/research"}


def get(path, params=None, timeout=12):
    url = PUB + path
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def px(x):
    try:
        return float((x or {}).get("value") or 0)
    except Exception:
        return 0.0


def skips():
    if not SKIP.exists():
        return set()
    return {ln.strip() for ln in SKIP.read_text().splitlines() if ln.strip() and not ln.startswith("#")}


def bbo(slug):
    try:
        md = get(f"/v1/markets/{slug}/bbo").get("marketData") or {}
        bid, ask = px(md.get("bestBid")), px(md.get("bestAsk"))
        last = px(md.get("lastTradePx"))
        return {
            "slug": slug,
            "bid": bid,
            "ask": ask,
            "last": last,
            "spr": round(ask - bid, 4) if ask and bid else None,
            "oi": md.get("openInterest"),
            "bid_depth": md.get("bidDepth"),
        }
    except Exception:
        return {"slug": slug, "error": True}


def league_slugs():
    slugs = []
    try:
        rows = get("/v2/leagues", {"limit": 200}).get("leagues") or []
        slugs = [x.get("slug") for x in rows if x.get("isOperational") and x.get("slug")]
    except Exception:
        slugs = []
    out = []
    seen = set()
    for s in list(slugs) + list(EXTRA_LEAGUES):
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def fetch_league(lg):
    try:
        evs = get(f"/v2/leagues/{lg}/events", {"limit": EVENT_LIMIT}).get("events") or []
        return lg, evs, None
    except Exception as ex:
        return lg, [], type(ex).__name__


def event_flags(ended: bool, api_live, mins: float, period: str) -> tuple[bool, bool]:
    """(live, soon). Ended never buys. In-game period or api_live counts; leftover NS does not."""
    if ended:
        return False, False
    if api_live is True:
        live_g = True
    elif (period or "").strip() not in ("", "NS"):
        live_g = True
    elif mins < 0 and mins > -risk.OVERDUE_LIVE_MIN and api_live is not False:
        live_g = True
    else:
        live_g = False
    soon_g = (not live_g) and (-SOON_MIN <= mins <= SOON_MIN)
    return live_g, soon_g


def picks(markets):
    out = []
    for m in markets or []:
        if not isinstance(m, dict):
            continue
        s = m.get("slug") or ""
        mt = m.get("sportsMarketType") or ""
        if s.startswith("aec-"):
            out.append(("aec", s))
        elif s.startswith("atc-") and "draw" not in s and "soccer_team_full_time_winner" in mt:
            out.append(("atc", s))
    seen, uniq = set(), []
    for t, s in out:
        if s in seen:
            continue
        seen.add(s)
        uniq.append((t, s))
    return uniq


def main():
    paths.ensure_desk()
    now = datetime.now(timezone.utc)
    ban = skips()
    live, soon_l, nxt, reject = [], [], [], []
    slugs = []
    meta = {}
    leagues = league_slugs()
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        fetched = list(ex.map(fetch_league, leagues))
    for lg, evs, err in fetched:
        if err:
            reject.append(f"{lg} fetch fail {err}")
            continue
        for e in evs:
            st = e.get("startTime") or ""
            try:
                ts = datetime.fromisoformat(st.replace("Z", "+00:00"))
            except Exception:
                continue
            period = (e.get("period") or "").strip()
            ended = e.get("ended") is True
            api_live = e.get("live")
            mins = (ts - now).total_seconds() / 60.0
            live_g, soon_g = event_flags(ended, api_live, mins, period)
            horizon = live_g or soon_g or (0 < mins <= 90)
            if not horizon:
                continue
            for kind, s in picks(e.get("markets")):
                if s in ban:
                    continue
                slugs.append(s)
                meta[s] = {
                    "lg": lg,
                    "title": e.get("title"),
                    "period": period or "NS",
                    "start": st,
                    "live": live_g,
                    "soon": soon_g,
                    "minutes_to_start": round(mins, 1),
                    "kind": kind,
                    "elapsed": e.get("elapsed"),
                    "score": e.get("score"),
                }
    ordered = []
    seen_s = set()
    per_lg: dict[str, int] = {}
    for want_live, want_soon in ((True, False), (False, True), (False, False)):
        for s in slugs:
            if s in seen_s:
                continue
            m = meta.get(s) or {}
            if want_live and not m.get("live"):
                continue
            if want_soon and (m.get("live") or not m.get("soon")):
                continue
            if not want_live and not want_soon and (m.get("live") or m.get("soon")):
                continue
            lg = m.get("lg") or risk.league(s)
            if per_lg.get(lg, 0) >= risk.BBO_PER_LEAGUE:
                continue
            per_lg[lg] = per_lg.get(lg, 0) + 1
            seen_s.add(s)
            ordered.append(s)
    slugs = ordered[:BBO_CAP]
    prev = {}
    if QUOTES.exists():
        try:
            prev = json.loads(QUOTES.read_text())
        except Exception:
            prev = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        quotes = list(ex.map(bbo, slugs))
    now_q = {}
    for q in quotes:
        s = q.get("slug")
        if q.get("error") or s not in meta:
            continue
        m = meta[s]
        ask, bid, spr = q.get("ask") or 0, q.get("bid") or 0, q.get("spr")
        old = prev.get(s) or {}
        last = q.get("last") or 0
        bid_hist = [x for x in (old.get("bids") or []) if x]
        if old.get("bid") and (not bid_hist or bid_hist[-1] != old.get("bid")):
            bid_hist.append(old["bid"])
        bid_hist = bid_hist[-3:]
        last_hist = [x for x in (old.get("lasts") or []) if x]
        if old.get("last") and (not last_hist or last_hist[-1] != old.get("last")):
            last_hist.append(old["last"])
        last_hist = last_hist[-3:]
        delta_c = round((bid - bid_hist[-1]) * 100, 2) if bid_hist and bid else None
        delta2_c = round((bid_hist[-1] - bid_hist[-2]) * 100, 2) if len(bid_hist) >= 2 else None
        last_delta_c = round((last - last_hist[-1]) * 100, 2) if last_hist and last else None
        last_delta2_c = round((last_hist[-1] - last_hist[-2]) * 100, 2) if len(last_hist) >= 2 else None
        q["delta_c"] = delta_c
        q["delta2_c"] = delta2_c
        q["last_delta_c"] = last_delta_c
        q["last_delta2_c"] = last_delta2_c
        now_q[s] = {
            "bid": bid,
            "ask": ask,
            "last": last,
            "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "bids": (bid_hist + [bid])[-3:] if bid else bid_hist,
            "lasts": (last_hist + [last])[-3:] if last else last_hist,
        }
        row = {**m, **q}
        if m["kind"] != "aec":
            reject.append(f"{s} 3way")
            continue
        scored = risk.rank(row)
        row["rank"] = round(scored, 3) if scored is not None else None
        if m["kind"] == "aec" and m["live"]:
            live.append(row)
        elif m.get("soon") and m["kind"] == "aec":
            soon_l.append(row)
        elif (not m["live"]) and not m.get("soon") and m["kind"] == "aec":
            nxt.append(row)
        elif spr and spr > 0.015:
            reject.append(f"{s} wide {spr}")
    live.sort(key=lambda r: (-(r.get("rank") or -1), r.get("spr") or 9))
    soon_l.sort(key=lambda r: (r.get("minutes_to_start") or 99, r.get("spr") or 9))
    nxt.sort(key=lambda r: (r.get("start") or "", r.get("spr") or 9))
    lines = [
        f"# tape {now.strftime('%Y-%m-%d %H:%M')}Z",
        f"live {len(live)} soon(≤{SOON_MIN}m) {len(soon_l)} later {len(nxt)} scanned {len(slugs)} leagues {len(leagues)}",
        "",
        "## LIVE",
    ]
    for r in live[:LIVE_KEEP]:
        lines.append(f"- {r['kind']} {r['slug']} {r['lg']} {r['period']} {r.get('score')} rank {r.get('rank')} d {r.get('delta_c')}/{r.get('delta2_c')} bid {r['bid']} last {r.get('last')} ask {r['ask']} | {r['title']}")
    lines += ["", f"## SOON ≤{SOON_MIN}m (ok to wait)"]
    for r in soon_l[:SOON_KEEP]:
        lines.append(f"- {r['slug']} in {r.get('minutes_to_start')}m score {r.get('score')} bid {r['bid']} ask {r['ask']} spr {r['spr']} | {r['title']}")
    lines += ["", "## LATER (do not buy — cash waits)"]
    for r in nxt[:4]:
        lines.append(f"- {r['slug']} in {r.get('minutes_to_start')}m | {r['title']}")
    lines += ["", "## REJECT (sample)", "- " + "; ".join(reject[:8])]
    OUT.write_text("\n".join(lines) + "\n")
    ttr = [
        s
        for s, m in meta.items()
        if m.get("kind") == "aec" and (m.get("live") or m.get("soon"))
    ]
    payload = {
        "asof": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "live": live[:LIVE_KEEP],
        "soon": soon_l[:SOON_KEEP],
        "later": nxt[:4],
        "ttr": ttr,
        "reject": reject[:8],
        "scanned": len(slugs),
        "leagues": len(leagues),
        "full_asof": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    OUTJ.write_text(json.dumps(payload, indent=2) + "\n")
    QUOTES.write_text(json.dumps(now_q, indent=2) + "\n")
    print(OUT.read_text())


def hot():
    """Re-BBO slugs already on tape. No league crawl."""
    paths.ensure_desk()
    now = datetime.now(timezone.utc)
    if not OUTJ.exists():
        return main()
    try:
        tape = json.loads(OUTJ.read_text())
    except Exception:
        return main()
    rows = list(tape.get("live") or []) + list(tape.get("soon") or [])
    slugs = [r.get("slug") for r in rows if r.get("slug")]
    slugs = list(dict.fromkeys(slugs))
    if not slugs:
        return main()
    meta = {r["slug"]: r for r in rows if r.get("slug")}
    prev = {}
    if QUOTES.exists():
        try:
            prev = json.loads(QUOTES.read_text())
        except Exception:
            prev = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        quotes = list(ex.map(bbo, slugs))
    live, soon_l, nxt, reject, now_q = [], [], [], [], {}
    ban = skips()
    for q in quotes:
        s = q.get("slug")
        if q.get("error") or s not in meta or s in ban:
            continue
        m = dict(meta[s])
        ask, bid, spr = q.get("ask") or 0, q.get("bid") or 0, q.get("spr")
        old = prev.get(s) or {}
        last = q.get("last") or 0
        bid_hist = [x for x in (old.get("bids") or []) if x]
        if old.get("bid") and (not bid_hist or bid_hist[-1] != old.get("bid")):
            bid_hist.append(old["bid"])
        bid_hist = bid_hist[-3:]
        last_hist = [x for x in (old.get("lasts") or []) if x]
        if old.get("last") and (not last_hist or last_hist[-1] != old.get("last")):
            last_hist.append(old["last"])
        last_hist = last_hist[-3:]
        delta_c = round((bid - bid_hist[-1]) * 100, 2) if bid_hist and bid else None
        delta2_c = round((bid_hist[-1] - bid_hist[-2]) * 100, 2) if len(bid_hist) >= 2 else None
        last_delta_c = round((last - last_hist[-1]) * 100, 2) if last_hist and last else None
        last_delta2_c = round((last_hist[-1] - last_hist[-2]) * 100, 2) if len(last_hist) >= 2 else None
        q["delta_c"] = delta_c
        q["delta2_c"] = delta2_c
        q["last_delta_c"] = last_delta_c
        q["last_delta2_c"] = last_delta2_c
        now_q[s] = {
            "bid": bid,
            "ask": ask,
            "last": last,
            "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "bids": (bid_hist + [bid])[-3:] if bid else bid_hist,
            "lasts": (last_hist + [last])[-3:] if last else last_hist,
        }
        row = {**m, **q}
        scored = risk.rank(row)
        row["rank"] = round(scored, 3) if scored is not None else None
        if m.get("live"):
            live.append(row)
        elif m.get("soon"):
            soon_l.append(row)
        else:
            nxt.append(row)
    live.sort(key=lambda r: (-(r.get("rank") or -1), r.get("spr") or 9))
    payload = {
        "asof": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "live": live[:LIVE_KEEP],
        "soon": soon_l[:SOON_KEEP],
        "later": tape.get("later") or nxt[:4],
        "ttr": tape.get("ttr") or [],
        "reject": reject[:8],
        "scanned": len(slugs),
        "hot": True,
        "full_asof": tape.get("full_asof"),
        "leagues": tape.get("leagues"),
    }
    OUTJ.write_text(json.dumps(payload, indent=2) + "\n")
    merged = prev
    merged.update(now_q)
    QUOTES.write_text(json.dumps(merged, indent=2) + "\n")
    lines = [
        f"# tape {now.strftime('%Y-%m-%d %H:%M')}Z hot",
        f"live {len(live)} soon {len(soon_l)} scanned {len(slugs)}",
        "",
        "## LIVE",
    ]
    for r in live[:LIVE_KEEP]:
        lines.append(
            f"- {r.get('kind')} {r['slug']} {r.get('lg')} {r.get('period')} {r.get('score')} "
            f"rank {r.get('rank')} d {r.get('delta_c')}/{r.get('delta2_c')} bid {r.get('bid')} "
            f"last {r.get('last')} ask {r.get('ask')} | {r.get('title')}"
        )
    OUT.write_text("\n".join(lines) + "\n")
    print(OUT.read_text())


if __name__ == "__main__":
    if "--hot" in sys.argv:
        hot()
    else:
        main()

