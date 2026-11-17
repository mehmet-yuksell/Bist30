"""filtreler.py için testler; en önemlisi geleceğe bakmama."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import filtreler as f


def _gunluk(n=400, seed=0, start="2023-01-02"):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(start, periods=n)
    c = pd.Series(50 * np.exp(np.cumsum(rng.normal(0.0005, 0.02, n))), index=idx)
    o = c.shift(1).fillna(c.iloc[0]) * (1 + rng.normal(0, 0.005, n))
    return pd.DataFrame({"Open": o, "High": np.maximum(o, c) * 1.01, "Low": np.minimum(o, c) * 0.99,
                         "Close": c, "Volume": rng.uniform(1e5, 1e6, n)}, index=idx)


def test_features_do_not_look_ahead():
    hisse, endeks = _gunluk(seed=1), _gunluk(seed=2)
    endeks = endeks.drop(endeks.index[100:105])  # endekste eksik günler (tatil gibi)
    tam = f.gunluk_ozellikler(hisse, endeks)
    kesim = hisse.index[300]
    kisa = f.gunluk_ozellikler(hisse.loc[:kesim], endeks.loc[:kesim])
    pd.testing.assert_frame_equal(tam.loc[:kesim], kisa, check_freq=False)


def test_index_aligned_with_last_known_value():
    hisse = _gunluk(10)
    endeks = _gunluk(10, seed=3).drop(hisse.index[5])  # 6. gün endeks verisi yok
    oz = f.gunluk_ozellikler(hisse, endeks)
    # 6. gün için endeksin 5. günkü değeri kullanılır (rs20 NaN olsa da hizalama hatasız)
    assert len(oz) == 10 and oz.index.equals(hisse.index)


def test_masks_match_definitions():
    idx = pd.bdate_range("2025-01-01", periods=3)
    oz = pd.DataFrame({
        "xu_ust_50": [True, False, True], "rs20": [0.03, 0.03, -0.01], "rs60": [0.03, 0.01, 0.05],
        "tl_hacim20": [25e6, 5e6, np.nan], "ust_ema_200": [True, False, True],
        "bosluk": [0.01, 0.06, 0.02], "gun_degisim": [0.02, 0.096, 0.08],
    }, index=idx)
    sonuc = pd.DataFrame({"Close": [110, 120, 105], "EMA_yavas": [100, 100, 100], "ATR": [5, 5, 5]}, index=idx)
    assert f.maske("F1", 50, oz, sonuc).tolist() == [True, False, True]
    assert f.maske("F2", 0.02, oz, sonuc).tolist() == [True, False, False]
    assert f.maske("F3", 2.5, oz, sonuc).tolist() == [True, False, True]  # uzaklık 2, 4, 1 ATR
    assert f.maske("F4", 20e6, oz, sonuc).tolist() == [True, False, False]  # NaN geçmez
    assert f.maske("F5", 200, oz, sonuc).tolist() == [True, False, True]
    assert f.maske("F6", 0.05, oz, sonuc).tolist() == [True, False, True]
    assert f.maske("F8", 0.095, oz, sonuc).tolist() == [True, False, True]
    with pytest.raises(ValueError):
        f.maske("F7", "Low", oz, sonuc)


def test_confirmation_uses_next_bar_close():
    idx = pd.bdate_range("2025-01-01", periods=4)
    sonuc = pd.DataFrame({"High": [12, 12, 12, 12], "Low": [10, 10, 10, 10],
                          "Close": [11, 9.5, 11.5, 11]}, index=idx)
    assert f.teyit(sonuc, "Low").tolist() == [False, True, True, False]  # son barın ertesi yok
    assert f.teyit(sonuc, "Mid").tolist() == [False, True, True, False]  # orta nokta 11
    assert f.teyit(sonuc, "Close").tolist() == [False, True, False, False]


def test_weekly_alignment_uses_last_trading_day_of_week():
    gunluk_idx = pd.bdate_range("2025-01-06", periods=10)  # iki hafta, Pzt-Cuma
    oz = pd.DataFrame({"x": range(10)}, index=gunluk_idx)
    hafta = pd.DatetimeIndex(["2025-01-10", "2025-01-17"])
    assert f.zaman_dilimine_hizala(oz, hafta)["x"].tolist() == [4, 9]
    # Cuma tatilse haftanın son işlem günü (Perşembe) kullanılır
    oz2 = oz.drop(pd.Timestamp("2025-01-17"))
    assert f.zaman_dilimine_hizala(oz2, hafta)["x"].tolist() == [4, 8]


def test_threshold_choice_counts_improving_years():
    assert f.yillik_tutarlilik({2021: 0.1, 2022: -0.05, 2023: 0.2, 2024: 0.0}) == (2, -0.05)
    assert f.yillik_tutarlilik({2021: np.nan}) == (0, -np.inf)


def test_engine_filters_match_evaluated_filters():
    """tarayici_motor'daki ORTA_VADE filtreleri, raporda değerlendirilen F1/F5/F8 ile aynı sinyalleri vermeli."""
    import tarayici_motor as motor

    hisse, endeks = _gunluk(n=1500, seed=7, start="2019-01-01"), _gunluk(n=1500, seed=8, start="2019-01-01")
    sonuc = motor.hisse_analiz(hisse, motor.ORTA_VADE, endeks)
    ayar = motor.ORTA_VADE.filtreler

    oz = f.zaman_dilimine_hizala(f.gunluk_ozellikler(hisse, endeks), sonuc.index)
    beklenen = (sonuc["AL"]
                & f.maske("F1", ayar.piyasa_ema, oz, sonuc)
                & f.maske("F5", ayar.uzun_trend_ema, oz, sonuc)
                & f.maske("F8", ayar.tavan_esik, oz, sonuc))
    pd.testing.assert_series_equal(sonuc["AL_filtreli"], beklenen, check_names=False)
    # skor ve ham AL değişmez
    ham = motor.sinyalleri_hesapla(motor.haftaliga_cevir(hisse), motor.ORTA_VADE)
    pd.testing.assert_series_equal(sonuc["AL"], ham["AL"])
    pd.testing.assert_series_equal(sonuc["Alim_skor"], ham["Alim_skor"])


def test_engine_filters_off_or_missing_index():
    import tarayici_motor as motor

    hisse = _gunluk(n=300, seed=9)
    kisa = motor.hisse_analiz(hisse, motor.KISA_VADE)
    assert kisa["AL_filtreli"].equals(kisa["AL"])  # kısa vadede filtre yok
    with pytest.raises(ValueError):
        motor.hisse_analiz(hisse, motor.ORTA_VADE)  # piyasa filtresi endeks ister
