# Desk v13 — architecture

**Live version: v13.** Start from a fresh TUI pasting `GO.md`.

## What broke

v11 **bid-tick** rank fired 13 programmatic buys on 2026-08-29 (wrong *names*, but the machine traded).
v12 (PR #4) switched momentum to **two last-trade prints** and required last≈bid. Last-trades are sparse; the afternoon GO HOLDed every cycle. That is the waste.

## Roles (unchanged)

```
one CoS TUI  →  reports / nohup pids / never orders
loop.py      →  ONLY BUYER   (loop.pid)
watch.py     →  ONLY SELLER  (watch.pid, 4s on open tickets)
orders.lock  →  one buy or cut at a time
```

## Market watch (efficient)

```
research.py           full scan ~20s   all operational US leagues + ATP/WTA → live/soon first, ≤100 BBO
research.py --hot     8s               re-BBO live/soon slugs only (no league crawl)
intent.py             picks BUY        uses --hot if tape <25s old
loop.py               cadence          8s while any live 18–42¢ exists, else 20s
watch.py              exits            GET positions + BBO *open* slugs every 4s
```

Universe scan is cheap enough; the hot path is what catches the +2¢ bid tick.

## Policy (v13)

LIVE `aec-` **18–42¢**. **One +2¢ bid uptick** (v11 fire path). Reject bounce if prior bid tick ≤ −2¢. Spread ≤ 2¢. OI ≥ 5k, depth ≥ 3. No 3-way, no 43–57, no 0–0 Q1, no $10. Clip $2 × max 2. Stop −3¢. Trail +5¢ / give 3¢. Session −$2 from this GO.

HOLD is correct when *no live 18–42 with a +2¢ bid tick* exists — not when last-trade history is empty.
