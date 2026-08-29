#!/usr/bin/env python3
"""v14 rank gates. python3 test_rank.py"""
from __future__ import annotations
import risk


def dog(**kw):
    row = {
        "slug": "aec-mlb-phi-laa-2026-08-28",
        "live": True,
        "ask": 0.20,
        "bid": 0.19,
        "spr": 0.01,
        "oi": 20000,
        "bid_depth": 10,
        "delta_c": 2.5,
        "delta2_c": 0.5,
        "score": "3-1",
        "period": "Bot 4th",
    }
    row.update(kw)
    return row


def main():
    assert risk.VERSION == "v14"
    assert risk.rank(dog()) is not None, "PHI-style live dog must fire"
    assert risk.rank(dog(delta_c=0.0)) is not None, "flat live dog must fire"
    assert risk.rank(dog(ask=0.37, delta_c=0.0, score="0-0", period="Top 1st")) is not None, "MLB 1st 0-0 37c"
    assert risk.rank(dog(slug="atc-epl-tot-new-2026-08-29-tot")) is None, "3-way"
    assert risk.rank(dog(ask=0.50, bid=0.49, spr=0.01)) is None, "coin-flip"
    assert risk.rank(dog(ask=0.61)) is None, "favorite"
    assert risk.rank(dog(score="0-0", period="Q1")) is None, "0-0 Q1 football"
    assert risk.rank(dog(delta_c=-1.0)) is None, "dumping"
    assert risk.rank(dog(live=False)) is None, "not live"
    assert risk.rank(dog(spr=0.03)) is None, "wide"
    assert risk.rank(dog(score=None, period="Bot 4th")) is not None, "missing score mid-game"
    print("ok", risk.VERSION)


if __name__ == "__main__":
    main()
