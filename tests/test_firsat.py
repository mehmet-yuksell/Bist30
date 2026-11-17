"""firsat.py için testler: elle kurulmuş düşüş ve dönüş senaryoları."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import firsat as fr


def _seri(kapanis, hacim=None, start="2023-01-02", aralik=0.02):
    idx = pd.bdate_range(start, periods=len(kapanis))
    c = pd.Series(np.asarray(kapanis, dtype=float), index=idx)
    o = c.shift(1).fillna(c.iloc[0])
    return pd.DataFrame({
        "Open": o,
        "High": np.maximum(o, c) * (1 + aralik),
        "Low": np.minimum(o, c) * (1 - aralik),
        "Close": c,
        "Volume": hacim if hacim is not None else np.full(len(c), 1e6),
    }, index=idx)


def _saglam_dusus_donus(dusus=(0.95, 0.95, 0.95), donus=1.09, sonra=12):
    """300 gün istikrarlı yükseliş (200 günlük EMA fiyatın epey altında), ardından 3 günde ~%14 düşüş, sonra dönüş günü ve yatay seyir."""
    yukselis = 100 * 1.002 ** np.arange(300)
    son = yukselis[-1]
    dusen = list(son * np.cumprod(dusus))
    donus_gunu = dusen[-1] * donus
    return list(yukselis) + dusen + [donus_gunu] + [donus_gunu] * sonra


def test_setup_trigger_and_signal_on_reversal_day():
    df = _seri(_saglam_dusus_donus())
    # Dönüş günü kapanışı önceki günün en yükseğini geçsin
    s = fr.firsat_hesapla(df)
    donus = df.index[303]
    assert s["kurulum"].iloc[300:303].any()
    assert s.loc[donus, "tetik"]
    assert s.loc[donus, "FIRSAT"] and not s.loc[donus, "BICAK"]
    assert s["tetik"].sum() == 1  # bölüm başına tek tetik


def test_no_setup_without_sharp_drop():
    df = _seri(_saglam_dusus_donus(dusus=(0.99, 0.99, 0.99)))
    assert not fr.firsat_hesapla(df)["kurulum"].any()


def test_no_setup_when_not_healthy_before_drop():
    # 300 gün düşüş trendi: düşüş öncesi 200 günlük EMA'nın altında
    kapanis = list(200 * 0.998 ** np.arange(300))
    kapanis += list(kapanis[-1] * np.cumprod([0.95, 0.95, 0.95])) + [kapanis[-1] * 0.9] * 10
    assert not fr.firsat_hesapla(_seri(kapanis))["kurulum"].any()


def test_new_52_week_low_marks_falling_knife():
    # Yükseliş kısa (60 gün) ve düşüş, 252 günlük dibin altına iner: K3
    kapanis = list(100 * 0.9995 ** np.arange(250)) + list(88 * 1.003 ** np.arange(60))
    son = kapanis[-1]
    dusen = list(son * np.cumprod([0.93, 0.93, 0.93, 0.93]))
    kapanis += dusen + [dusen[-1] * 1.10] + [dusen[-1] * 1.10] * 10
    s = fr.firsat_hesapla(_seri(kapanis))
    assert s["tetik"].sum() == 1
    assert s.loc[s["tetik"], "K3"].all()
    assert not s["FIRSAT"].any() and s["BICAK"].sum() == 1


def test_high_volume_close_at_low_marks_falling_knife():
    kapanis = _saglam_dusus_donus()
    hacim = np.full(len(kapanis), 1e6)
    hacim[302] = 5e6  # düşüşün son günü 5 kat hacim
    df = _seri(kapanis, hacim)
    df.iloc[302, df.columns.get_loc("Low")] = df["Close"].iloc[302] * 0.995  # kapanış dibe yakın
    s = fr.firsat_hesapla(df)
    donus = df.index[303]
    assert s.loc[donus, "K2"]
    assert s.loc[donus, "BICAK"] and not s.loc[donus, "FIRSAT"]
    assert s.loc[donus, "BICAK_RISKI"]


def test_conditions_do_not_look_ahead():
    df = _seri(_saglam_dusus_donus())
    tam = fr.firsat_hesapla(df)
    for kesim in (301, 303, 306):
        kisa = fr.firsat_hesapla(df.iloc[:kesim + 1])
        sutunlar = ["kurulum", "tetik", "FIRSAT", "BICAK", "BICAK_RISKI", "K1", "K2", "K3", "K4", "Stop"]
        pd.testing.assert_frame_equal(tam.iloc[:kesim + 1][sutunlar], kisa[sutunlar], check_freq=False)


def test_trade_enters_next_open_with_stop_below_swing_low():
    df = _seri(_saglam_dusus_donus())
    s = fr.firsat_hesapla(df)
    t = fr.islemler(s, s["FIRSAT"], kod="X", cost=0.0)
    assert len(t) == 1
    satir = t.iloc[0]
    donus_i = 303
    assert satir["giris"] == pytest.approx(df["Open"].iloc[donus_i + 1])
    dip = df["Low"].iloc[donus_i - 9:donus_i + 1].min()
    assert satir["stop"] == pytest.approx(dip - 0.5 * s["ATR"].iloc[donus_i])
    assert satir["gun"] <= fr.VARSAYILAN.zaman


def test_target_is_lower_of_prior_ema_and_2r():
    s = fr.firsat_hesapla(_seri(_saglam_dusus_donus()))
    hedef = fr.hedef_dizisi(s, giris=100.0, stop=95.0)
    ema_dun = s["EMA_hedef"].shift(1).to_numpy()
    np.testing.assert_allclose(hedef[1:], np.minimum(ema_dun[1:], 110.0))
