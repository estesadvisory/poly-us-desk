# Lessons — decision log (not live policy)

**Live policy is v26.** Read `DESIGN.md` + `desk.json` + `VERSION`. Knobs change without a version bump; this file is *why* we do not go backwards.

PnL source: `GET /v1/portfolio/activities` (taker fee already in cost). Not Chrome cash, not chat memory. Fills stay under `~/.grok/desk` (never git).

## Never again

Do not ship these without a new issue that names the old failure:

| Do not | Why | When |
|--------|-----|------|
| Last-trade + live-score AND-gates | Tape went empty. Afternoon GO: zero fills. | v12 |
| 18–42¢-only / 12–88 shrink as a starve | Missed live dogs that paid; then bought dying 12–16¢ wrecks. Band is **exit-able**, not a religion. | v11, v23 |
| 2-ticket cap | Idle cash sat while the tape had books. Working cash is the cap. | v15–v16 |
| Intent running `research.py --hot` | Overwrote the 52-league crawl with a handful of CS2 slugs. Research child owns the tape. | v20 |
| Skip-on-cut hiding rows from the tape | Skip blocks **buys**, not listing. | v21 |
| League/sport **cold** (≥2 losses, 0 wins → sit the sport) | Starved CS2/Valorant/NFL after a bad card. Per-slug skip + 1 ticket/slug is enough. | v20 in, v22 out |
| LIVE first-print (`delta_c = 0`) | Flat snapshot + taker fee. 08-31 bleed. LIVE and SOON both need an uptick. | v19 in, v24 out |
| Trail +5/−3 | Net ~+2¢, fees ate it (`54→60 +$0.11` fees `$0.11`). Trail arms at **+8¢**. | v24 |
| Hard $7 / $10 ring while BP is small | Working $1.74 < $2 clip → HOLD, no trades. Ring floor is **$0**; 10% profit reserve ratchets park. | v23, v25 |
| Full clip only (no `clip_min`) | Working $1.84 sat idle. v26 buys `min(clip, working)` down to $1. | v25 |
| 3-ways (`atc-`) | Levante −$3.44. Banned. | 08-29 |
| `nohup` loop/watch; hand `hum` / `intent` / `trade buy\|cut` | One Terminal: `python3 desk.py --go`. | v16 |
| Restart after a version bump **without** `--go` | Cold start sits on operator HOLD. Recipe: `quit` → `git pull` → `python3 desk.py --go`. | v19 docs |
| Inventing a mid-band scalp on an empty qualified tape | Fee bill. Idle cash is correct. | 08-29 |

HUD **BUYING** + last action HOLD is usually the **session-loss circuit**, not the operator HOLD file.

## What paid vs what bled

Winners are **live (or ticking SOON) names already moving**, then a trail that can clear fees. Not 1¢ scalps, not flat first prints, not 12–16¢ wrecks.

| Day | Closed | PnL | Note |
|-----|--------|-----|------|
| 08-28 | — | PHI–LAA 19.5→92 **+$10.43**; AZ–SF 5.7→34 +$4.88 (dust — do not revive sub-20) | Prototype runner |
| 08-29 | 36 | **−$10.39** | 3-ways, 50¢ coin-flips, −3¢ stop sold winners (CHI–TEN). Real wins: KC–CLE 18→43 **+$2.57**, Mayo ATP +$0.30 |
| 08-30 | 24 | **−$5.90** | 12–16¢ LIVE first prints (Vandewinkel 13→3, Keys 12→1). Runner: Kecmanovic 38→73 **+$1.72**, WNBA 70→94 +$0.64 |
| 08-31 | 15 | **−$6.61** | Flat LIVE snapshots; trail +5 scratched into fees; overdue NS bought; four ATP tickets until working $1. Circuit −$5.94 / $5 |

US taker fee ≈ `0.06 × p × (1−p)` ≈ **1.5¢/side at 50¢**, ~3¢ round-trip. A +1¢/−1¢ scalp cannot have positive EV. CWS 08-29 sold at entry: 100% fees.

## Version log (v11 → v26)

| Ver | Issue | Keep | Drop / lesson |
|-----|-------|------|----------------|
| v11 | #1 | BBO fire, one buyer / one seller | 18–42-only (later dropped) |
| v12 | #3 | — | Last-trade + score gates **starved** |
| v13 | #5 | All US leagues, bid ticks | — |
| v14 | — | Reject dumping bids | — |
| v15 | — | 12–88 exit-able | Rank that preferred 50¢ fee-max; 2-ticket freeze |
| v16 | #7 | Terminal `desk.py`, HUD, HOLD/go | CoS TUI / `nohup` |
| v17 | #9 | SOON ≤45m, MAX_OPEN=20 | 2-ticket cap |
| v18 | #11 | Trail never sells through entry; no pregame TTR | — |
| v19 | #13 | SOON needs `delta_c > 0`; `--go` in docs | LIVE first-print still allowed (later dropped) |
| v20 | #15 | Intent must not `--hot`; 1 ticket/league | Cold leagues (later dropped) |
| v21 | #17 | Stop −10¢ / −8¢ cliff; skip ≠ hide; `--hot` keeps rows | −3¢ stop sold winners |
| v22 | #21 | — | League/sport **cold** flag |
| v23 | #23 | Park $7 (later $0); no league slot; band **20–88¢**; rank 25–70 playable | 12–16¢ wrecks |
| v24 | #25 | LIVE **and** SOON need uptick; leftover NS not a buy; trail **+8/−3** | First-print lottery |
| v25 | #27 | `desk.json` knobs; ring floor **$0**; 10% profit reserve ratchet | Hardcoded $7 ring (working < clip) |
| v26 | #31 | `set` / `reserve reset`; `clip_min_usd`; ask **20–75¢**; public-safe docs | HOLD when working < full clip; vault names in README |

## 08-29 morning sample (fee exhibit)

13 closed that morning were all red (**−$6.37**), including Levante 3-way **−$3.44** and CWS sold at entry. Kept here so we do not re-learn that a scratch is a fee bill. Full day closed 36 / −$10.39 (ledger).

## Pre-v11 (superseded, one line each)

v7–v10: TUI, 18–42 dogs, −3¢ stop, +8¢ reap, `nohup`. PHI would have been sold at +8¢. v8 introduced trail. Do not restore.

## How to continue (next session)

1. `AGENTS.md` → `DESIGN.md` → `desk.json` → `GO.md`. Humans: `README.md` (Grok run loop). Fork / PR: `CONTRIBUTING.md`
2. This file only for *why not* to revert
3. Runtime: `~/.grok/desk` (`ledger.md`, `STATUS.md`, `reserve.json`). After a **deposit**, delete `reserve.json`
4. Change a knob: type `set <knob> <value>` in the desk, or edit `desk.json` / overlay → `reload`. After a deposit: `reserve reset`. Version bump only for code/policy, not ring
5. Leave the desk running. Grok improves the repo on a regular basis (issue → PR). After merge: `quit` → `git pull` → `python3 desk.py --go`
