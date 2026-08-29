# poly-us-desk (v13)

Polymarket **US** micro desk. Private. **No secrets in this repo.**

Runtime copy: `~/.grok/desk`. Secrets: 1Password EstesDevOps login `polymarket-us` → `~/.grok/secrets/polymarket-us.env` (never commit).

## Roles

- `loop.py` — only **buyer**
- `watch.py` — only **seller**
- One CoS TUI — talks; does not place orders

Start card: [`GO.md`](./GO.md)

Policy: LIVE 2-way dogs 18–42¢, **+2¢ bid tick** (v11 fire path). No 3-way, no 43–57, no 0–0 Q1. `$10` never trades.
