"""Bluetsman — Piyasanın Efendisi (Alım) göstergesinin Python karşılığı.

Kaynak, TradingView Pine Script v5 göstergesidir ("Alım 1.2 Final Sürüm"). Hesaplar,
TradingView'deki sonuçla aynı çıkacak şekilde birebir aktarılmıştır; göstergenin kendine
özgü tercihleri (ör. hacim puanının pratikte hep 15 olması, momentum ve MACD puanlarının
TL cinsinden sabit eşiklerle ölçülmesi, standart dışı Supertrend) bilinçli olarak korunur.

Pine'daki karşılıklar:
- ta.ema -> indicators.ema (ilk değerle başlayan üssel ortalama, Pine ile aynı)
- ta.rsi -> indicators.rsi (Wilder yöntemi)
- ta.rma -> rma() (ilk değer basit ortalama, sonrası alpha = 1/uzunluk)
- ta.tr / ta.atr -> true_range() / rma(true_range(handle_na=True))
- Pine'da `na` içeren karşılaştırmalar `false` döner; pandas'ta NaN karşılaştırmaları da
  False döndüğü için koşullar aynı davranır.

Yalnızca bir koşul taramasıdır; yatırım tavsiyesi değildir.
"""

import math

import numpy as np
import pandas as pd

from indicators import ema, macd, rsi

EMA_FAST = 13
EMA_SLOW = 34
RSI_LENGTH = 14
ADX_LENGTH = 14
ADX_THRESHOLD = 20
ATR_LENGTH = 10
SUPERTREND_FACTOR = 3.0
VOLUME_LENGTH = 20
VOLUME_MULTIPLIER = 1.05

MAX_SCORE_EMA = 15
MAX_SCORE_VOLUME = 15
MAX_SCORE_RSI = 15
MAX_SCORE_MOMENTUM = 15
MAX_SCORE_MACD = 15
MAX_SCORE_PRICE = 20
MAX_SCORE_SUPERTREND = 5
MAX_SCORE_ADX = 10

# Sinyal için sekiz koşulun tamamı aynı gün sağlanmalıdır (Pine'daki buySignal).
CONDITIONS = (
    "ema_cross",
    "volume",
    "rsi",
    "momentum",
    "macd",
    "price_above",
    "supertrend",
    "adx",
)


def condition_score(value: pd.Series, low: float, high: float, max_score: float) -> pd.Series:
    """Pine'daki getConditionScore: değeri [low, high] aralığında 0..max_score'a ölçekler."""
    if high > low:
        return ((value - low) / (high - low) * max_score).clip(lower=0, upper=max_score)
    return pd.Series(np.where(value > low, max_score, 0.0), index=value.index)


def rma(series: pd.Series, length: int) -> pd.Series:
    """Pine ta.rma: ilk `length` değerin basit ortalamasıyla başlar, sonra Wilder düzeltmesi."""
    # Döngü numpy skalerleri yerine düz Python listeleri üzerinde döner: tarama 100 hisse için
    # bunu birkaç kez çalıştırır ve skaler indeksleme belirgin şekilde yavaştır.
    values = series.to_numpy(dtype=float).tolist()
    seed = series.rolling(length).mean().to_numpy().tolist()
    out = [math.nan] * len(values)
    alpha = 1.0 / length
    prev = math.nan
    for i, value in enumerate(values):
        prev = seed[i] if math.isnan(prev) else alpha * value + (1 - alpha) * prev
        out[i] = prev
    return pd.Series(out, index=series.index, dtype=float)


def true_range(df: pd.DataFrame, handle_na: bool = False) -> pd.Series:
    """Pine ta.tr(handle_na): önceki kapanış yoksa NaN (False) ya da yüksek-düşük (True)."""
    prev_close = df["Close"].shift(1)
    tr = pd.concat(
        [df["High"] - df["Low"], (df["High"] - prev_close).abs(), (df["Low"] - prev_close).abs()],
        axis=1,
    ).max(axis=1, skipna=False)
    if handle_na:
        tr = tr.where(prev_close.notna(), df["High"] - df["Low"])
    return tr


def adx(df: pd.DataFrame, length: int = ADX_LENGTH) -> pd.Series:
    up_move = df["High"] - df["High"].shift(1)
    down_move = df["Low"].shift(1) - df["Low"]
    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=df.index)
    trur = rma(true_range(df), length)
    plus_di = 100 * rma(plus_dm, length) / trur
    minus_di = 100 * rma(minus_dm, length) / trur
    with np.errstate(divide="ignore", invalid="ignore"):
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    return rma(dx.replace([np.inf, -np.inf], np.nan), length)


