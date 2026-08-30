# Desk v20 — architecture

**Live version: v20.** One Terminal: `python3 desk.py --go`. Zero LLM in the loop.

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

## Policy (v20)

- $10 ring. Working = the rest. Clip $2. Ticket cap is working cash, not 2.
- All operational US leagues. LIVE or ticking SOON (≤45m) `aec-`. NS leftover is not live. Max 1 ticket per league. A league with ≥2 losses and 0 wins today is cold.
- 12–88¢ so we can exit. LIVE first print allowed. SOON needs `delta_c > 0`. `delta_c < 0` rejected. Bounce (prior ≤ −2¢) rejected.
- Rank: tight book + lower taker fee + small uptick bonus.
- Stop −3¢. Trail arm +5¢, give back 3¢, never EXIT_UP at/under entry. No scratch at +1–2¢.
- Per-slug 15m after a losing cut. Session −$2 circuit from this GO.
