"""indicators.py için testler. Beklenen değerler elle (kapalı formülle) hesaplanmıştır."""

import math
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from indicators import bollinger_bands, ema, macd, rsi, sma


def test_sma_basic():
    data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    result = sma(data, window=3)

    assert result.iloc[:2].isna().all()
    assert result.iloc[2] == pytest.approx(2.0)
    assert result.iloc[3] == pytest.approx(3.0)
    assert result.iloc[4] == pytest.approx(4.0)


def test_ema_basic():
    # span=3 -> alpha=0.5; y[0]=x[0], y[t]=0.5*x[t]+0.5*y[t-1]
    data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    result = ema(data, window=3)

    expected = [1.0, 1.5, 2.25, 3.125, 4.0625]
    for actual, exp in zip(result, expected):
        assert actual == pytest.approx(exp)


def test_rsi_wilder_known_values():
    # window=4; gain/loss ve Wilder düzeltmesi elle hesaplanmıştır (bkz. test dosyasının
    # yazılma sürecindeki hesap: avg_gain/avg_loss her adımda (prev*(n-1)+yeni)/n).
    data = pd.Series([10, 10.5, 10, 10.5, 11, 10.5, 11, 11.5], dtype=float)
    result = rsi(data, window=4)

    assert result.iloc[:4].isna().all()
    assert result.iloc[4] == pytest.approx(75.0)
    assert result.iloc[5] == pytest.approx(56.25)
    assert result.iloc[6] == pytest.approx(67.1875)
    assert result.iloc[7] == pytest.approx(75.390625)


def test_rsi_all_gains_is_100():
    data = pd.Series([10, 11, 12, 13, 14, 15, 16], dtype=float)
    result = rsi(data, window=3)

    assert result.iloc[3:].dropna().eq(100.0).all()


def test_rsi_flat_series_is_50():
    data = pd.Series([10.0] * 10)
    result = rsi(data, window=3)

    assert result.iloc[3:].dropna().eq(50.0).all()


def test_macd_matches_ema_composition():
    data = pd.Series([10, 11, 12, 11, 13, 12, 14, 13, 15, 16], dtype=float)
    fast, slow, signal = 3, 6, 2

    result = macd(data, fast=fast, slow=slow, signal=signal)

    expected_macd_line = ema(data, fast) - ema(data, slow)
    expected_signal_line = ema(expected_macd_line, signal)
    expected_histogram = expected_macd_line - expected_signal_line

    pd.testing.assert_series_equal(
        result["macd"], expected_macd_line, check_names=False
    )
    pd.testing.assert_series_equal(
        result["signal"], expected_signal_line, check_names=False
    )
    pd.testing.assert_series_equal(
        result["histogram"], expected_histogram, check_names=False
    )


def test_bollinger_bands_basic():
    data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    result = bollinger_bands(data, window=3, num_std=2.0)

    expected_std = math.sqrt(2.0 / 3.0)

    assert result["middle"].iloc[2] == pytest.approx(2.0)
    assert result["upper"].iloc[2] == pytest.approx(2.0 + 2 * expected_std)
    assert result["lower"].iloc[2] == pytest.approx(2.0 - 2 * expected_std)

    assert result["middle"].iloc[4] == pytest.approx(4.0)
    assert result["upper"].iloc[4] == pytest.approx(4.0 + 2 * expected_std)
    assert result["lower"].iloc[4] == pytest.approx(4.0 - 2 * expected_std)
