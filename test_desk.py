#!/usr/bin/env python3
"""Supervisor command parser. python3 test_desk.py"""
from __future__ import annotations
import json
import tempfile
from pathlib import Path

import cfg
import desk


def main():
    assert desk.parse_cmd("help") == ("help", None)
    assert desk.parse_cmd("status") == ("status", None)
    assert desk.parse_cmd("hold") == ("hold", None)
    assert desk.parse_cmd("go") == ("go", None)
    assert desk.parse_cmd("reload") == ("reload", None)
    assert desk.parse_cmd("config") == ("config", None)
    assert desk.parse_cmd("skip aec-mlb-mia-wsh-2026-08-29") == (
        "skip",
        "aec-mlb-mia-wsh-2026-08-29",
    )
    assert desk.parse_cmd("set clip_usd 1") == ("set", ("clip_usd", "1"))
    assert desk.parse_cmd("set") == ("set", None)
    assert desk.parse_cmd("reserve reset") == ("reserve", "reset")
    assert desk.parse_cmd("") is None
    assert desk.parse_cmd("nope") is None
    assert "enough cash" in desk.say_hold("working $1.84 < clip_min $2.0").lower()
    assert "paused new buys" in desk.say_hold("operator hold").lower()
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "desk.json"
        val, path = cfg.set_overlay("clip_usd", "1", dest=dest)
        assert val == 1.0 and path == dest
        assert json.loads(dest.read_text())["clip_usd"] == 1.0
    print("ok desk-commands")


if __name__ == "__main__":
    main()
