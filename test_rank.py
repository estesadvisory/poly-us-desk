#!/usr/bin/env python3
"""v16 rank. python3 test_rank.py"""
from __future__ import annotations
import research
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
        "delta_c": 1.0,
    }
    d.update(kw)
    return d


def main():
    assert risk.VERSION == "v24"
    assert risk.MAX_OPEN >= 10
    assert risk.RING_USD == 7.0
    assert risk.MAX_DAY_LOSS == 5.0
    assert risk.TRAIL_ARM == 0.08
    assert risk.rank(row(delta_c=0.0)) is None, "LIVE flat snapshot must wait"
    assert risk.why_not(row(delta_c=0.0)) == "flat"
    assert risk.rank(row(delta_c=None)) is None, "no history must wait"
    assert risk.rank(row()) is not None, "LIVE +1c must fire"
    soon_flat = row(live=False, soon=True, minutes_to_start=10, ask=0.53, bid=0.52, delta_c=0.0)
    assert risk.rank(soon_flat) is None, "SOON with no uptick must wait"
    assert risk.why_not(soon_flat) == "flat"
    assert risk.rank(row(live=False, soon=True, minutes_to_start=10, ask=0.53, bid=0.52, delta_c=None)) is None
    soon = row(live=False, soon=True, minutes_to_start=10, ask=0.53, bid=0.52, delta_c=1.0)
    assert risk.rank(soon) is not None, "SOON with +1c must fire"
    soon45 = row(live=False, soon=True, minutes_to_start=40, ask=0.34, bid=0.33, delta_c=1.0)
    assert risk.rank(soon45) is not None, "40m ticking SOON must fire"
    assert risk.SOON_MIN >= 40
    assert risk.rank(row(live=False, soon=False, minutes_to_start=40, ask=0.34, bid=0.33, delta_c=1.0)) is not None
    later = row(live=False, soon=False, minutes_to_start=80)
    assert risk.rank(later) is None, "LATER must not buy"
    assert risk.why_not(later) == "later"
    assert risk.why_not(row(ask=0.99, bid=0.98)) == "band"
    assert risk.why_not(row(delta_c=-1.0)) == "dump"
    assert risk.why_not(row(period="NS", delta_c=1.0, minutes_to_start=-36)) == "not_started"
    assert risk.rank(row(period="NS", delta_c=1.0, minutes_to_start=-36)) is None
    assert risk.rank(row(live=False, soon=True, period="NS", minutes_to_start=-10, ask=0.41, bid=0.40, delta_c=1.0)) is None
    assert risk.rank(row(live=False, soon=True, period="NS", minutes_to_start=20, ask=0.41, bid=0.40, delta_c=1.0)) is not None
    overdue = row(live=True, soon=False, minutes_to_start=-36, ask=0.41, bid=0.40, period="Q1", delta_c=1.0)
    assert risk.rank(overdue) is not None, "overdue in-game must fire"
    assert research.event_flags(True, False, 10, "NS") == (False, False)
    assert research.event_flags(True, False, -10, "NS") == (False, False)
    assert research.event_flags(False, False, 30, "NS") == (False, True)
    assert research.event_flags(False, False, -36, "NS") == (False, True)
    assert research.event_flags(False, False, -36, "Q1") == (True, False)
    assert risk.league("aec-cs2-mak-unn-2026-08-29") == "cs2"
    import intent

    tape = {
        "live": [
            {
                "slug": "aec-cs2-aaa-2026-08-29",
                "live": True,
                "ask": 0.40,
                "bid": 0.39,
                "spr": 0.01,
                "delta_c": 1.0,
            },
            {
                "slug": "aec-cs2-bbb-2026-08-29",
                "live": True,
                "ask": 0.35,
                "bid": 0.34,
                "spr": 0.01,
                "delta_c": 1.0,
            },
        ]
    }
    picked = intent.pick_buy(tape, set(), {"aec-cs2-aaa-2026-08-29"})
    assert picked is not None and picked[1]["slug"] == "aec-cs2-bbb-2026-08-29"
    assert intent.pick_buy(tape, set(), {"aec-cs2-aaa-2026-08-29", "aec-cs2-bbb-2026-08-29"}) is None
    assert risk.why_not(row(ask=0.14, bid=0.13)) == "band", "12-16c wrecks are out"
    assert risk.rank(row(ask=0.37, bid=0.365, delta_c=1.0)) is not None, "37c uptick"
    assert risk.rank(row(ask=0.85, bid=0.84, spr=0.01, delta_c=1.0)) is not None, "85c still tradable"
    cheap = risk.rank(row(ask=0.20, bid=0.195, spr=0.005, delta_c=1.0))
    mover = risk.rank(row(ask=0.38, bid=0.375, spr=0.005, delta_c=2.0))
    assert cheap is not None and mover is not None
    assert mover > cheap, "ticking 38c should beat a 20c edge"
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
    assert risk.watch_exit(0.50, 0.47, 0.50, True) is None, "3c wiggle is hold"
    assert risk.watch_exit(0.50, 0.40, 0.50, True) == "EXIT_DOWN", "10c hole"
    assert risk.watch_exit(0.50, 0.42, 0.50, True, prev_bid=0.50) == "EXIT_DOWN", "8c cliff"
    assert risk.watch_exit(0.50, 0.52, 0.52, True) is None, "do not scratch +2c"
    assert risk.watch_exit(0.50, 0.55, 0.56, True) is None, "+6c peak is not armed"
    assert risk.watch_exit(0.50, 0.55, 0.59, True) == "EXIT_UP", "peak +9 giveback 3"
    assert risk.watch_exit(0.53, 0.51, 0.60, True) is None, "trail must not sell through entry"
    assert risk.watch_exit(0.53, 0.50, 0.60, True) is None, "3c from entry is not a crash"
    assert risk.should_ttr(50) is False
    assert risk.should_ttr(-5) is True
    print("ok", risk.VERSION)


if __name__ == "__main__":
    main()
