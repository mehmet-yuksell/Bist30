"""panel_veri.py için testler."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import panel_veri as pv


def test_week_completion():
    assert pv.hafta_tamamlandi(pd.Timestamp("2026-11-20"), pd.Timestamp("2026-11-20"))
    assert not pv.hafta_tamamlandi(pd.Timestamp("2026-11-17"), pd.Timestamp("2026-11-20"))
    # Cuma tatil: perşembe son gün, etiket cuma -> pazartesi yeni veri gelene kadar yarım sayılır
    assert not pv.hafta_tamamlandi(pd.Timestamp("2026-11-19"), pd.Timestamp("2026-11-20"))


def _satis_sonuc(rows):
    idx = pd.bdate_range("2026-11-02", periods=len(rows))
    return pd.DataFrame(rows, index=idx, columns=["SAT", "KAR_AL", "CIK", "Satis_skor", "RSI"])


def test_sell_warning_priority_and_recency():
    s = _satis_sonuc([
        (False, True, False, 45.0, 60.0),
        (False, False, False, 10.0, 55.0),
        (False, True, True, 50.0, 52.0),   # son bar: KAR AL ve ÇIK birlikte -> KAR AL
    ])
    assert pv.satis_uyarisi(s)["ad"] == "KAR AL"
    s.iloc[-1, s.columns.get_loc("SAT")] = True
    assert pv.satis_uyarisi(s)["ad"] == "SAT"
    assert pv.satis_uyarisi(s, -2) is None
    assert pv.son_satis(s.iloc[:2], 5) == {"tur": "KAR_AL", "ad": "KAR AL", "skor": 45.0, "rsi": 60.0, "once": 1}
    assert pv.son_satis(s.iloc[1:2], 5) is None


def _firsat_son(**kolonlar):
    varsayilan = {"Close": 100.0, "FIRSAT": False, "BICAK_RISKI": False, "kurulum_penceresi": False,
                  "tetik": False, "K1": False, "K2": False, "K3": False, "K4": False,
                  "uyari_hisseye_ozel": False, "uyari_piyasa": False, "Stop": 90.0, "EMA_hedef": 105.0,
                  "RSI2": 4.0}
    varsayilan.update(kolonlar)
    idx = pd.bdate_range("2026-11-02", periods=7)
    df = pd.DataFrame([varsayilan] * 7, index=idx)
    df.iloc[0, df.columns.get_loc("Close")] = 110.0
    return df


def test_firsat_status_flags_and_levels():
    d = pv.firsat_durumu(_firsat_son(FIRSAT=True, tetik=True, kurulum_penceresi=True))
    assert d["firsat"] and not d["bekliyor"] and not d["bicak"]
    assert d["hedef_2r"] == pytest.approx(120.0)  # 100 + 2 × (100 − 90)
    assert d["dusus5"] == pytest.approx(0.0)
    d = pv.firsat_durumu(_firsat_son(kurulum_penceresi=True))
    assert d["bekliyor"]
    d = pv.firsat_durumu(_firsat_son(kurulum_penceresi=True, BICAK_RISKI=True, K1=True, K3=True))
    assert d["bicak"] and not d["bekliyor"] and d["kriterler"] == ["K1", "K3"]


def test_trade_statistics_for_histogram():
    t = pd.DataFrame({"sonuc": ["hedef", "hedef", "stop", "acik"], "gun": [3, 7, 2, np.nan], "r": [2.0, 2.0, -1.0, 0.0]})
    s = pv.islem_istatistigi(t)
    assert s["sinyal"] == 3 and s["hedef_gunleri"] == [3, 7]
    assert s["medyan_gun"] == pytest.approx(5.0)
    assert pv.islem_istatistigi(pd.DataFrame())["sinyal"] == 0


def test_analysis_uses_filtered_signal_column_on_both_horizons():
    rng = np.random.default_rng(4)
    n = 800
    idx = pd.bdate_range("2023-01-02", periods=n)
    c = pd.Series(50 * np.exp(np.cumsum(rng.normal(0.0008, 0.02, n))), index=idx)
    df = pd.DataFrame({"Open": c.shift(1).fillna(c.iloc[0]), "High": c * 1.01, "Low": c * 0.99,
                       "Close": c, "Volume": rng.uniform(1e5, 1e6, n)}, index=idx)
    endeks = pv.endeks_girdisi(df.assign(Close=c * 0 + 100 + np.arange(n) * 0.1))
    kisa = pv.analiz(df, pv.KISA)
    orta = pv.analiz(df, pv.ORTA, endeks)
    assert pv.ALIM_SUTUNU in kisa and pv.ALIM_SUTUNU in orta
    assert len(orta) < len(kisa)  # haftalık
    assert pv.analiz(df.iloc[:100], pv.KISA) is None
