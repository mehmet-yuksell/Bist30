"""bluetsman.py için testler. Beklenen değerler Pine Script tanımlarından elle hesaplanmıştır."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bluetsman
from bluetsman import compute, condition_score, latest_status, rma, signal_history, true_range
from indicators import ema


def _ohlcv(close: np.ndarray, volume: np.ndarray | None = None) -> pd.DataFrame:
    idx = pd.bdate_range("2025-01-01", periods=len(close))
    close = pd.Series(close, index=idx, dtype=float)
    return pd.DataFrame(
        {
            "Open": close.shift(1).fillna(close.iloc[0]),
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": volume if volume is not None else np.full(len(close), 1_000_000.0),
        },
        index=idx,
    )


def _reversal_df() -> pd.DataFrame:
    """120 gün düşüş, ardından 40 gün güçlü ve artan hacimli yükseliş."""
    down = np.linspace(100, 70, 120)
    up = 70 * 1.03 ** np.arange(1, 41)
    volume = np.concatenate([np.full(120, 1_000_000.0), 1_000_000.0 * 1.1 ** np.arange(1, 41)])
    return _ohlcv(np.concatenate([down, up]), volume)


def test_condition_score_scales_and_clips():
    values = pd.Series([-1.0, 0.0, 1.0, 2.0, 3.0])
    result = condition_score(values, 0, 2, 15)
    assert result.tolist() == pytest.approx([0, 0, 7.5, 15, 15])


def test_rma_seeds_with_sma_then_wilder():
    # Pine ta.rma(3): ilk değer sma = 2; sonra (1/3)*x + (2/3)*önceki
    result = rma(pd.Series([1.0, 2.0, 3.0, 4.0, 5.0]), 3)
    assert result.iloc[:2].isna().all()
    assert result.iloc[2] == pytest.approx(2.0)
    assert result.iloc[3] == pytest.approx(8 / 3)
    assert result.iloc[4] == pytest.approx(31 / 9)


def test_rma_skips_leading_nan():
    result = rma(pd.Series([np.nan, 1.0, 2.0, 3.0]), 2)
    assert result.iloc[:2].isna().all()
    assert result.iloc[2] == pytest.approx(1.5)
    assert result.iloc[3] == pytest.approx(2.25)


def test_true_range_first_bar():
    df = _ohlcv(np.array([10.0, 11.0, 9.0]))
    assert np.isnan(true_range(df).iloc[0])  # ta.tr: önceki kapanış yok -> na
    assert true_range(df, handle_na=True).iloc[0] == pytest.approx(10.1 - 9.9)  # ta.atr içindeki
    # 3. gün: max(9.09-8.91, |9.09-11|, |8.91-11|) = 2.09
    assert true_range(df).iloc[2] == pytest.approx(2.09)


def test_ema_cross_matches_sign_change():
    df = _reversal_df()
    result = compute(df)
    diff = ema(df["Close"], 13) - ema(df["Close"], 34)
    expected = (diff > 0) & (diff.shift(1) <= 0)
    assert result["ema_cross"].equals(expected)
    assert result["ema_cross"].sum() >= 1


def test_reversal_produces_buy_signal_with_all_conditions():
    result = compute(_reversal_df())
    signals = result[result["buy_signal"]]

    assert len(signals) >= 1
    assert signals[list(bluetsman.CONDITIONS)].all(axis=None)
    # Sinyal günü EMA (15) + fiyat (20) + hacim (15) puanları kesin alınır
    assert (signals["score"] >= 50).all()


def test_no_signal_in_steady_downtrend():
    result = compute(_ohlcv(np.linspace(100, 50, 200)))
    assert not result["buy_signal"].any()
    assert not result["supertrend"].iloc[-1]


def test_score_bounded_on_random_walk():
    rng = np.random.default_rng(7)
    close = 50 * np.exp(np.cumsum(rng.normal(0, 0.02, 400)))
    volume = rng.uniform(5e5, 2e6, 400)
    result = compute(_ohlcv(close, volume))
    assert result["score"].between(0, 100).all()
    assert result["buy_signal"].dtype == bool


def test_latest_status_counts_trading_days():
    idx = pd.bdate_range("2026-01-01", periods=12)
    signals = pd.DataFrame({c: False for c in bluetsman.CONDITIONS}, index=idx)
    signals["score"] = 30.0
    signals["buy_signal"] = False
    signals.iloc[-3, signals.columns.get_loc("buy_signal")] = True
    signals.iloc[-3, signals.columns.get_loc("score")] = 81.0
    signals.iloc[-1, signals.columns.get_loc("rsi")] = True

    status = latest_status(signals, lookback=10)

    assert status["days_since"] == 2
    assert status["signal_score"] == 81.0
    assert status["signal_date"] == idx[-3]
    assert status["met"] == 1
    assert not status["signal_today"]
    assert latest_status(signals, lookback=2)["days_since"] is None


def test_signal_history_forward_return():
    idx = pd.bdate_range("2026-01-01", periods=6)
    df = pd.DataFrame({"Close": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]}, index=idx)
    signals = pd.DataFrame(
        {"buy_signal": [True, False, False, False, True, False], "score": [60.0, 0, 0, 0, 75.0, 0]},
        index=idx,
    )

    history = signal_history(df, signals, horizon=2)

    assert list(history.index) == [idx[4], idx[0]]  # en yeni üstte
    assert history["forward_return"].iloc[1] == pytest.approx(20.0)  # 10 -> 12
    assert np.isnan(history["forward_return"].iloc[0])  # 2 gün henüz geçmedi
