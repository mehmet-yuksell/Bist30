"""Yahoo Finance üzerinden fiyat verisi çekme işlevleri."""

import csv
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
import yfinance as yf

from config import YAHOO_SUFFIX

BIST_ALL_CSV_PATH = Path(__file__).parent / "data" / "bist_all.csv"
from ui_text import (
    ERROR_INCOMPLETE_DATA,
    ERROR_NETWORK,
    ERROR_NETWORK_BATCH,
    ERROR_NO_DATA,
    ERROR_NO_DATA_BATCH,
)


class DataFetchError(Exception):
    """Kullanıcıya gösterilecek hazır Türkçe mesajı taşır."""


@st.cache_data(show_spinner=False)
def load_all_bist_symbols() -> dict[str, str]:
    """data/bist_all.csv dosyasından (KAP kaynaklı) tüm BIST sembollerini yükler.

    Sembol -> şirket adı eşlemesi döner. BIST 30 Tarama sekmesi bunu KULLANMAZ;
    sadece Hisse Detay ve Karşılaştırma'daki arama/seçim için kullanılır.
    """
    symbols: dict[str, str] = {}
    with open(BIST_ALL_CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = row["symbol"].strip()
            name = row["company_name"].strip()
            if symbol and name:
                symbols[symbol] = name
    return symbols


@st.cache_data(ttl=3600, show_spinner=False)
def get_price_history(ticker: str, start_date: date, end_date: date) -> pd.DataFrame:
    """Bir BIST hissesi için günlük OHLCV verisini döndürür (end_date dahildir)."""
    yahoo_ticker = f"{ticker}{YAHOO_SUFFIX}"

    try:
        df = yf.download(
            yahoo_ticker,
            start=start_date,
            end=end_date + timedelta(days=1),
            progress=False,
            auto_adjust=False,
        )
    except Exception as exc:
        raise DataFetchError(ERROR_NETWORK.format(ticker=ticker)) from exc

    if df is None or df.empty:
        raise DataFetchError(ERROR_NO_DATA.format(ticker=ticker))

    # yfinance tek hisse için de MultiIndex kolon döndürebiliyor (Price, Ticker).
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.dropna(how="all")
    if df.empty:
        raise DataFetchError(ERROR_INCOMPLETE_DATA.format(ticker=ticker))

    return df


@st.cache_data(ttl=3600, show_spinner=False)
def get_multiple_price_histories(
    tickers: tuple[str, ...], period: str = "2y"
) -> dict[str, pd.DataFrame]:
    """BIST 30 taraması için tüm hisselerin OHLCV verisini tek seferde çeker."""
    yahoo_tickers = [f"{t}{YAHOO_SUFFIX}" for t in tickers]

    try:
        raw = yf.download(
            yahoo_tickers,
            period=period,
            progress=False,
            auto_adjust=False,
            group_by="ticker",
        )
    except Exception as exc:
        raise DataFetchError(ERROR_NETWORK_BATCH) from exc

    if raw is None or raw.empty:
        raise DataFetchError(ERROR_NO_DATA_BATCH)

    result: dict[str, pd.DataFrame] = {}
    for ticker, yahoo_ticker in zip(tickers, yahoo_tickers):
        try:
            df = raw[yahoo_ticker].dropna(how="all")
        except KeyError:
            continue
        if not df.empty:
            result[ticker] = df

    if not result:
        raise DataFetchError(ERROR_NO_DATA_BATCH)

    return result
