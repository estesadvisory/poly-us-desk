#!/usr/bin/env python3
"""v16 rank. python3 test_rank.py"""
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
    assert risk.VERSION == "v17"
    assert risk.MAX_OPEN >= 10
    assert risk.RING_USD == 10.0
    assert risk.rank(row()) is not None, "flat first-ish print must fire"
    assert risk.rank(row(delta_c=None)) is not None, "no history still fires"
    soon = row(live=False, soon=True, minutes_to_start=10, ask=0.53, bid=0.52)
    assert risk.rank(soon) is not None, "SOON 12-88 must fire"
    soon45 = row(live=False, soon=True, minutes_to_start=40, ask=0.34, bid=0.33)
    assert risk.rank(soon45) is not None, "40m SOON must fire"
    assert risk.SOON_MIN >= 40
    assert risk.rank(row(live=False, soon=False, minutes_to_start=40, ask=0.34, bid=0.33)) is not None
    later = row(live=False, soon=False, minutes_to_start=80)
    assert risk.rank(later) is None, "LATER must not buy"
    assert risk.why_not(later) == "later"
    assert risk.why_not(row(ask=0.99, bid=0.98)) == "band"
    assert risk.why_not(row(delta_c=-1.0)) == "dump"
    overdue = row(live=True, soon=False, minutes_to_start=-36, ask=0.41, bid=0.40)
    assert risk.rank(overdue) is not None, "overdue NS treated live must fire"
    assert risk.rank(row(ask=0.37, bid=0.365, delta_c=1.0)) is not None, "37c uptick"
    assert risk.rank(row(ask=0.85, bid=0.84, spr=0.01)) is not None, "85c still tradable"
    assert risk.rank(row(slug="atc-epl-tot-new-tot")) is None, "3-way"
    assert risk.rank(row(live=False)) is None, "not live"
    assert risk.rank(row(ask=0.03, bid=0.025)) is None, "dust"
    assert risk.rank(row(ask=0.95, bid=0.94)) is None, "lock"
    assert risk.rank(row(spr=0.08, ask=0.50, bid=0.42)) is None, "wide"
    assert risk.rank(row(delta_c=-1.0)) is None, "dumping"
    assert risk.rank(row(delta_c=1.0, delta2_c=-2.5)) is None, "bounce"
    dog = risk.rank(row(ask=0.28, bid=0.275, spr=0.005, delta_c=1.0))
    mid = risk.rank(row(ask=0.50, bid=0.495, spr=0.005, delta_c=1.0))
    assert dog is not None and mid is not None
    assert dog > mid, "lower-fee dog should outrank 50c coin-flip"
    assert risk.watch_exit(0.50, 0.47, 0.50, True) == "EXIT_DOWN"
    assert risk.watch_exit(0.50, 0.52, 0.52, True) is None, "do not scratch +2c"
    assert risk.watch_exit(0.50, 0.53, 0.56, True) == "EXIT_UP"
    print("ok", risk.VERSION)


if __name__ == "__main__":
    main()
