# Desk v11 — architecture

**Live version: v11.** Start only from a fresh TUI pasting `GO.md`.

## Roles

```
one CoS TUI  →  reports / nohup pids / never orders
loop.py      →  ONLY BUYER   (loop.pid, refuses a second)
watch.py     →  ONLY SELLER  (watch.pid, refuses a second)
orders.lock  →  one buy or cut at a time
```

Intent/hum never CUT. Watch owns stop, trail, and LATER TTR.

## Policy

LIVE 2-way dogs **18–42¢**, two upticks, OI ≥ 5k, depth ≥ 5. No fav band (TCU net red; Idaho +$0.06 after fees). No 43–57¢, no 3-way, no pregame. Stop −3¢. Trail +5¢ / give 3¢ from peak every 4s. Session halt $2 from GO BP. $10 never trades. $2 × max 2.

HOLD on an empty qualified tape is success.

## Struck

Parallel agent traders. LLM scanner. Loop selling. Fav 58–72¢. Hard reap. Pregame sit. Chicago-day −$6.38 as a halt on a new GO.
