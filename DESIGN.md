# Desk v12 — architecture

**Live version: v12.** Start only from a fresh TUI pasting `GO.md`.

## Roles

```
one CoS TUI  →  reports / nohup pids / never orders
loop.py      →  ONLY BUYER   (loop.pid, refuses a second)
watch.py     →  ONLY SELLER  (watch.pid, refuses a second)
orders.lock  →  one buy or cut at a time
```

Intent/hum never CUT. Watch owns stop, trail, and LATER TTR.

## Policy

LIVE 2-way dogs **18–42¢**, two **last-trade** upticks, score on the board (no 0–0 in Q1), last print within 1¢ of bid, OI ≥ 5k, depth ≥ 5. No favs. Stop −3¢. Trail +5¢. Cut at bid when the book is 1¢ wide. Session halt $2 from GO equity. $10 never trades. $2 × max 2.

HOLD on an empty qualified tape is success.

## Struck

Parallel agent traders. LLM scanner. Loop selling. Fav 58–72¢. Hard reap. Pregame sit. Chicago-day −$6.38 as a halt on a new GO.
