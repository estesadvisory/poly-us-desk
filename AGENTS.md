# Agent instructions (poly-us-desk)

This repository is **Grok-first**. Grok (or another agent) improves the code on a regular basis. Python trades. Runtime state is **not** in git. Humans and other contributors: [CONTRIBUTING.md](CONTRIBUTING.md) — fork for your own desk; PRs (including AI-written) are welcome.

- **GitHub:** https://github.com/estesadvisory/poly-us-desk
- **Local path (typical):** `~/repos/poly-us-desk`

## What this repo is

Polymarket **US** micro desk operated with Grok. Python supervisor + buyer + seller + tape. **Zero LLM in the trade loop** — do not call Grok (or any model) from `loop.py` / `watch.py` / `intent.py`. Live version is the `VERSION` file. Trading knobs: `desk.json` (plus optional overlay `~/.grok/desk/desk.json`).

How the humans run it: leave `python3 desk.py --go` up; you ship improvements via issue → PR; they `quit` → `git pull` → `python3 desk.py --go`. Details: [README.md](README.md#how-we-use-it-grok).

Code is this git repo. Runtime state and logs live under `~/.grok/desk` (override with `POLY_DESK`). Secrets never live here. Point `POLY_ENV` at a file that contains `POLYMARKET_KEY_ID` and `POLYMARKET_SECRET_KEY` (see `env.example`).

## Delivery

Multi-step work: issue → branch → PR → review → merge (not direct `main`). Announce `Tracking: owner/repo#N`. Priority in titles: `[P0]`…`[P3]`. Implementing commits: `Refs #N` / `Fixes #N`. After PR: review, fix bugs on the same PR, then merge unless the human said `hold` / `wait` / `don't merge`. Never embed PATs in `git remote` URLs.

## Repo-specific non-negotiables

- **No secrets in git.** Do not commit `.env`, fills, session JSON, tape dumps, or anything under `~/.grok/desk`.
- Run in **one Terminal**: `python3 desk.py --go`. Do not `nohup` `loop.py` / `watch.py`. Do not run `hum.py` / `intent.py` / `trade.py buy|cut` by hand.
- After a version bump: `quit` → `git pull` → `python3 desk.py --go`. Cold start without `--go` sits on HOLD.
- **Do not invent trading rules.** Live policy: `DESIGN.md` + `desk.json` + `VERSION`. History / never-again: `LESSONS.md` (not live). Idle cash on an empty qualified tape is correct; mid-band scalps are how the fee bill happens.
- US desk only. Do not open polymarket.com or use a VPN / “not a U.S. person” path from agent work.
- Do not paste venue keys. Do not mix this live desk with a paper-only market-run path.

## Useful links

- [README.md](README.md) (humans) · [CONTRIBUTING.md](CONTRIBUTING.md) · [DESIGN.md](DESIGN.md) · [GO.md](GO.md) · [LESSONS.md](LESSONS.md) · [RESTART.md](RESTART.md) · [SECURITY.md](SECURITY.md)
