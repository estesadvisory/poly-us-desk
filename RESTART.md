# Restart (does not start the machine)

**Live version: v26** (this repo `VERSION`). Knobs: `desk.json`. Humans: start from [README.md](README.md).

In **one** Terminal (see `GO.md`):

```bash
cd /path/to/poly-us-desk
test -n "${POLY_ENV:-}" -o -f ~/.grok/secrets/polymarket-us.env || { echo "NO ENV"; exit 1; }
test "$(cat VERSION)" = "v26" || { echo "VERSION mismatch"; cat VERSION; exit 1; }
python3 desk.py --go
```

After a version bump: **`quit` → `git pull` → `python3 desk.py --go`**. Cold start without `--go` sits on HOLD.

Change a knob in the desk: `set clip_usd 1` (writes overlay and reloads). After a deposit: `reserve reset`.

Logs: `~/.grok/desk/logs/`. This file does not start the desk.
