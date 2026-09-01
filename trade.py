#!/usr/bin/env python3
"""Trader executor. No scanning. CoS passes the slug.
  python3 trade.py books
  python3 trade.py buy SLUG --usd 3
  python3 trade.py cut SLUG
"""
from __future__ import annotations
import argparse, base64, json, sys, time, urllib.request
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ed25519

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lock as desklock
import paths
import risk

API = "https://api.polymarket.us"
PUB = "https://gateway.polymarket.us"
ENVP = paths.ENVP
SKIP = paths.DESK / "skip_slugs.txt"
TAPE = paths.DESK / "tape.json"
RING = risk.RING_USD
MAX_OPEN = risk.MAX_OPEN
MIN_USD, MAX_USD = risk.CLIP_USD, risk.MAX_USD


def load_env():
    d = {}
    for line in ENVP.read_text().splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        d[k] = v.strip()
    return d


def signed(method, path, e, body=None):
    # Venue signs the path *without* query. Including ?cursor=… 401s.
    pk = ed25519.Ed25519PrivateKey.from_private_bytes(base64.b64decode(e["POLYMARKET_SECRET_KEY"])[:32])
    ts = str(int(time.time() * 1000))
    sign_path = path.split("?")[0]
    sig = base64.b64encode(pk.sign(f"{ts}{method}{sign_path}".encode())).decode()
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={
            "X-PM-Access-Key": e["POLYMARKET_KEY_ID"],
            "X-PM-Timestamp": ts,
            "X-PM-Signature": sig,
            "Content-Type": "application/json",
            "User-Agent": "estes-desk/trade",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as err:
        raw = err.read().decode()
        try:
            return err.code, json.loads(raw)
        except Exception:
            return err.code, {"error": raw[:400]}


def bbo(slug):
    req = urllib.request.Request(PUB + f"/v1/markets/{slug}/bbo", headers={"User-Agent": "estes-desk/trade"})
    with urllib.request.urlopen(req, timeout=12) as r:
        return json.loads(r.read().decode()).get("marketData") or {}


def px(x):
    try:
        return float((x or {}).get("value") or 0)
    except Exception:
        return 0.0


def skip_add(slug):
    SKIP.parent.mkdir(parents=True, exist_ok=True)
    have = SKIP.read_text() if SKIP.exists() else ""
    if slug not in have.split():
        with SKIP.open("a") as f:
            f.write(slug + "\n")


def books(e):
    st, bal = signed("GET", "/v1/account/balances", e)
    if st != 200:
        print(json.dumps({"ok": False, "stage": "books", "http": st}))
        return None
    b = (bal.get("balances") or [{}])[0] if isinstance(bal, dict) else {}
    if b.get("buyingPower") is None:
        print(json.dumps({"ok": False, "stage": "books", "reason": "no_buyingPower"}))
        return None
    bp = float(b.get("buyingPower") or 0)
    st, pos = signed("GET", "/v1/portfolio/positions", e)
    positions = (pos or {}).get("positions") or {}
    open_ = []
    for slug, p in positions.items():
        md = bbo(slug)
        avg = px(p.get("costPerShare"))
        qty = float(p.get("qtyAvailableDecimal") or 0)
        if not avg and qty:
            avg = px(p.get("cost")) / qty
        bid, ask = px(md.get("bestBid")), px(md.get("bestAsk"))
        open_.append(
            {
                "slug": slug,
                "qty": qty,
                "avg": avg,
                "bid": bid,
                "ask": ask,
                "cost": px(p.get("cost")),
                "mark": px(p.get("cashValue")),
                "delta_c": round((bid - avg) * 100, 2) if avg and bid else None,
            }
        )
    marked = sum(float(o.get("mark") or 0) for o in open_)
    ring, rec = risk.compute_ring(bp, marked, persist=True)
    out = {
        "buyingPower": bp,
        "working": round(bp - ring, 4),
        "ring": ring,
        "ring_floor": risk.RING_USD,
        "reserved": rec.get("reserved"),
        "waterline": rec.get("waterline"),
        "open": open_,
        "asof": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    paths.ensure_desk()
    (paths.DESK / "books.json").write_text(json.dumps(out) + "\n")
    print(json.dumps(out))
    return out


def preview_place(e, order):
    st, prev = signed("POST", "/v1/order/preview", e, {"request": order})
    if st != 200:
        print(json.dumps({"ok": False, "stage": "preview", "http": st, "body": prev}))
        return False
    st, body = signed("POST", "/v1/orders", e, order)
    execs = (body.get("executions") if isinstance(body, dict) else None) or []
    fills = [x for x in execs if isinstance(x, dict) and x.get("type") in ("EXECUTION_TYPE_FILL", "EXECUTION_TYPE_PARTIAL_FILL")]
    ok = st == 200 and bool(fills)
    print(json.dumps({"ok": ok, "stage": "place", "http": st, "id": body.get("id") if isinstance(body, dict) else None, "fills": [{"type": f.get("type"), "px": f.get("lastPx"), "sh": f.get("lastShares")} for f in fills]}))
    if ok:
        persist_ledger()
    return ok


def persist_ledger():
    import subprocess

    try:
        subprocess.run(["python3", str(paths.REPO / "ledger.py")], capture_output=True, text=True, timeout=45)
    except Exception:
        pass


def skipped(slug):
    if not SKIP.exists():
        return False
    return slug in SKIP.read_text().split()


def buy(e, slug, usd):
    if paths.HOLD.exists():
        print(json.dumps({"ok": False, "stage": "operator_hold", "slug": slug}))
        return
    if paths.PAPER:
        print(json.dumps({"ok": True, "stage": "paper", "cmd": "buy", "slug": slug, "usd": usd}))
        return
    with desklock.order_lock():
        _buy(e, slug, usd)


def _buy(e, slug, usd):
    if skipped(slug):
        print(json.dumps({"ok": False, "stage": "skip_list", "slug": slug}))
        return
    if slug.startswith(risk.BAN_PREFIX):
        print(json.dumps({"ok": False, "stage": "no_3way", "slug": slug}))
        return
    if not TAPE.exists():
        print(json.dumps({"ok": False, "stage": "no_tape", "slug": slug}))
        return
    try:
        tape = json.loads(TAPE.read_text())
        rows = {r.get("slug"): r for r in list(tape.get("live") or []) + list(tape.get("soon") or [])}
        if slug not in rows:
            print(json.dumps({"ok": False, "stage": "not_actionable", "slug": slug}))
            return
        row = dict(rows.get(slug) or {})
        if risk.rank(row) is None:
            print(json.dumps({"ok": False, "stage": "rank_reject", "slug": slug}))
            return
    except Exception as err:
        print(json.dumps({"ok": False, "stage": "tape_error", "error": str(err)[:120]}))
        return
    if usd < risk.CLIP_USD or usd > risk.MAX_USD:
        print(json.dumps({"ok": False, "stage": "size", "usd": usd}))
        return
    st, bal = signed("GET", "/v1/account/balances", e)
    bp = float(((bal.get("balances") or [{}])[0] if isinstance(bal, dict) else {}).get("buyingPower") or 0)
    st, pos = signed("GET", "/v1/portfolio/positions", e)
    positions = (pos or {}).get("positions") or {}
    marked = sum(px(p.get("cashValue")) for p in positions.values())
    ring, rec = risk.compute_ring(bp, marked, persist=True)
    if bp - usd < ring:
        print(json.dumps({"ok": False, "stage": "ring_fence", "buyingPower": bp, "usd": usd, "ring": ring, "reserved": rec.get("reserved")}))
        return
    if slug in positions:
        print(json.dumps({"ok": False, "stage": "already_in", "slug": slug}))
        return
    if len(positions) >= risk.MAX_OPEN:
        print(json.dumps({"ok": False, "stage": "max_open", "n": len(positions), "max": risk.MAX_OPEN}))
        return
    md = bbo(slug)
    ask, bid = px(md.get("bestAsk")), px(md.get("bestBid"))
    row["ask"], row["bid"], row["spr"] = ask, bid, round(ask - bid, 4) if ask and bid else None
    if risk.rank(row) is None:
        print(json.dumps({"ok": False, "stage": "gate", "bid": bid, "ask": ask}))
        return
    qty = round(usd / ask, 2)
    order = {
        "marketSlug": slug,
        "intent": "ORDER_INTENT_BUY_LONG",
        "type": "ORDER_TYPE_LIMIT",
        "price": {"value": f"{ask:.4f}", "currency": "USD"},
        "quantity": qty,
        "tif": "TIME_IN_FORCE_IMMEDIATE_OR_CANCEL",
        "manualOrderIndicator": "MANUAL_ORDER_INDICATOR_AUTOMATIC",
        "synchronousExecution": True,
        "maxBlockTime": "10",
    }
    preview_place(e, order)


def cut(e, slug):
    if paths.PAPER:
        print(json.dumps({"ok": True, "stage": "paper", "cmd": "cut", "slug": slug}))
        return
    with desklock.order_lock():
        _cut(e, slug)


def _cut(e, slug):
    st, pos = signed("GET", "/v1/portfolio/positions", e)
    p = ((pos or {}).get("positions") or {}).get(slug)
    if not p:
        print(json.dumps({"ok": True, "stage": "already_flat", "slug": slug}))
        return
    qty = float(p.get("qtyAvailableDecimal") or 0)
    avg = px(p.get("costPerShare"))
    if not avg and qty:
        avg = px(p.get("cost")) / qty
    md = bbo(slug)
    bid, ask = px(md.get("bestBid")), px(md.get("bestAsk"))
    spr = round(ask - bid, 4) if ask and bid else 0.02
    # Tight book: take the bid. Wide: cross. Empty IOC → cross once (KC-CLE miss).
    limit = round(bid if spr <= 0.01 else max(bid - 0.02, 0.01), 4)
    order = {
        "marketSlug": slug,
        "intent": "ORDER_INTENT_SELL_LONG",
        "type": "ORDER_TYPE_LIMIT",
        "price": {"value": f"{limit:.4f}", "currency": "USD"},
        "quantity": qty,
        "tif": "TIME_IN_FORCE_IMMEDIATE_OR_CANCEL",
        "manualOrderIndicator": "MANUAL_ORDER_INDICATOR_AUTOMATIC",
        "synchronousExecution": True,
        "maxBlockTime": "12",
    }
    ok = preview_place(e, order)
    if not ok and bid:
        order["price"] = {"value": f"{max(bid - 0.02, 0.01):.4f}", "currency": "USD"}
        ok = preview_place(e, order)
    if ok:
        skip_add(slug)
        if avg and bid and bid < avg:
            p = paths.DESK / "last_cut"
            rec = {}
            if p.exists():
                try:
                    rec = json.loads(p.read_text())
                    if not isinstance(rec, dict):
                        rec = {}
                except Exception:
                    rec = {}
            rec[slug] = int(time.time())
            p.write_text(json.dumps(rec) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["books", "buy", "cut"])
    ap.add_argument("slug", nargs="?")
    ap.add_argument("--usd", type=float, default=2.0)
    args = ap.parse_args()
    e = load_env()
    if args.cmd == "books":
        books(e)
    elif args.cmd == "buy":
        if not args.slug:
            raise SystemExit("slug required")
        buy(e, args.slug, args.usd)
    elif args.cmd == "cut":
        if not args.slug:
            raise SystemExit("slug required")
        cut(e, args.slug)


if __name__ == "__main__":
    main()
