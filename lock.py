#!/usr/bin/env python3
"""Single loop, single watch, one order at a time. Agents do not trade."""
from __future__ import annotations
import atexit, fcntl, os, sys
from pathlib import Path

DESK = Path.home() / ".grok/desk"
ORDERS = DESK / "orders.lock"


def _alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def claim(name: str) -> None:
    DESK.mkdir(parents=True, exist_ok=True)
    pidf = DESK / f"{name}.pid"
    if pidf.exists():
        try:
            old = int(pidf.read_text().strip() or "0")
        except ValueError:
            old = 0
        if _alive(old) and old != os.getpid():
            print(f'{{"ok": false, "stage": "already_running", "name": "{name}", "pid": {old}}}')
            sys.exit(1)
    pidf.write_text(str(os.getpid()) + "\n")

    def _clear():
        try:
            if pidf.exists() and pidf.read_text().strip() == str(os.getpid()):
                pidf.unlink()
        except Exception:
            pass

    atexit.register(_clear)


class order_lock:
    """Exclusive buy/cut so loop and watch cannot double-submit."""

    def __enter__(self):
        DESK.mkdir(parents=True, exist_ok=True)
        self.fd = open(ORDERS, "a")
        fcntl.flock(self.fd, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        try:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
            self.fd.close()
        except Exception:
            pass
        return False
