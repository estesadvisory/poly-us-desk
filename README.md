# poly-us-desk (v11)

Polymarket **US** micro desk. Private. **No secrets in this repo.**

Runtime copy: `~/.grok/desk`. Secrets: 1Password EstesDevOps login `polymarket-us` → `~/.grok/secrets/polymarket-us.env` (never commit).

## Roles

- `loop.py` — only **buyer**
- `watch.py` — only **seller**
- One CoS TUI — talks; does not place orders

Start card: [`GO.md`](./GO.md)

Policy: LIVE 2-way dogs 18–42¢, two upticks. No favorites. `$10` never trades.
