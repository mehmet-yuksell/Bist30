"""Teknik göstergeler: SMA, EMA, RSI (Wilder), MACD, Bollinger Bantları.

Hazır gösterge paketi kullanılmaz; tüm hesaplamalar pandas/numpy ile yapılır.
"""

import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window).mean()


def ema(series: pd.Series, window: int) -> pd.Series:
    return series.ewm(span=window, adjust=False).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Wilder'ın orijinal yöntemiyle RSI: ilk ortalama basit ortalama, sonrası
    (önceki_ortalama * (window-1) + yeni_değer) / window şeklinde düzeltilir."""
    delta = series.diff()
    gain = delta.clip(lower=0.0).to_numpy()
    loss = (-delta.clip(upper=0.0)).to_numpy()

    avg_gain = np.full(len(series), np.nan)
    avg_loss = np.full(len(series), np.nan)

    if len(series) > window:
        avg_gain[window] = gain[1 : window + 1].mean()
        avg_loss[window] = loss[1 : window + 1].mean()

        for i in range(window + 1, len(series)):
            avg_gain[i] = (avg_gain[i - 1] * (window - 1) + gain[i]) / window
            avg_loss[i] = (avg_loss[i - 1] * (window - 1) + loss[i]) / window

    avg_gain_s = pd.Series(avg_gain, index=series.index)
    avg_loss_s = pd.Series(avg_loss, index=series.index)

    with np.errstate(divide="ignore", invalid="ignore"):
        rs = avg_gain_s / avg_loss_s
    rsi_values = 100 - (100 / (1 + rs))

    rsi_values = rsi_values.where(avg_loss_s != 0, 100.0)
    flat = (avg_gain_s == 0) & (avg_loss_s == 0)
    rsi_values = rsi_values.where(~flat, 50.0)

    return rsi_values


def macd(
    series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> pd.DataFrame:
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return pd.DataFrame(
        {"macd": macd_line, "signal": signal_line, "histogram": histogram}
    )


def bollinger_bands(
    series: pd.Series, window: int = 20, num_std: float = 2.0
) -> pd.DataFrame:
    middle = sma(series, window)
    std = series.rolling(window=window).std(ddof=0)
    upper = middle + num_std * std
    lower = middle - num_std * std
    return pd.DataFrame({"middle": middle, "upper": upper, "lower": lower})
