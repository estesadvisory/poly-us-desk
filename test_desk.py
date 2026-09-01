#!/usr/bin/env python3
"""Supervisor command parser. python3 test_desk.py"""
from __future__ import annotations
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
    assert desk.parse_cmd("") is None
    assert desk.parse_cmd("nope") is None
    print("ok desk-commands")


if __name__ == "__main__":
    main()
