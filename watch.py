#!/usr/bin/env python3
"""CoS watch: OPEN positions only. TTR cut, LIVE trail, SOON hard-stop. Silent otherwise."""
from __future__ import annotations
import json, time, sys, base64, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ed25519

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lock as desklock
import risk

PUB = "https://gateway.polymarket.us"
API = "https://api.polymarket.us"
ENVP = Path.home() / ".grok/secrets/polymarket-us.env"
TAPE = Path.home() / ".grok/desk/tape.json"
PEAKF = Path.home() / ".grok/desk/peak.json"


def env():
    d = {}
    for line in ENVP.read_text().splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        d[k] = v.strip()
    return d


def signed(method, path, e):
    pk = ed25519.Ed25519PrivateKey.from_private_bytes(base64.b64decode(e["POLYMARKET_SECRET_KEY"])[:32])
    ts = str(int(time.time() * 1000))
    sig = base64.b64encode(pk.sign(f"{ts}{method}{path}".encode())).decode()
    req = urllib.request.Request(
        API + path,
        method=method,
        headers={
            "X-PM-Access-Key": e["POLYMARKET_KEY_ID"],
            "X-PM-Timestamp": ts,
            "X-PM-Signature": sig,
            "Content-Type": "application/json",
            "User-Agent": "estes-desk/watch",
        },
    )
    with urllib.request.urlopen(req, timeout=12) as r:
        return json.loads(r.read().decode())


def bbo(slug):
    req = urllib.request.Request(PUB + f"/v1/markets/{slug}/bbo", headers={"User-Agent": "estes-desk/watch"})
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.loads(r.read().decode()).get("marketData") or {}


def px(x):
    try:
        return float((x or {}).get("value") or 0)
    except Exception:
        return 0.0


def cut_now(slug):
    import subprocess

    trade = Path.home() / ".grok/desk/trade.py"
    r = subprocess.run(["python3", str(trade), "cut", slug], capture_output=True, text=True, timeout=45)
    line = (r.stdout or r.stderr or "").strip().splitlines()
    last = line[-1] if line else ""
    print(f"CUT {slug} {last}", flush=True)


def tape_sets():
    """(later, live). Missing from tape ≠ cut (research hole). Stale tape → (None, None) = treat LIVE."""
    if not TAPE.exists():
        return None, None
    try:
        t = json.loads(TAPE.read_text())
        asof = t.get("asof") or ""
        ts = datetime.fromisoformat(asof.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - ts).total_seconds()
        if age > risk.TAPE_STALE_SEC:
            return None, None
        live = {r.get("slug") for r in (t.get("live") or []) if r.get("slug")}
        later = {r.get("slug") for r in (t.get("later") or []) if r.get("slug")}
        return later, live
    except Exception:
        return None, None


def load_peak():
    if not PEAKF.exists():
        return {}
    try:
        d = json.loads(PEAKF.read_text())
        return {k: float(v) for k, v in d.items()} if isinstance(d, dict) else {}
    except Exception:
        return {}


def save_peak(peak):
    try:
        PEAKF.write_text(json.dumps(peak) + "\n")
    except Exception:
        pass


def main():
    desklock.claim("watch")
    print(json.dumps({"ok": True, "role": "watch", "version": risk.VERSION}), flush=True)
    e = env()
    deadline = time.time() + 12 * 3600
    last_cut = {}
    peak = load_peak()
    while time.time() < deadline:
        try:
            pos = signed("GET", "/v1/portfolio/positions", e).get("positions") or {}
            for gone in [s for s in list(peak) if s not in pos]:
                peak.pop(gone, None)
            later, live_set = tape_sets()
            for slug, p in pos.items():
                avg = px(p.get("costPerShare"))
                if not avg:
                    cost, qty = px(p.get("cost")), float(p.get("qtyAvailableDecimal") or 0)
                    avg = cost / qty if qty else 0
                bid = px(bbo(slug).get("bestBid"))
                if not (avg and bid):
                    continue
                peak[slug] = max(peak.get(slug, bid), bid)
                now = time.time()
                if now - last_cut.get(slug, 0) < 20:
                    continue
                if later is not None and slug in later:
                    print(f"EXIT_TTR {slug}", flush=True)
                    cut_now(slug)
                    last_cut[slug] = now
                    peak.pop(slug, None)
                    continue
                is_live = True if live_set is None else slug in live_set
                side = risk.watch_exit(avg, bid, peak[slug], is_live)
                if side:
                    print(f"{side} {slug} bid={bid} avg={avg} peak={peak[slug]} live={is_live}", flush=True)
                    cut_now(slug)
                    last_cut[slug] = now
                    peak.pop(slug, None)
            save_peak(peak)
        except Exception as ex:
            print(f"WATCH_ERR {type(ex).__name__}", flush=True)
        time.sleep(4)
    print("FAILED", flush=True)
    sys.exit(1)


if __name__ == "__main__":
    main()
