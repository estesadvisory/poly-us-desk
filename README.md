# poly-us-desk

A Polymarket **US** micro desk that any AI agent can operate and improve. Python watches sports markets, buys a small ticket when a book qualifies, and sells on a stop or a trail. **No model places the orders.** An agent improves the code on a regular basis while the desk keeps running.

**You can lose the money you put on the venue.** This is not financial advice, not a product for sale, and not a “set it and forget it” money machine. Fees on Polymarket US are large enough that tiny scalps usually lose. Sitting in cash when nothing qualifies is the correct behavior.

**United States venue only.** Use this with a Polymarket **US** account. Do not use a VPN or a “not a U.S. person” workaround with this code.

Want your own copy? **[Fork the repo](https://github.com/estesadvisory/poly-us-desk/fork).** Pull requests (including ones an AI agent wrote) are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

License: [MIT](LICENSE). See [SECURITY.md](SECURITY.md) before you put keys on disk.

## How we use it

This is the loop we actually run:

1. **Leave the desk on.** One Terminal, all day: `python3 desk.py --go`. Python is the trader. Do not put an AI agent in that process.
2. **Let an agent improve the program.** On a regular basis (after a session, a losing day, or when something looks wrong) any AI agent reads `DESIGN.md`, `LESSONS.md`, the HUD, and `~/.grok/desk/logs/`, then ships a small change through a GitHub issue and pull request.
3. **Restart only after a merge.** In the desk window: `quit` → `git pull` → `python3 desk.py --go`. Starting without `--go` leaves buys paused.
4. **Do not invent rules mid-session.** Live policy is `desk.json` + `DESIGN.md` + `VERSION`. History lives in `LESSONS.md` so the next session does not repeat a starved tape or a fee-bill scalp.

The point: **the desk runs unattended; the agent edits the repo, not the live orders.** Grok, Claude, Cursor, Codex, or anything else is fine.

New to this? Copy a ready-made prompt from [PROMPTS.md](PROMPTS.md) and paste it into any AI chat.

If you only want a personal desk, fork and point your agent at the fork. You do not need a PR for that.

## What you need

1. A Mac or Linux computer with **Python 3** (3.10 or newer).
2. A **Polymarket US** account with cash you can afford to lose.
3. API keys from the [Polymarket US developer portal](https://polymarket.us/developer) (a key id and a secret). Official walkthrough: [Get your API keys](https://docs.polymarket.us/getting-started/quickstart).
4. Comfort typing a few commands in Terminal. You do not need to be a programmer.

## Set up (once)

```bash
git clone https://github.com/estesadvisory/poly-us-desk.git
cd poly-us-desk
```

Create the key at [polymarket.us/developer](https://polymarket.us/developer) after you have a verified Polymarket US account ([step-by-step](https://docs.polymarket.us/getting-started/quickstart)). The secret is shown **once** — copy it immediately.

Copy the example env file and fill in **your** keys. Do not email or commit that file.

```bash
cp env.example ~/.polymarket-us.env
# edit ~/.polymarket-us.env in any text editor
# put the key id and secret on the two lines — no quotes needed
export POLY_ENV="$HOME/.polymarket-us.env"
```

The desk also looks at `~/.grok/secrets/polymarket-us.env` if you do not set `POLY_ENV`. Keep that file off git either way.

Paper mode (no live orders) is available: add `--paper` when you start.

## Run (one Terminal window)

```bash
cd poly-us-desk
export POLY_ENV="$HOME/.polymarket-us.env"   # if you used the path above
python3 desk.py --go
```

`--go` means “you may buy.” If you start without it, the desk watches and can sell, but it will not open new tickets until you type `go`.

Leave that window open. Type commands there. Do not start extra copies of the buyer or seller by hand.

### What you will see

A short status block every few seconds:

- **BUYING** — new tickets are allowed (the desk may still wait; that is normal).
- **HOLD** — new buys are paused. The line under `last HOLD` says why, in plain language.
- **BP** — buying power (cash the venue says you have).
- **work** — cash the desk is allowed to spend after it parks a profit reserve.
- **open** — tickets it is already in.

If it says you do not have enough cash for a ticket, deposit on the venue, or type `set clip_min_usd 0.5` (smaller tickets cost more in fees).

## Commands you can type

| Type this | What it does |
|-----------|----------------|
| `help` | Print this list |
| `status` | Show cash, open tickets, and why it is waiting |
| `hold` | Pause new buys. Open tickets can still be sold. |
| `go` | Allow buys again |
| `reload` | Restart the workers after you change files |
| `skip <market-id>` | Do not buy that market again this session |
| `books` | Refresh the account snapshot |
| `config` | Show the live settings |
| `set <name> <number>` | Change a setting now (see below) |
| `reserve reset` | After you **deposit** money, reset the profit-reserve line |
| `quit` | Stop everything |

Examples:

```text
set clip_usd 1
set ask_hi 0.70
reserve reset
```

`set` writes a local overlay (`~/.grok/desk/desk.json`, not this git repo) and reloads. Type `config` to confirm.

## How it decides (short)

Defaults live in `desk.json`. You can change them with `set` without editing the file.

- Ticket size is **$2**, or whatever cash you have left down to **$1**.
- It only looks at two-way US sports markets (`aec-`), live or about to start.
- Ask between **20¢ and 75¢**, tight spread, bid must have **ticked up**.
- Stop: down **10¢** from entry, or **8¢** in one print.
- Winners: trail after **+8¢**, give back **3¢**. It will not sell a winner at or below the entry price.
- If this session is down **$5**, it stops buying.
- **10%** of profit above a waterline is parked so it is not all re-risked. After a deposit, type `reserve reset`.

Idle cash on an empty tape is expected. That is not a crash.

## After you update the code

In the desk window: `quit`. Then:

```bash
git pull
python3 desk.py --go
```

Starting without `--go` after an update leaves buys paused.

## Files (you can ignore most of these)

| Where | What |
|-------|------|
| This git repo | The program |
| `desk.json` | Default settings |
| `~/.grok/desk/` | Runtime state and logs (not git) |
| `$POLY_ENV` | Your API keys (not git) |

Developer notes: [DESIGN.md](DESIGN.md) (how it is built), [GO.md](GO.md) (operator start), [LESSONS.md](LESSONS.md) (why we do not revert old rules). Any agent: [AGENTS.md](AGENTS.md). Example prompts: [PROMPTS.md](PROMPTS.md). Contribute or fork: [CONTRIBUTING.md](CONTRIBUTING.md).
