#!/usr/bin/env python3
"""Fast public tape. No LLM. Target <15s. Writes ~/.grok/desk/tape.md
  python3 research.py          # full league scan
  python3 research.py --hot    # re-BBO live/soon slugs only
"""
from __future__ import annotations
import concurrent.futures, json, sys, urllib.request, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import risk

PUB = "https://gateway.polymarket.us"
FOCUS = ["mlb", "nfl", "cfb", "wnba", "epl", "lal", "mls", "sea", "bun", "ucl", "ufc"]
SOON_MIN = risk.SOON_MIN  # capital may sit this long; not 90
SKIP = Path.home() / ".grok/desk/skip_slugs.txt"
OUT = Path.home() / ".grok/desk/tape.md"
OUTJ = Path.home() / ".grok/desk/tape.json"
QUOTES = Path.home() / ".grok/desk/quotes.json"
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
    now = datetime.now(timezone.utc)
    ban = skips()
    live, soon_l, nxt, reject = [], [], [], []
    slugs = []
    meta = {}
    for lg in FOCUS:
        try:
            evs = get(f"/v2/leagues/{lg}/events", {"limit": 10}).get("events") or []
        except Exception as e:
            reject.append(f"{lg} fetch fail")
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
            if api_live is True:
                live_g = not ended
            elif api_live is False:
                live_g = False
            else:
                live_g = (not ended) and period not in ("", "NS")
            mins = (ts - now).total_seconds() / 60.0
            # Overdue NS (posted start passed, still not in play) is still a queue for ≤20m.
            soon_g = (not live_g) and (-SOON_MIN <= mins <= SOON_MIN)
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
    slugs = list(dict.fromkeys(slugs))[:40]
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
        if m["kind"] == "aec" and m["live"] and spr is not None and spr <= 0.02:
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
        f"live {len(live)} soon(≤{SOON_MIN}m) {len(soon_l)} later {len(nxt)} scanned {len(slugs)}",
        "",
        "## LIVE",
    ]
    for r in live[:8]:
        lines.append(f"- {r['kind']} {r['slug']} {r['lg']} {r['period']} {r.get('score')} rank {r.get('rank')} d {r.get('delta_c')}/{r.get('delta2_c')} bid {r['bid']} last {r.get('last')} ask {r['ask']} | {r['title']}")
    lines += ["", f"## SOON ≤{SOON_MIN}m (ok to wait)"]
    for r in soon_l[:6]:
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
        "live": live[:8],
        "soon": soon_l[:6],
        "later": nxt[:4],
        "ttr": ttr,
        "reject": reject[:8],
        "scanned": len(slugs),
    }
    OUTJ.write_text(json.dumps(payload, indent=2) + "\n")
    QUOTES.write_text(json.dumps(now_q, indent=2) + "\n")
    print(OUT.read_text())


def hot():
    """Re-BBO slugs already on tape. No league crawl."""
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
        if m.get("live") and spr is not None and spr <= 0.02:
            live.append(row)
        elif m.get("soon"):
            soon_l.append(row)
        else:
            nxt.append(row)
    live.sort(key=lambda r: (-(r.get("rank") or -1), r.get("spr") or 9))
    payload = {
        "asof": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "live": live[:8],
        "soon": soon_l[:6],
        "later": tape.get("later") or nxt[:4],
        "ttr": tape.get("ttr") or [],
        "reject": reject[:8],
        "scanned": len(slugs),
        "hot": True,
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
    for r in live[:8]:
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

