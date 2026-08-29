# poly-us-desk (v17)

Polymarket **US** micro desk. Private. **No secrets in this repo.**

Code: this git repo. State + logs: `~/.grok/desk` (override with `POLY_DESK`).
Secrets: 1Password EstesDevOps login `polymarket-us` → `~/.grok/secrets/polymarket-us.env`.

## Run (one Terminal)

```bash
cd ~/repos/poly-us-desk
test -f ~/.grok/secrets/polymarket-us.env || { echo "NO ENV"; exit 1; }
python3 desk.py          # research + seller; buys HOLD until you type go
```

Commands in that same terminal: `help` `status` `hold` `go` `reload` `skip <slug>` `books` `quit`

- `--go` — arm buys on start
- `--no-buy` — seller + research only (leftover tickets)
- `--paper` — no live orders

Iteration: `hold` → edit this repo → `reload` (or `quit` and run again).

Logs for later check-in: `~/.grok/desk/logs/` (`desk.log`, `events.jsonl`, `research.log`, `loop.log`, `watch.log`).

## Roles

- `desk.py` — supervisor / HUD / commands (no LLM)
- `research.py` — tape
- `loop.py` — only **buyer**
- `watch.py` — only **seller**

`$10` never trades. Clip $2. Working cash is the ticket cap. LIVE or SOON `aec-` 2-way, all operational US leagues.
Entry: not dumping. Exit: stop −3¢, trail +5¢. No 3-ways. No 2-ticket freeze.
