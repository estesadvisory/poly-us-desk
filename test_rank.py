#!/usr/bin/env python3
"""v15 rank. python3 test_rank.py"""
from __future__ import annotations
import risk


def row(**kw):
    d = {
        "slug": "aec-mlb-mia-wsh-2026-08-29",
        "live": True,
        "ask": 0.52,
        "bid": 0.515,
        "spr": 0.005,
        "score": "0-0",
        "period": "Top 1st",
        "delta_c": 0.0,
    }
    d.update(kw)
    return d


def main():
    assert risk.VERSION == "v15"
    assert risk.MAX_OPEN == 2
    assert risk.rank(row()) is not None, "52c live 2-way must fire (no 18-42)"
    assert risk.rank(row(ask=0.37, bid=0.365)) is not None, "37c"
    assert risk.rank(row(ask=0.85, bid=0.84, spr=0.01)) is not None, "85c still tradable"
    assert risk.rank(row(slug="atc-epl-tot-new-tot")) is None, "3-way"
    assert risk.rank(row(live=False)) is None, "not live"
    assert risk.rank(row(ask=0.03, bid=0.025)) is None, "dust"
    assert risk.rank(row(ask=0.95, bid=0.94)) is None, "lock"
    assert risk.rank(row(spr=0.08, ask=0.50, bid=0.42)) is None, "wide"
    print("ok", risk.VERSION)


if __name__ == "__main__":
    main()
