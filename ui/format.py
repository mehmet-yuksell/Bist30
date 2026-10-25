"""Türkçe sayı ve tarih biçimlendirme (binlik ayraç nokta, ondalık virgül)."""

import math

import pandas as pd

MINUS = "−"  # tipografik eksi işareti


def _is_missing(value) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) or pd.isna(value)


def fmt_num(value, decimals: int = 2) -> str:
    """1234.56 -> '1.234,56'; eksik değer -> '—'."""
    if _is_missing(value):
        return "—"
    text = f"{abs(float(value)):,.{decimals}f}"
    text = text.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    return f"{MINUS}{text}" if float(value) < 0 and text.strip("0,.") else text


def fmt_pct(value, decimals: int = 2, signed: bool = True) -> str:
    """1.234 -> '%+1,23'; -0.5 -> '%−0,50'; signed=False -> '%1,23'."""
    if _is_missing(value):
        return "—"
    number = fmt_num(abs(float(value)), decimals)
    if not signed:
        return f"%{number}"
    rounded = round(float(value), decimals)
    if rounded > 0:
        sign = "+"
    elif rounded < 0:
        sign = MINUS
    else:
        sign = ""
    return f"%{sign}{number}"


def arrow(value) -> str:
    """Yön işareti: ▲ (pozitif), ▼ (negatif), • (sıfır/eksik)."""
    if _is_missing(value) or round(float(value), 2) == 0:
        return "•"
    return "▲" if value > 0 else "▼"


def direction(value) -> str:
    """CSS sınıfı için yön adı: 'up', 'down' veya 'flat'."""
    if _is_missing(value) or round(float(value), 2) == 0:
        return "flat"
    return "up" if value > 0 else "down"


def fmt_compact(value) -> str:
    """Büyük sayılar için kısa gösterim: 46_611_644 -> '46,6 Mn'."""
    if _is_missing(value):
        return "—"
    value = float(value)
    for limit, suffix in ((1e9, "Mr"), (1e6, "Mn"), (1e3, "Bin")):
        if abs(value) >= limit:
            return f"{fmt_num(value / limit, 1)} {suffix}"
    return fmt_num(value, 0)


def fmt_date(value) -> str:
    """Tarihi gg.aa.yyyy biçiminde döndürür."""
    if _is_missing(value):
        return "—"
    return pd.Timestamp(value).strftime("%d.%m.%Y")


def fmt_price(value, currency: str = "TL") -> str:
    symbol = "$" if currency == "USD" else "₺"
    return f"{fmt_num(value, 2)} {symbol}"
