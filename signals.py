"""Gösterge değerlerinden tarafsız Türkçe gözlem metinleri üretir.

Bu modül "AL/SAT" gibi tavsiye niteliğinde ifadeler üretmez; sadece
göstergelerin durumunu betimler.
"""

import numpy as np
import pandas as pd

RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30


def describe_rsi(rsi_value: float) -> str:
    if pd.isna(rsi_value):
        return "RSI hesaplanamadı (yetersiz veri)."
    if rsi_value >= RSI_OVERBOUGHT:
        return f"RSI aşırı alım bölgesinde ({rsi_value:.1f})."
    if rsi_value <= RSI_OVERSOLD:
        return f"RSI aşırı satım bölgesinde ({rsi_value:.1f})."
    return f"RSI normal bölgede ({rsi_value:.1f})."


def _last_crossover(diff: pd.Series, lookback: int) -> str | None:
    """diff serisinin son `lookback` günündeki en son işaret değişimini döndürür."""
    window = diff.iloc[-(lookback + 1) :]
    sign_changes = np.sign(window).diff().dropna()

    last_cross = None
    for value in sign_changes:
        if value > 0:
            last_cross = "up"
        elif value < 0:
            last_cross = "down"
    return last_cross


def describe_macd_cross(macd_df: pd.DataFrame, lookback: int = 5) -> str:
    valid = macd_df.dropna(subset=["macd", "signal"])
    if len(valid) < 2:
        return "MACD hesaplanamadı (yetersiz veri)."

    diff = valid["macd"] - valid["signal"]
    cross = _last_crossover(diff, lookback)

    if cross == "up":
        return "MACD çizgisi son günlerde sinyal çizgisinin üzerine çıktı."
    if cross == "down":
        return "MACD çizgisi son günlerde sinyal çizgisinin altına indi."
    return (
        "MACD çizgisi sinyal çizgisinin üzerinde."
        if diff.iloc[-1] > 0
        else "MACD çizgisi sinyal çizgisinin altında."
    )


def describe_price_vs_ma(price: float, sma50: float, sma200: float) -> str:
    parts = []

    if pd.isna(sma50):
        parts.append("50 günlük ortalama hesaplanamadı (yetersiz veri)")
    else:
        parts.append(f"50 günlük ortalamanın {'üzerinde' if price >= sma50 else 'altında'}")

    if pd.isna(sma200):
        parts.append("200 günlük ortalama hesaplanamadı (yetersiz veri)")
    else:
        parts.append(f"200 günlük ortalamanın {'üzerinde' if price >= sma200 else 'altında'}")

    return "Fiyat, " + " ve ".join(parts) + "."


def describe_golden_death_cross(
    sma50: pd.Series, sma200: pd.Series, lookback: int = 10
) -> str:
    valid = pd.DataFrame({"sma50": sma50, "sma200": sma200}).dropna()
    if len(valid) < 2:
        return "Altın/ölüm kesişimi için yeterli veri yok (200 günlük ortalama hesaplanamadı)."

    diff = valid["sma50"] - valid["sma200"]
    cross = _last_crossover(diff, lookback)

    if cross == "up":
        return (
            "Son günlerde altın kesişim gerçekleşti "
            "(50 günlük ortalama, 200 günlük ortalamanın üzerine çıktı)."
        )
    if cross == "down":
        return (
            "Son günlerde ölüm kesişimi gerçekleşti "
            "(50 günlük ortalama, 200 günlük ortalamanın altına indi)."
        )
    return (
        "50 günlük ortalama, 200 günlük ortalamanın üzerinde."
        if diff.iloc[-1] > 0
        else "50 günlük ortalama, 200 günlük ortalamanın altında."
    )
