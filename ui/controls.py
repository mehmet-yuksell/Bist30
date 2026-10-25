"""Sekmeler arasında ortak kullanılan form kontrolleri."""

from datetime import date, timedelta

import streamlit as st

from config import BIST30_TICKERS
from ui.components import callout
from ui_text import (
    DATE_BUTTON_LABEL,
    DATE_RANGE_INCOMPLETE,
    DATE_RANGE_INVALID,
    DATE_RANGE_LABEL,
    SYMBOL_NOT_IN_LIST,
)

MIN_DATE = date(2005, 1, 1)


def symbol_formatter(all_stocks: dict[str, str]):
    def format_symbol(symbol: str) -> str:
        if symbol in all_stocks:
            return f"{symbol} — {all_stocks[symbol]}"
        return f"{symbol} {SYMBOL_NOT_IN_LIST}"

    return format_symbol


def display_name(symbol: str, all_stocks: dict[str, str]) -> str:
    """BIST 30 için okunaklı kısa ad, diğerleri için KAP'taki resmi unvan."""
    return BIST30_TICKERS.get(symbol) or all_stocks.get(symbol, "")


def date_range_popover(key: str, default_days: int):
    """Tarih aralığını varsayılan olarak kapalı bir açılır panelde toplar.

    Geçerli bir aralık seçildiyse (başlangıç, bitiş) döner; aksi halde kullanıcıya
    yönlendirici bir mesaj gösterip None döner.
    """
    today = date.today()
    with st.popover(DATE_BUTTON_LABEL, icon=":material/calendar_month:", width="content"):
        date_range = st.date_input(
            DATE_RANGE_LABEL,
            value=(today - timedelta(days=default_days), today),
            min_value=MIN_DATE,
            max_value=today,
            format="DD.MM.YYYY",
            key=key,
        )
    return date_range


def validate_date_range(date_range):
    if not isinstance(date_range, tuple) or len(date_range) != 2:
        callout("info", None, DATE_RANGE_INCOMPLETE)
        return None
    start_date, end_date = date_range
    if start_date >= end_date:
        callout("warn", None, DATE_RANGE_INVALID)
        return None
    return start_date, end_date
