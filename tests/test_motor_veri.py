"""motor_veri.py ve tarayici_motor.alim_skor_kalemleri için testler."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import motor_veri
import tarayici_motor as motor


def _yahoo_frame(close: np.ndarray, volume: np.ndarray | None = None, adj_factor=None) -> pd.DataFrame:
    """data.py'nin döndürdüğü biçim: Open/High/Low/Close/Adj Close/Volume, sütun adı 'Price'."""
    idx = pd.bdate_range("2024-01-01", periods=len(close))
    close = pd.Series(close, index=idx, dtype=float)
    df = pd.DataFrame(
        {
            "Open": close.shift(1).fillna(close.iloc[0]),
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Adj Close": close * (adj_factor if adj_factor is not None else 1.0),
            "Volume": volume if volume is not None else np.full(len(close), 1_000_000.0),
        },
        index=idx,
    )
    df.columns.name = "Price"
    return df


def _random_walk(n: int = 400, seed: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 50 * np.exp(np.cumsum(rng.normal(0.001, 0.02, n)))
    return _yahoo_frame(close, rng.uniform(5e5, 2e6, n))


def test_motor_girdisi_applies_dividend_factor_and_keeps_last_price():
    close = np.linspace(100, 120, 150)
    factor = np.where(np.arange(150) < 100, 0.9, 1.0)  # 100. günde temettü
    girdi = motor_veri.motor_girdisi(_yahoo_frame(close, adj_factor=factor))

    assert list(girdi.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert girdi["Close"].iloc[0] == pytest.approx(close[0] * 0.9)
    assert girdi["High"].iloc[0] == pytest.approx(close[0] * 1.01 * 0.9)
    assert girdi["Close"].iloc[-1] == pytest.approx(close[-1])  # güncel fiyat değişmez
    assert girdi["Volume"].iloc[0] == 1_000_000.0


def test_motor_girdisi_without_adj_close_and_with_bad_rows():
    df = _yahoo_frame(np.linspace(10, 20, 130)).drop(columns="Adj Close")
    df.iloc[5, df.columns.get_loc("Volume")] = np.nan
    df.iloc[6, df.columns.get_loc("Open")] = np.nan
    girdi = motor_veri.motor_girdisi(df)

    assert len(girdi) == 129  # OHLC eksik satır atılır
    assert girdi["Volume"].iloc[5] == 0.0
    assert girdi["Close"].iloc[-1] == pytest.approx(20.0)


def test_analiz_needs_120_bars():
    assert motor_veri.analiz(_random_walk(119)) is None
    sonuc = motor_veri.analiz(_random_walk(200))
    assert {"Alim_skor", "AL", "Stop", "Hedef", "RSI", "Hacim_kat"} <= set(sonuc.columns)


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_score_breakdown_sums_to_engine_score(seed):
    df = _random_walk(400, seed)
    girdi = motor_veri.motor_girdisi(df)
    kalemler = motor.alim_skor_kalemleri(girdi, motor_veri.AYAR)
    sonuc = motor.hisse_analiz(girdi, motor_veri.AYAR)

    assert list(kalemler.columns) == list(motor.ALIM_KALEMLERI)
    assert sum(motor.ALIM_KALEMLERI.values()) == 100
    np.testing.assert_allclose(kalemler.sum(axis=1), sonuc["Alim_skor"], atol=1e-9)
    for column, maximum in motor.ALIM_KALEMLERI.items():
        assert kalemler[column].between(0, maximum + 1e-9).all()


def _sonuc_with_signals(positions: list[int], n: int = 20) -> pd.DataFrame:
    idx = pd.bdate_range("2026-10-01", periods=n)
    close = pd.Series(np.arange(100.0, 100.0 + n), index=idx)
    sonuc = pd.DataFrame({"Close": close, "Alim_skor": 50.0, "Stop": close - 2, "Hedef": close + 4, "AL": False})
    for pos in positions:
        sonuc.iloc[pos, sonuc.columns.get_loc("AL")] = True
        sonuc.iloc[pos, sonuc.columns.get_loc("Alim_skor")] = 70.0 + pos
    return sonuc


def test_al_sinyalleri_window_and_order():
    sonuc = _sonuc_with_signals([5, 16, 19])

    sinyaller = motor_veri.al_sinyalleri(sonuc, 5)

    assert [s["once"] for s in sinyaller] == [0, 3]
    assert sinyaller[1]["fiyat"] == 116.0
    assert sinyaller[1]["degisim"] == pytest.approx((119 / 116 - 1) * 100)
    assert motor_veri.son_al(sonuc, 5)["once"] == 0
    assert motor_veri.son_al(_sonuc_with_signals([5]), 5) is None


def test_al_sinyalleri_matches_engine_son_sinyal():
    sonuc = _sonuc_with_signals([12, 15])
    satir, once = motor.son_sinyal(sonuc, "AL", 10)
    assert motor_veri.son_al(sonuc, 10)["once"] == once
    assert motor_veri.son_al(sonuc, 10)["skor"] == satir["Alim_skor"]


def test_al_gecmisi_forward_return():
    sonuc = _sonuc_with_signals([2, 18])
    history = motor_veri.al_gecmisi(sonuc, horizon=3)

    assert list(history.index) == [sonuc.index[18], sonuc.index[2]]
    assert history["forward_return"].iloc[1] == pytest.approx((105 / 102 - 1) * 100)
    assert np.isnan(history["forward_return"].iloc[0])
