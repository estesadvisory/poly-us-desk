# Restart (does not start the machine)

**Live version: v25** (this repo `VERSION`). Knobs: `desk.json`.

In **one** Terminal (see `GO.md`):

```bash
cd ~/repos/poly-us-desk
test -f ~/.grok/secrets/polymarket-us.env || { echo "NO ENV"; exit 1; }
test "$(cat VERSION)" = "v25" || { echo "VERSION mismatch"; cat VERSION; exit 1; }
python3 desk.py --go
```

After a version bump: **`quit` → `git pull` → `python3 desk.py --go`**. Cold start without `--go` sits on HOLD.

Edit knobs → type `reload` (or `quit` and run again). Overlay: `~/.grok/desk/desk.json`. After a deposit: delete `~/.grok/desk/reserve.json`.

Logs: `~/.grok/desk/logs/`. This file does not start the desk.
