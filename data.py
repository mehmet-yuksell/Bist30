"""Yahoo Finance üzerinden fiyat verisi çekme işlevleri."""

from datetime import date, timedelta

import pandas as pd
import streamlit as st
import yfinance as yf

from config import YAHOO_SUFFIX
from ui_text import ERROR_INCOMPLETE_DATA, ERROR_NETWORK, ERROR_NO_DATA


class DataFetchError(Exception):
    """Kullanıcıya gösterilecek hazır Türkçe mesajı taşır."""


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
