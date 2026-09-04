# How to contribute

This repo is **Grok-first**. The live desk is Python. Grok (or another AI agent) is how the program gets better. Human and AI pull requests are both welcome. AI-written changes are **encouraged**, not a reason to reject a PR.

## If you want your own desk

**Fork** this repository and run your fork. Point `POLY_ENV` at **your** Polymarket US keys. Do not open a PR just to keep a personal copy, a private overlay, or your fills.

Your fork can track upstream `main` when you want our improvements. You can also ignore us and let your own Grok agent change your fork on whatever cadence you like.

## If you want to contribute here

1. Fork, then branch from current `main`.
2. Open a pull request against [estesadvisory/poly-us-desk](https://github.com/estesadvisory/poly-us-desk).
3. Say what changed and why. If an agent wrote it, say so — that is a plus.
4. Run `python3 test_desk.py` and `python3 test_rank.py` before you push.

We review PRs. We may ask for a smaller change or a follow-up issue. We do not require you to hide that Grok, Cursor, or another model wrote the diff.

### What we will merge

- Fixes, clearer docs, safer defaults, tests
- Policy changes that name the old failure (see [LESSONS.md](LESSONS.md)) and do not silently re-starve the tape
- Agent-authored refactors that keep the one-Terminal desk and the zero-LLM trade loop

### What we will not merge

- Secrets, `.env` files, fills, tape dumps, or anything from `~/.grok/desk`
- An LLM (Grok included) **inside** the buy/sell path. Grok improves **code**. Python places **orders**.
- VPN / “not a U.S. person” / polymarket.com paths
- Direct commits to `main` from outside this project’s operators

## For Grok and other agents

Read [AGENTS.md](AGENTS.md), then [DESIGN.md](DESIGN.md) and [LESSONS.md](LESSONS.md). Do not invent trading rules. Idle cash on an empty qualified tape is correct.

Prefer a GitHub issue, then a branch, then this PR. After merge, the operator restarts with `quit` → `git pull` → `python3 desk.py --go`.

## License

By opening a PR you agree the contribution is under the same [MIT](LICENSE) license as the rest of the repo.
