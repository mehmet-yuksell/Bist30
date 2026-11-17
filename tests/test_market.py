"""market.py için testler: seans saati ve önbellek zaman dilimi (Europe/Istanbul)."""

import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from market import TZ, cache_slot, in_session, market_open, next_open, provisional


def at(day: int, hour: int, minute: int = 0) -> datetime:
    # Kasım 2026: 16 Pazartesi, 17 Salı, 20 Cuma, 21 Cumartesi
    return datetime(2026, 11, day, hour, minute, tzinfo=TZ)


def test_session_hours():
    assert not in_session(at(17, 9, 59))
    assert in_session(at(17, 10, 0))
    assert in_session(at(17, 18, 9))
    assert not in_session(at(17, 18, 10))
    assert not in_session(at(21, 12))  # cumartesi


def test_slot_changes_every_15_minutes_in_session():
    assert cache_slot(at(17, 10, 0)) == cache_slot(at(17, 10, 14))
    assert cache_slot(at(17, 10, 14)) != cache_slot(at(17, 10, 15))
    assert cache_slot(at(17, 14, 0)) == "2026-11-17#16"


def test_slot_keeps_refreshing_until_close_data_settles():
    # 18:10-18:40 arası gecikmeli kapanış verisi için yenileme sürer
    assert cache_slot(at(17, 18, 20)) != cache_slot(at(17, 18, 35))
    assert cache_slot(at(17, 18, 40)).startswith("kapali")


def test_slot_constant_outside_session_until_next_open():
    evening = cache_slot(at(17, 19, 0))
    assert evening == cache_slot(at(18, 9, 59))
    assert evening != cache_slot(at(18, 10, 0))
    # cuma akşamından pazartesi açılışına kadar aynı
    assert cache_slot(at(20, 19)) == cache_slot(at(21, 12)) == cache_slot(at(23, 9, 30))


def test_next_open_skips_weekend():
    assert next_open(at(20, 19)) == at(23, 10)
    assert next_open(at(17, 8)) == at(17, 10)


def test_market_open_requires_todays_data():
    assert market_open(at(17, 12), date(2026, 11, 17))
    # resmî tatil: saat seans içinde ama son veri dünden
    assert not market_open(at(17, 12), date(2026, 11, 16))
    assert not market_open(at(17, 18, 30), date(2026, 11, 17))


def test_provisional_until_close_data_settles():
    assert provisional(at(17, 12), date(2026, 11, 17))
    assert provisional(at(17, 18, 30), date(2026, 11, 17))
    assert not provisional(at(17, 18, 45), date(2026, 11, 17))
    assert not provisional(at(17, 12), date(2026, 11, 16))
