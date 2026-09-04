# Desk v26 — architecture

**Live version: v26.** Grok-operated. One Terminal: `python3 desk.py --go`. Zero LLM in the trade loop (Grok edits the repo; Python trades). Knobs: `desk.json`. Humans: `README.md`. Fork / PR: `CONTRIBUTING.md`.

## What we kept / dropped

| Attempt | Keep | Drop |
|---------|------|------|
| v11 | BBO fire path (it actually traded) | 18–42-only religion |
| v12 | — | last-trade + score AND-gates (starved) |
| v13 | all operational US leagues | — |
| v14 | reject dumping bids | — |
| v15 | 12–88 exit-able | rank that preferred 50¢ fee-max; 2-ticket freeze |
| v16 | Terminal desk, HUD, HOLD/go | CoS TUI / `nohup` |
| v17 | SOON ≤45m, MAX_OPEN=20 | 2-ticket cap |
| v18 | trail never sells through entry | pregame TTR |
| v19 | SOON uptick; `--go` after bump | — |
| v20 | intent must not `--hot` the tape | (cold leagues — removed v22) |
| v21 | −10¢ / −8¢ cliff; skip ≠ hide | −3¢ stop that sold winners |
| v22 | — | league/sport cold flag |
| v23 | no league slot; 20–88¢; 25–70 playable rank | 12–16¢ wrecks |
| v24 | LIVE uptick too; leftover NS out; trail +8/−3 | LIVE first-print lottery |
| v25 | `desk.json`; ring floor $0; 10% profit reserve | hardcoded $7 ring |
| v26 | `set` / `reserve reset`; clip_min $1; ask 20–75¢; public docs | HOLD when working < $2 clip |
| ledger | trail winners, stop losers, no 3-ways, no scratch | 1¢ scalps |

## Never again

Full table and day PnL: `LESSONS.md`. Short form:

- No last-trade/score AND-gates, no 2-ticket cap, no league **cold**, no LIVE first-print, no intent `--hot`, no skip-hiding the tape, no 3-ways, no `nohup` children.
- Do not starve the band (12–88 shrink / 18–42-only) or park so much that working < clip.
- Trail must clear fees (+8 arm). Session-loss HOLD is not the operator HOLD file.
- After merge: `python3 desk.py --go`. After a deposit: delete `~/.grok/desk/reserve.json`.

## Roles

```
desk.py (Terminal)  →  HUD + commands + restart dead children
research            →  all-league tape. `--hot` re-BBO only; **intent must not `--hot`** (v20 CS2 hole)
loop.py             →  ONLY BUYER
watch.py            →  ONLY SELLER  (4s on open tickets)
orders.lock         →  one buy or cut at a time
```

Code is the git repo. State is `~/.grok/desk`. After an edit: `reload` or `quit` + run again.

## Policy (v26)

- Ring floor and clip live in `desk.json` (overlay `~/.grok/desk/desk.json`). Default floor **$0**. Working = BP − effective ring.
- `profit_reserve_pct` (default 0.10): 10% of equity above a persisted waterline ratchets into park and does not shrink. Cap so one clip of working remains. Survives quit. After a deposit: type `reserve reset` (or delete `~/.grok/desk/reserve.json`).
- `clip_usd` (default $2) is the full ticket. `clip_min_usd` (default $1): if working is below clip but at least the min, buy a smaller ticket. Type `set` in the desk to change knobs without editing JSON.
- All operational US leagues. LIVE or ticking SOON (≤45m) `aec-`. Leftover NS is not a buy. Any number of leagues; one ticket per slug. Rank picks the best book.
- 20–75¢ so we can exit (80¢ favorites that fade are out). 12–16¢ wrecks are out. LIVE and SOON need `delta_c > 0`. `delta_c < 0` rejected. Bounce (prior ≤ −2¢) rejected.
- Rank: tight book + lower taker fee + uptick + 25–70¢ playable bonus.
- Stop −10¢ from entry, or −8¢ in one watch print. 3¢ wiggle is hold. Trail +8/−3, never EXIT_UP at/under entry. Skip blocks buys, not the tape.
- Per-slug 15m after a losing cut. Session −$5 circuit from this GO (intent HOLD, not the operator HOLD file).