def supertrend(df: pd.DataFrame, length: int = ATR_LENGTH, factor: float = SUPERTREND_FACTOR):
    """Göstergedeki Supertrend varyantı (standart Supertrend'den farklıdır, aynen korunur).

    Döner: (çizgi, trend_yukarı) serileri.
    """
    atr = rma(true_range(df, handle_na=True), length)
    hl2 = (df["High"] + df["Low"]) / 2
    close = df["Close"].to_numpy(dtype=float).tolist()
    upper = (hl2 + factor * atr).to_numpy(dtype=float).tolist()
    lower = (hl2 - factor * atr).to_numpy(dtype=float).tolist()

    line = [math.nan] * len(close)
    trend_up = [False] * len(close)
    prev = math.nan
    for i in range(len(close)):
        if math.isnan(prev):
            line[i] = upper[i]
            trend_up[i] = close[i] > upper[i]  # NaN karşılaştırması False (Pine ile aynı)
        elif close[i] > prev:
            line[i] = max(lower[i], prev)
            trend_up[i] = True
        else:
            line[i] = min(upper[i], prev)
            trend_up[i] = False
        prev = line[i]
    return pd.Series(line, index=df.index, dtype=float), pd.Series(trend_up, index=df.index)


def compute(df: pd.DataFrame) -> pd.DataFrame:
    """OHLCV verisinden her gün için koşulları, skoru (0-100) ve alım sinyalini hesaplar.

    Döner sütunlar: ema_fast, ema_slow, CONDITIONS'taki her koşul (bool), score, buy_signal.
    """
    close = df["Close"]
    volume = df["Volume"].astype(float)

    ema_fast = ema(close, EMA_FAST)
    ema_slow = ema(close, EMA_SLOW)
    rsi_value = rsi(close, RSI_LENGTH)
    momentum = close - close.shift(1)
    macd_hist = macd(close)["histogram"]
    adx_value = adx(df)
    st_line, st_up = supertrend(df)
    volume_sma = volume.rolling(VOLUME_LENGTH).mean()

    out = pd.DataFrame(index=df.index)
    out["ema_fast"] = ema_fast
    out["ema_slow"] = ema_slow
    out["ema_cross"] = (ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1))
    out["volume"] = volume > volume_sma * VOLUME_MULTIPLIER
    out["rsi"] = rsi_value > 50
    out["momentum"] = momentum > 0
    out["macd"] = macd_hist > 0
    out["price_above"] = close > ema_slow
    out["supertrend"] = st_up
    out["adx"] = adx_value > ADX_THRESHOLD

    st_distance = (close - st_line) / close * 100
    scores = [
        np.where(out["ema_cross"], MAX_SCORE_EMA, 0.0),
        np.where(out["volume"], (volume / volume_sma * 100).clip(upper=MAX_SCORE_VOLUME), 0.0),
        np.where(out["rsi"], condition_score(rsi_value, 30, 80, MAX_SCORE_RSI), 0.0),
        np.where(out["momentum"], condition_score(momentum, 0, 2, MAX_SCORE_MOMENTUM), 0.0),
        np.where(out["macd"], condition_score(macd_hist, 0, 1, MAX_SCORE_MACD), 0.0),
        np.where(out["price_above"], MAX_SCORE_PRICE, 0.0),
        np.where(out["supertrend"], condition_score(st_distance, 0, 5, MAX_SCORE_SUPERTREND), 0.0),
        np.where(out["adx"], condition_score(adx_value, ADX_THRESHOLD, 50, MAX_SCORE_ADX), 0.0),
    ]
    out["score"] = np.clip(np.nansum(scores, axis=0), 0, 100)
    out["buy_signal"] = out[list(CONDITIONS)].all(axis=1)

    # Göstergede ayrıca kullanılmayan ama ekranda açıklama için gereken değerler
    out["rsi_value"] = rsi_value
    out["momentum_value"] = momentum
    out["macd_hist"] = macd_hist
    out["adx_value"] = adx_value
    out["volume_ratio"] = volume / volume_sma
    return out


def latest_status(signals: pd.DataFrame, lookback: int = 10) -> dict:
    """Son günün durumu ve son `lookback` işlem günündeki en son sinyal.

    Döner: score, met (sağlanan koşul sayısı), signal_today, days_since (int | None),
    signal_score (son sinyalin skoru | None), signal_date.
    """
    last = signals.iloc[-1]
    recent = signals.iloc[-lookback:]
    hits = recent.index[recent["buy_signal"]]
    status = {
        "score": float(last["score"]),
        "met": int(sum(bool(last[c]) for c in CONDITIONS)),
        "signal_today": bool(last["buy_signal"]),
        "days_since": None,
        "signal_score": None,
        "signal_date": None,
    }
    if len(hits):
        last_hit = hits[-1]
        status["days_since"] = len(signals) - 1 - signals.index.get_loc(last_hit)
        status["signal_score"] = float(signals.at[last_hit, "score"])
        status["signal_date"] = last_hit
    return status


def signal_history(df: pd.DataFrame, signals: pd.DataFrame, horizon: int = 10) -> pd.DataFrame:
    """Her sinyal için tarih, skor ve sinyal kapanışından `horizon` işlem günü sonraki getiri (%).

    Henüz `horizon` gün geçmemiş sinyallerde getiri NaN'dır. En yeni sinyal en üsttedir.
    """
    close = df["Close"].reindex(signals.index)
    forward = (close.shift(-horizon) / close - 1) * 100
    hits = signals["buy_signal"]
    return pd.DataFrame(
        {"score": signals.loc[hits, "score"], "close": close[hits], "forward_return": forward[hits]}
    ).iloc[::-1]
