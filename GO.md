# Run in **one** Terminal. Not Cursor. Not a Grok TUI.

You are sitting at a shell. Python trades. You type commands.

## Start

```bash
cd ~/repos/poly-us-desk
test -f ~/.grok/secrets/polymarket-us.env || { echo "NO ENV"; exit 1; }
test "$(cat VERSION)" = "v24" || { echo "VERSION mismatch"; cat VERSION; exit 1; }
python3 desk.py --go
```

After a version bump: **`quit` → `git pull` → `python3 desk.py --go`**. Do not restart on HOLD and walk away. Cold start without `--go` still pauses buys until you type `go`.

```bash
python3 desk.py --go          # research + seller + buys armed
python3 desk.py               # buys HOLD until you type go
python3 desk.py --no-buy      # leftover / watch-only
python3 desk.py --paper       # no live orders
```

Do **not** `nohup` `loop.py` / `watch.py` by hand. Do **not** run `hum.py` / `intent.py` / `trade.py buy|cut` by hand.

## Commands

| Type | Effect |
|------|--------|
| `status` | version, git SHA, BP, working, open, live/soon/later, why |
| `hold` | pause new buys (seller stays up) |
| `go` | resume buys |
| `reload` | restart children after you edit this repo |
| `skip <slug>` | never buy that market this session |
| `books` | refresh venue snapshot |
| `quit` | stop everything (Ctrl-C also) |

## Edit → halt → restart

1. `hold` (optional, stops new buys immediately)
2. Edit files in `~/repos/poly-us-desk` (Cursor is fine)
3. `reload` in the desk terminal — children exec the new code
4. Or `quit`, then `python3 desk.py` again

Do not edit a running child and expect it to pick up changes without `reload` / `quit`.

## Logs (for a later Cursor check-in)

`~/.grok/desk/logs/`

- `events.jsonl` — structured start/stop/cmd/child_exit
- `desk.log` — same in one line per event
- `research.log` `loop.log` `watch.log` — child stdout

## Book / policy

- `books.json` — `open: []` means flat
- `$7` never trades. Clip $2. Working = BP − 7 (ticket cap, not a league-slot freeze).
- LIVE or ticking SOON (≤45m) `aec-`, all US sports, 20–88¢ book. Best book wins, any league. LIVE and SOON need a bid uptick. Leftover NS is not a buy.
- Session circuit −$5 from this GO (not operator HOLD). `hold` / missing `--go` is the only operator pause.
- Stop −10¢ or −8¢ in one print. 3¢ wiggle is hold. Trail +8/−3, never sell a winner at/under entry.

US only. Never print secrets.
