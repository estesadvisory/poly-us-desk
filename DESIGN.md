# Desk v17 — architecture

**Live version: v17.** One Terminal: `python3 desk.py`. Zero LLM in the loop.

## What we kept / dropped

| Attempt | Keep | Drop |
|---------|------|------|
| v11 | BBO fire path (it actually traded) | 18–42-only religion |
| v12 | — | last-trade + score AND-gates (starved) |
| v13 | all operational US leagues | — |
| v14 | reject dumping bids | — |
| v15 | 12–88 exit-able, $10 ring, $2 × 2 | rank that preferred 50¢ fee-max |
| ledger | trail winners, stop losers, no 3-ways, no scratch | 1¢ scalps |

## Roles

```
desk.py (Terminal)  →  HUD + commands + restart dead children
research            →  all-league tape / --hot re-BBO
loop.py             →  ONLY BUYER
watch.py            →  ONLY SELLER  (4s on open tickets)
orders.lock         →  one buy or cut at a time
```

Code is the git repo. State is `~/.grok/desk`. After an edit: `reload` or `quit` + run again.

## Policy (v17)

- $10 ring. Working = the rest. Clip $2. Ticket cap is working cash, not 2.
- All operational US leagues. LIVE or SOON (≤45m) `aec-`. Overdue NS kept live 90m.
- 12–88¢ so we can exit. First print allowed. `delta_c < 0` rejected. Bounce (prior ≤ −2¢) rejected.
- Rank: tight book + lower taker fee + small uptick bonus.
- Stop −3¢. Trail arm +5¢, give back 3¢. No scratch at +1–2¢.
- Per-slug 15m after a losing cut. Session −$2 circuit from this GO.
