"""panel_veri.py için testler: fiyat girdisi, bölünme onarımı, haftalık bar ve sinyal listeleri."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bluetsman
import panel_veri as pv


def _yahoo_frame(close: np.ndarray, volume: np.ndarray | None = None) -> pd.DataFrame:
    """data.py'nin döndürdüğü biçim: Open/High/Low/Close/Adj Close/Volume, sütun adı 'Price'."""
    idx = pd.bdate_range("2024-01-01", periods=len(close))
    close = pd.Series(close, index=idx, dtype=float)
    df = pd.DataFrame(
        {
            "Open": close.shift(1).fillna(close.iloc[0]),
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Adj Close": close * 0.9,
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


# ---------------------------------------------------------------------------
# Girdi ve bölünme onarımı
# ---------------------------------------------------------------------------

def test_input_has_no_dividend_adjustment():
    close = np.linspace(100, 120, 150)
    girdi = pv.girdi(_yahoo_frame(close))
    assert list(girdi.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert girdi["Close"].to_numpy() == pytest.approx(close)  # Adj Close kullanılmaz (TradingView gibi)


def test_input_drops_bad_rows():
    df = _yahoo_frame(np.linspace(10, 20, 130))
    df.iloc[5, df.columns.get_loc("Volume")] = np.nan
    df.iloc[6, df.columns.get_loc("Open")] = np.nan
    girdi = pv.girdi(df)
    assert len(girdi) == 129  # OHLC eksik satır atılır
    assert girdi["Volume"].iloc[5] == 0.0


def _ohlc_with_jump(ratio: float, n: int = 40, at: int = 20, intraday: float = 0.02) -> pd.DataFrame:
    close = np.full(n, 100.0)
    close[at:] = 100.0 * ratio * (1 + intraday)
    df = _yahoo_frame(close)
    df.iloc[at, df.columns.get_loc("Open")] = 100.0 * ratio
    return df[pv.OHLC + ["Volume"]].astype(float)


def test_split_is_repaired_with_open_gap_ratio():
    df = _ohlc_with_jump(0.5)
    onarilmis, olaylar = pv.bolunme_onar(df)
    assert len(olaylar) == 1 and olaylar[0]["oran"] == pytest.approx(0.5)
    assert onarilmis["Close"].iloc[0] == pytest.approx(50.0)
    assert onarilmis["Volume"].iloc[0] == pytest.approx(2_000_000.0)
    assert onarilmis["Close"].iloc[-1] == pytest.approx(df["Close"].iloc[-1])


def test_real_market_gap_within_limits_is_not_repaired():
    assert pv.bolunme_onar(_ohlc_with_jump(1.20))[1] == []
    assert pv.bolunme_onar(_ohlc_with_jump(0.90, intraday=-0.04))[1] == []


def test_large_upward_gap_is_repaired():
    assert len(pv.bolunme_onar(_ohlc_with_jump(1.7))[1]) == 1


# ---------------------------------------------------------------------------
# Vadeler
# ---------------------------------------------------------------------------

def test_week_completion():
    assert pv.hafta_tamamlandi(pd.Timestamp("2026-11-20"), pd.Timestamp("2026-11-20"))
    assert not pv.hafta_tamamlandi(pd.Timestamp("2026-11-17"), pd.Timestamp("2026-11-20"))
    # Cuma tatil: perşembe son gün, etiket cuma -> pazartesi yeni veri gelene kadar yarım sayılır
    assert not pv.hafta_tamamlandi(pd.Timestamp("2026-11-19"), pd.Timestamp("2026-11-20"))


def test_weekly_bars():
    h = pv.haftalik(pv.girdi(_random_walk(20)))
    assert (h.index.dayofweek == 4).all()  # cuma etiketli
    first_week = pv.girdi(_random_walk(20)).loc[:"2024-01-05"]
    assert h["Open"].iloc[0] == first_week["Open"].iloc[0]
    assert h["High"].iloc[0] == first_week["High"].max()
    assert h["Close"].iloc[0] == first_week["Close"].iloc[-1]
    assert h["Volume"].iloc[0] == first_week["Volume"].sum()


def test_analysis_combines_buy_and_sell_on_both_horizons():
    df = _random_walk(400)
    kisa = pv.analiz(df, pv.KISA)
    orta = pv.analiz(df, pv.ORTA)
    assert len(kisa) == 400 and len(orta) == 80
    assert kisa["score"].equals(bluetsman.compute(pv.girdi(df))["score"])
    assert kisa["s_sell_score"].equals(bluetsman.compute_sell(pv.girdi(df))["sell_score"])
    assert orta["score"].equals(bluetsman.compute(pv.haftalik(pv.girdi(df)))["score"])
    assert pv.analiz(_random_walk(50), pv.KISA) is None  # 60 günden az
    assert pv.analiz(_random_walk(150), pv.ORTA) is None  # 40 haftadan az


# ---------------------------------------------------------------------------
# Sinyal listeleri
# ---------------------------------------------------------------------------

def _sonuc(buy: list[int] = (), kar_al: list[int] = (), sat: list[int] = (), n: int = 12) -> pd.DataFrame:
    idx = pd.bdate_range("2026-11-02", periods=n)
    df = pd.DataFrame({"Close": np.linspace(100, 111, n), "score": 50.0, "buy_signal": False,
                       "s_kar_al": False, "s_sat": False, "s_sell_score": 0.0}, index=idx)
    for i in buy:
        df.iloc[i, df.columns.get_loc("buy_signal")] = True
        df.iloc[i, df.columns.get_loc("score")] = 80.0
    for col, positions, score in (("s_kar_al", kar_al, 45.0), ("s_sat", sat, 66.0)):
        for i in positions:
            df.iloc[i, df.columns.get_loc(col)] = True
            df.iloc[i, df.columns.get_loc("s_sell_score")] = score
    return df


def test_buy_signals_window_and_order():
    s = _sonuc(buy=[1, 8, 11])
    sinyaller = pv.alim_sinyalleri(s, 5)
    assert [x["once"] for x in sinyaller] == [0, 3]  # 1. bar pencere dışında
    assert sinyaller[1]["skor"] == 80.0 and sinyaller[1]["fiyat"] == pytest.approx(108.0)
    assert sinyaller[1]["degisim"] == pytest.approx((111 / 108 - 1) * 100)


def test_sell_signals_types_and_priority():
    s = _sonuc(kar_al=[7, 10], sat=[10])
    sinyaller = pv.satis_sinyalleri(s, 10)
    assert [(x["once"], x["ad"]) for x in sinyaller] == [(1, "SAT"), (4, "KAR AL")]
    assert pv.son_satis(s, 10)["skor"] == 66.0
    assert pv.son_satis(s, 1) is None


def test_open_buy_requires_no_later_sell():
    assert pv.acik_alim(_sonuc(buy=[8]), 6)["once"] == 3
    assert pv.acik_alim(_sonuc(buy=[8], kar_al=[10]), 6) is None  # alımdan sonra KAR AL geldi
    assert pv.acik_alim(_sonuc(buy=[8], sat=[7]), 6)["once"] == 3  # satış alımdan önceydi
    assert pv.acik_alim(_sonuc(buy=[2]), 6) is None  # pencere dışında


def test_signal_history_marks_kinds_and_forward_return():
    s = _sonuc(buy=[0], kar_al=[3], sat=[9])
    gecmis = pv.sinyal_gecmisi(s, horizon=2)
    assert list(gecmis["tur"]) == ["sat", "kar_al", "alim"]  # en yeni üstte
    assert list(gecmis["score"]) == [66.0, 45.0, 80.0]
    assert gecmis["forward_return"].iloc[2] == pytest.approx((102 / 100 - 1) * 100)
    assert gecmis["forward_return"].iloc[0] == pytest.approx((111 / 109 - 1) * 100)
