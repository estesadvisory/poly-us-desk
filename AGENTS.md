# Agent instructions (poly-us-desk)

This repository is the **local source of truth** for poly-us-desk work in the Grok CLI.
Web UI Grok Projects do **not** sync here. Continuity is: **disk + this file** (+ Memory MCP when used).

- **Local path:** `~/repos/poly-us-desk`
- **GitHub:** https://github.com/estesadvisory/poly-us-desk (private)

## What this repo is

Private Polymarket **US** micro desk. Python supervisor + buyer + seller + tape. **Zero LLM in the loop.** Live version is the `VERSION` file (v25 as of onboard). Trading knobs: `desk.json`.

Code is this git repo. Runtime state and logs live under `~/.grok/desk` (override with `POLY_DESK`). Secrets never live here.

## Portfolio process (shared)

Cross-repo standards live in **[estesadvisory/portfolio-ops](https://github.com/estesadvisory/portfolio-ops)** (`docs/PHILOSOPHY.md`, `docs/OPS.md`, `docs/DELIVERY.md`, `docs/ISSUE_FIRST.md`).

1. **Delivery:** multi-step work → issue → **branch → PR → review → merge** (not direct `main`). See `docs/DELIVERY.md`.
2. **Issue-first:** announce `Tracking: owner/repo#N` (skill `issue-first`).
3. **Issue bodies** are source of truth; update bodies when closing.
4. **Priority in titles:** `[P0]`…`[P3]`; park as `[P3 / parked]` with unpark criteria.
5. **Small PRs**; `Refs #N` / `Fixes #N` on implementing commits.
6. **After PR:** `/review --pr N` → fix bugs on PR → agent merge (unless `hold` / `wait` / `don't merge`). File issues only for deferred findings.
7. **Never** embed PATs/tokens in `git remote` URLs — clean HTTPS + `gh auth` keyring (or SSH).
8. **No silent product breakage** across repos; file issues first for risky changes.
9. **Session harvest** after meaningful work: short MCP summary — portfolio-ops `docs/SESSION_HARVEST.md`.

## Repo-specific non-negotiables

- **No secrets in git.** Materialize from 1Password EstesDevOps login `polymarket-us` → `~/.grok/secrets/polymarket-us.env`. Do not add a repo `.env.op.tpl` / `secrets-onboard` inject path unless a later ticket says so.
- Do not commit fills, session JSON, tape dumps, or anything under `~/.grok/desk`.
- Run in **one Terminal**: `python3 desk.py --go`. Do not `nohup` `loop.py` / `watch.py`. Do not run `hum.py` / `intent.py` / `trade.py buy|cut` by hand.
- After a version bump: `quit` → `git pull` → `python3 desk.py --go`. Cold start without `--go` sits on HOLD.
- **Do not invent trading rules.** Policy lives in `DESIGN.md` + `VERSION`. Idle cash on an empty qualified tape is correct; mid-band scalps are how the fee bill happens.
- Private product. Do not publish this repo, paste venue keys, or mix this live desk with the paper-only `portfolio-ops/market-run` path.
- US desk only. Do not open polymarket.com or use a VPN / “not a U.S. person” path from agent work.

## Useful links

- [README.md](README.md) · [DESIGN.md](DESIGN.md) · [GO.md](GO.md) · [LESSONS.md](LESSONS.md)
- Hub onboard: https://github.com/estesadvisory/portfolio-ops/issues/156
