"""Piyasa saatine göre güncel tutulan veri katmanı (data.py'nin üzerine, onu değiştirmeden).

- data.py'deki indirme fonksiyonları kendi 1 saatlik önbellekleriyle değil, `__wrapped__`
  ile doğrudan çağrılır; önbelleği burada tutulur ve anahtarı market.cache_slot'tur:
  seansta 15 dakikada bir, seans dışında bir sonraki açılışa kadar aynı veri.
- "Şimdi yenile" anahtara bir sayaç ekler (en fazla 2 dakikada bir, tüm kullanıcılar için).
- İndirme başarısız olursa ya da veri boş/eksik gelirse son başarılı veri döner (stale=True).
"""

import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date, datetime

import pandas as pd
import streamlit as st

import market
from data import DataFetchError, get_multiple_price_histories, get_price_history

REFRESH_COOLDOWN_SECONDS = 120
MIN_BATCH_COVERAGE = 0.5  # 100 hissenin yarısından azı geldiyse indirme başarısız sayılır
MAX_SINGLE_FALLBACKS = 50


@dataclass
class Feed:
    data: object
    fetched_at: datetime
    stale: bool

    def age_minutes(self) -> int:
        return max(0, int((market.now() - self.fetched_at).total_seconds() // 60))


@st.cache_resource
def _state() -> dict:
    """Süreç genelinde paylaşılan durum: yenileme sayacı ve son başarılı veriler."""
    return {"nonce": 0, "last_refresh": 0.0, "last_good": OrderedDict()}


def _key() -> str:
    return f"{market.cache_slot(market.now())}|{_state()['nonce']}"


@st.cache_data(max_entries=3, ttl=24 * 3600, show_spinner=False)
def _batch(tickers: tuple[str, ...], key: str) -> tuple[dict, datetime]:
    data = get_multiple_price_histories.__wrapped__(tickers)
    if len(data) < len(tickers) * MIN_BATCH_COVERAGE:
        raise DataFetchError(f"Yalnızca {len(data)}/{len(tickers)} hisse için veri geldi.")
    return data, market.now()


@st.cache_data(max_entries=64, ttl=24 * 3600, show_spinner=False)
def _single(ticker: str, start: date, end: date, key: str) -> tuple[pd.DataFrame, datetime]:
    return get_price_history.__wrapped__(ticker, start, end), market.now()


def _remember(store_key: tuple, data, fetched_at: datetime) -> None:
    last_good = _state()["last_good"]
    last_good[store_key] = (data, fetched_at)
    last_good.move_to_end(store_key)
    while len(last_good) > MAX_SINGLE_FALLBACKS:
        last_good.popitem(last=False)


def _fetch(store_key: tuple, loader) -> Feed:
    try:
        data, fetched_at = loader(_key())
    except DataFetchError:
        cached = _state()["last_good"].get(store_key)
        if cached is None:
            raise
        return Feed(cached[0], cached[1], stale=True)
    _remember(store_key, data, fetched_at)
    return Feed(data, fetched_at, stale=False)


def batch(tickers: tuple[str, ...]) -> Feed:
    """Tarama için tüm hisselerin günlük OHLCV verisi (sözlük)."""
    return _fetch(("batch", tickers), lambda key: _batch(tickers, key))


def single(ticker: str, start: date, end: date) -> Feed:
    """Hisse Detay için tek hissenin ham günlük OHLCV verisi."""
    return _fetch(("single", ticker, start, end), lambda key: _single(ticker, start, end, key))


def request_refresh() -> int:
    """Önbelleği geçersiz kılar. Başarılıysa 0, bekleme süresi dolmadıysa kalan saniye."""
    state = _state()
    wait = REFRESH_COOLDOWN_SECONDS - (time.monotonic() - state["last_refresh"])
    if state["last_refresh"] and wait > 0:
        return int(wait) + 1
    state["nonce"] += 1
    state["last_refresh"] = time.monotonic()
    return 0
