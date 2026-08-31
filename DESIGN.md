# Desk v23 — architecture

**Live version: v23.** One Terminal: `python3 desk.py --go`. Zero LLM in the loop.

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

## Policy (v23)

- $7 ring. Working = the rest. Clip $2. Ticket cap is working cash, not a league slot.
- All operational US leagues. LIVE or ticking SOON (≤45m) `aec-`. NS leftover is not live. Any number of leagues; one ticket per slug. Rank picks the best book.
- 20–88¢ so we can exit. 12–16¢ wrecks are out. LIVE first print allowed. SOON needs `delta_c > 0`. `delta_c < 0` rejected. Bounce (prior ≤ −2¢) rejected.
- Rank: tight book + lower taker fee + uptick + 25–70¢ playable bonus.
- Stop −10¢ from entry, or −8¢ in one watch print. 3¢ wiggle is hold. Trail +5/−3, never EXIT_UP at/under entry. Skip blocks buys, not the tape.
- Per-slug 15m after a losing cut. Session −$5 circuit from this GO (intent HOLD, not the operator HOLD file).
