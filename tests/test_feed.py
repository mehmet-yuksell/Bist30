"""feed.py için testler: Yahoo hatasında son başarılı veriye dönüş ve yenileme sınırı.

Yahoo'ya gidilmez; data.py'nin indirme fonksiyonları sahte fonksiyonlarla değiştirilir.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import feed
from data import DataFetchError


@pytest.fixture(autouse=True)
def fresh_state():
    feed._state.clear()
    feed._batch.clear()
    feed._single.clear()
    yield
    feed._state.clear()


def _fake(func):
    return SimpleNamespace(__wrapped__=func)


def test_batch_falls_back_to_last_good_data(monkeypatch):
    tickers = ("AAA", "BBB")
    good = {t: pd.DataFrame({"Close": [1.0]}) for t in tickers}
    monkeypatch.setattr(feed, "get_multiple_price_histories", _fake(lambda t: good))
    first = feed.batch(tickers)
    assert not first.stale

    def broken(_):
        raise DataFetchError("ağ hatası")

    monkeypatch.setattr(feed, "get_multiple_price_histories", _fake(broken))
    feed.request_refresh()  # yeni anahtar: önbellekten değil, yeniden indirilir
    second = feed.batch(tickers)

    assert second.stale
    assert second.data is not None and set(second.data) == set(tickers)
    assert second.fetched_at == first.fetched_at


def test_partial_batch_counts_as_failure(monkeypatch):
    tickers = tuple(f"T{i}" for i in range(10))
    monkeypatch.setattr(feed, "get_multiple_price_histories",
                        _fake(lambda t: {"T0": pd.DataFrame({"Close": [1.0]})}))
    with pytest.raises(DataFetchError):  # önceki başarılı veri yok -> hata yukarı çıkar
        feed.batch(tickers)


def test_single_without_previous_data_raises(monkeypatch):
    def broken(*_):
        raise DataFetchError("veri yok")

    monkeypatch.setattr(feed, "get_price_history", _fake(broken))
    with pytest.raises(DataFetchError):
        feed.single("THYAO", pd.Timestamp("2025-01-01").date(), pd.Timestamp("2026-01-01").date())


def test_refresh_is_rate_limited():
    assert feed.request_refresh() == 0
    wait = feed.request_refresh()
    assert 0 < wait <= feed.REFRESH_COOLDOWN_SECONDS
    assert feed._state()["nonce"] == 1
