# Venue lessons 2026-08-28 → 08-29 — live policy **v11**

Source: `GET /v1/portfolio/activities` (cost already includes taker fee). Not Chrome cash, not memory.

## Today (08-29): 13 closed, 13 red, **−$6.37**

| Slug | Buy | Sell | PnL | Why it died |
|------|-----|------|-----|-------------|
| Levante 3-way | 54¢ | 25¢ | **−$3.44** | Washington. Rode a 3-way to the floor. |
| Spurs 3-way | 43¢ | 38¢ | −$0.54 | 3-way knife, 3 minutes. |
| Newcastle (other side) | 32¢ | 29¢ | −$0.52 | Flipped the cut match. |
| Fiorentina 3-way | 33¢ | 31¢ | −$0.42 | Same knife. |
| BOS–NYY | 49.5¢ | 49¢ | −$0.35 | Coin-flip + **$0.30 fees**. |
| PIT pregame | 46.5¢ | 46¢ | −$0.23 | 35 min sit, then scratch + $0.20 fees. |
| LAD | 61¢ | 58¢ | −$0.20 | 61¢ favorite for a 2¢ dream. |
| DET–IND | 45¢ | 44¢ | −$0.18 | 1¢ + fees. |
| NCST | 37.5¢ | 37¢ | −$0.17 | Quiet dog, no rip. |
| SEA–TOR | 49¢ | 48.5¢ | −$0.14 | Mid-band. |
| CWS–MIN | 49¢ | 49¢ | −$0.12 | **Sold at entry. 100% fees.** |
| TCU | 63.2¢ | 65.3¢ | −$0.05 | Chrome looked +$0.06. Fees $0.22 ate the 2¢. |
| Roosevelt CFB | 49¢ | 50.5¢ | −$0.01 | Thin 0.30-lot book. |

CWS is the exhibit: even a scratch is a fee bill. TCU is the exhibit that **+2¢ is not a win** on this venue.

## What actually paid (08-28)

| Slug | Buy | Sell | PnL |
|------|-----|------|-----|
| PHI–LAA | 19.5¢ | 92¢ | **+$10.43** |
| AZ–SF | 5.7¢ | 34¢ | **+$4.88** |
| Idaho CFB | 72.6¢ | 75.9¢ | +$0.06 |

Winners are **live names that already moved a dime**, not 1¢ scalps. AZ 5.7¢ is dust — keep the 18¢ floor so we do not revive Washington. PHI 19.5¢ is the prototype.

## Math we ignored

US sports `feeCoefficient` 0.06. Taker fee/share ≈ `0.06 × p × (1−p)` ≈ **1.5¢/side at 50¢**, ~3¢ round-trip. A +1¢ / −1¢ scalp on a $2–$5 clip cannot have positive EV. Stop −1¢ and reap +2¢ were both inside the fee.

Live policy is **v11**. Below is how we got there (superseded).

## v7 (superseded)

- Do not buy 43–57¢. That zone is a fee trap.
- LIVE 2-way only. No SOON, no 3-way, no other-side.
- Dogs 18–42¢ need tape **+2¢ already**. Favorites 58–72¢ need **+3¢ confirmation**.
- Stop −3¢ / trail arm +5¢ give-back 3¢ / reap **+8¢**.
- 15 minute buy cooldown after a cut. −$2 day circuit from the session mark.
- Max 2 × $2. $10 never trades.

Idle cash on an empty *qualified* tape is still correct. Inventing a mid-band scalp is how we paid the market maker all afternoon.

## v8 (superseded)

v7 would have **sold PHI at +8¢**. The paid trades were dimes, so v8 **trails** (arm +5¢, give back 3¢ from peak) and does not hard-reap. One 30s uptick is not a move — need the prior tick up too. 15m cooldown only after a **losing** cut. Skip books with OI < 5,000.

## v9 (superseded)

## v10 (superseded)

One loop (buyer), one watch (seller), one CoS TUI. Order lock. Session $2 circuit. Peak every 4s. TTR only LATER.

## v11 (live policy — GO.md in a fresh TUI)

Dogs **18–42¢ only** (no fav band). Loop **never sells**. `nohup` in GO.md. Watch owns every exit.

