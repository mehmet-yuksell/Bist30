"""Basit, parametre optimizasyonu yapılmayan sinyal geriye dönük testi (backtest).

Kurallar (bilinçli tasarım kararları):
- Sinyal gün sonu (kapanış) verisiyle oluşur; işlem ERTESİ GÜN açılışında (Open)
  gerçekleşir. Bu, enter/exit koşullarının bir gün KAYDIRILMASIYLA (shift) sağlanır —
  bkz. `_run_signal_strategy` içindeki `enter_shifted`/`exit_shifted`. Böylece bir günün
  kararı, o günün kapanışından SONRAKİ güne kadar bilinen hiçbir veriyi kullanmaz.
- Parametreler (RSI 14/30/70, MACD 12/26/9, SMA 50/200) sabittir; optimizasyon yapılmaz.
- Sadece uzun (long) pozisyon, kaldıraç yok.
- İşlem maliyeti her yönde (al/sat) ayrı ayrı, çarpımsal olarak uygulanır.
- Çağıran taraf (app.py), `data.get_adjusted_price_history` ile bedelsiz/temettü
  düzeltmeli fiyat sağlamalıdır — bu modül düzeltmeyi kendi yapmaz, sadece gelen
  Open/Close serilerini kullanır.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from indicators import macd, rsi, sma

RSI_WINDOW = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

SMA_SHORT = 50
SMA_LONG = 200

DEFAULT_COST_PCT = 0.1  # her yönde (al/sat), yüzde


@dataclass
class Trade:
    entry_date: pd.Timestamp
    entry_price: float
    exit_date: pd.Timestamp | None = None
    exit_price: float | None = None

    @property
    def is_closed(self) -> bool:
        return self.exit_date is not None

    def net_return_pct(self, cost_pct: float) -> float | None:
        if not self.is_closed:
            return None
        cost_factor = 1 - cost_pct / 100
        multiplier = cost_factor * (self.exit_price / self.entry_price) * cost_factor
        return (multiplier - 1) * 100


@dataclass
class BacktestResult:
    name: str
    equity_curve: pd.Series
    trades: list[Trade] = field(default_factory=list)
    total_return_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    num_trades: int | None = 0
    win_rate_pct: float | None = None


def _max_drawdown_pct(equity_curve: pd.Series) -> float:
    running_max = equity_curve.cummax()
    drawdown = (equity_curve - running_max) / running_max
    return float(drawdown.min() * 100)


def _run_signal_strategy(
    df: pd.DataFrame,
    enter_condition: pd.Series,
    exit_condition: pd.Series,
    cost_pct: float,
    name: str,
) -> BacktestResult:
    open_ = df["Open"]
    dates = df.index
    n = len(dates)

    # KRİTİK: sinyal bir gün kaydırılır ki bugünkü karar, bugünün kendi kapanışını
    # değil, DÜNÜN kapanışını kullansın (look-ahead önleme).
    enter_shifted = enter_condition.shift(1).fillna(False)
    exit_shifted = exit_condition.shift(1).fillna(False)

    equity = 100.0
    equity_values: list[float] = []
    trades: list[Trade] = []
    in_position = False
    entry_date = None
    entry_price = None

    for i in range(n):
        if not in_position and bool(enter_shifted.iloc[i]):
            in_position = True
            entry_date = dates[i]
            entry_price = float(open_.iloc[i])
            equity *= 1 - cost_pct / 100
        elif in_position and bool(exit_shifted.iloc[i]):
            exit_price = float(open_.iloc[i])
            equity *= 1 - cost_pct / 100
            trades.append(Trade(entry_date, entry_price, dates[i], exit_price))
            in_position = False
            entry_date = None
            entry_price = None

        if in_position and i + 1 < n:
            equity *= float(open_.iloc[i + 1]) / float(open_.iloc[i])

        equity_values.append(equity)

    if in_position:
        trades.append(Trade(entry_date, entry_price))  # dönem sonunda hâlâ açık

    equity_curve = pd.Series(equity_values, index=dates, name=name)

    closed = [t for t in trades if t.is_closed]
    num_trades = len(closed)
    if num_trades > 0:
        wins = sum(1 for t in closed if t.net_return_pct(cost_pct) > 0)
        win_rate_pct = wins / num_trades * 100
    else:
        win_rate_pct = None

    return BacktestResult(
        name=name,
        equity_curve=equity_curve,
        trades=trades,
        total_return_pct=(equity_curve.iloc[-1] / 100 - 1) * 100,
        max_drawdown_pct=_max_drawdown_pct(equity_curve),
        num_trades=num_trades,
        win_rate_pct=win_rate_pct,
    )


def run_rsi_strategy(df: pd.DataFrame, cost_pct: float = DEFAULT_COST_PCT) -> BacktestResult:
    close = df["Close"]
    rsi_series = rsi(close, RSI_WINDOW)
    enter_condition = rsi_series < RSI_OVERSOLD
    exit_condition = rsi_series > RSI_OVERBOUGHT
    return _run_signal_strategy(df, enter_condition, exit_condition, cost_pct, "RSI Stratejisi")


def run_macd_strategy(df: pd.DataFrame, cost_pct: float = DEFAULT_COST_PCT) -> BacktestResult:
    close = df["Close"]
    macd_df = macd(close, MACD_FAST, MACD_SLOW, MACD_SIGNAL)
    enter_condition = macd_df["macd"] > macd_df["signal"]
    exit_condition = macd_df["macd"] < macd_df["signal"]
    return _run_signal_strategy(df, enter_condition, exit_condition, cost_pct, "MACD Stratejisi")


def run_sma_cross_strategy(df: pd.DataFrame, cost_pct: float = DEFAULT_COST_PCT) -> BacktestResult:
    close = df["Close"]
    sma_short = sma(close, SMA_SHORT)
    sma_long = sma(close, SMA_LONG)
    enter_condition = sma_short > sma_long
    exit_condition = sma_short < sma_long
    return _run_signal_strategy(df, enter_condition, exit_condition, cost_pct, "Altın/Ölüm Kesişimi")


def run_buy_and_hold(df: pd.DataFrame, cost_pct: float = DEFAULT_COST_PCT) -> BacktestResult:
    open_ = df["Open"]
    close = df["Close"]
    entry_price = float(open_.iloc[0])
    cost_factor = 1 - cost_pct / 100

    equity_curve = close / entry_price * 100 * cost_factor
    equity_curve.name = "Al-Tut"

    trade = Trade(df.index[0], entry_price, df.index[-1], float(close.iloc[-1]))

    return BacktestResult(
        name="Al-Tut",
        equity_curve=equity_curve,
        trades=[trade],
        total_return_pct=(equity_curve.iloc[-1] / 100 - 1) * 100,
        max_drawdown_pct=_max_drawdown_pct(equity_curve),
        num_trades=None,
        win_rate_pct=None,
    )
