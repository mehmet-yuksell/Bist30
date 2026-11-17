"""gunluk.py için testler: kayıt satırları, tekrar önleme, ileri test."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gunluk as gl
import panel_veri as pv


def _sonuc(**son):
    idx = pd.bdate_range("2026-11-10", periods=3)
    satir = {"Close": 100.0, "ATR": 4.0, "Alim_skor": 72.0, "Satis_skor": 45.0, "RSI": 55.0,
             "Stop": 94.0, "Hedef": 112.0, pv.ALIM_SUTUNU: False, "SAT": False, "KAR_AL": False, "CIK": False}
    satir.update(son)
    return pd.DataFrame([satir] * 3, index=idx)


def test_buy_row_with_grade_and_levels():
    rows = gl.vade_satirlari(_sonuc(**{pv.ALIM_SUTUNU: True}), pv.KISA, "THYAO", lambda s, v: "A")
    assert rows == [{"tarih": "2026-11-12", "vade": "kisa", "tur": "AL", "kod": "THYAO", "skor": 72.0, "not": "A",
                     "giris_referans": 100.0, "stop": 94.0, "hedef": 112.0}]


def test_sell_row_mirrors_levels_and_takes_priority():
    rows = gl.vade_satirlari(_sonuc(KAR_AL=True, CIK=True), pv.KISA, "SISE", lambda s, v: None)
    assert len(rows) == 1 and rows[0]["tur"] == "KAR_AL"
    # kısa vade: stop = kapanış + 1,5 ATR, hedef = kapanış − 3 ATR
    assert rows[0]["stop"] == pytest.approx(106.0) and rows[0]["hedef"] == pytest.approx(88.0)
    rows = gl.vade_satirlari(_sonuc(SAT=True), pv.ORTA, "SISE", lambda s, v: None)
    assert rows[0]["stop"] == pytest.approx(108.0) and rows[0]["hedef"] == pytest.approx(84.0)  # 2 ATR / 4 ATR


def test_no_signal_no_rows():
    assert gl.vade_satirlari(_sonuc(), pv.KISA, "X", lambda s, v: None) == []


def test_append_skips_duplicates():
    satir = {"tarih": "2026-11-12", "vade": "kisa", "tur": "AL", "kod": "A", "skor": 70.0, "not": "A",
             "giris_referans": 10.0, "stop": 9.0, "hedef": 12.0}
    g = gl.ekle(pd.DataFrame(columns=gl.SUTUNLAR), [satir])
    g = gl.ekle(g, [satir, {**satir, "kod": "B"}])
    assert list(g["kod"]) == ["A", "B"]


def test_read_missing_file_returns_empty(tmp_path):
    assert gl.oku(tmp_path / "yok.csv").empty
    yol = tmp_path / "g.csv"
    gl.ekle(pd.DataFrame(columns=gl.SUTUNLAR), [{"tarih": "2026-11-12", "vade": "kisa", "tur": "SAT", "kod": "A",
                                                  "skor": 61.0, "not": "", "giris_referans": 10.0, "stop": 11.0,
                                                  "hedef": 8.0}]).to_csv(yol, index=False)
    okunan = gl.oku(yol)
    assert okunan["not"].iloc[0] == "" and okunan["tur"].iloc[0] == "SAT"


def _fiyat(n=160, son_gunler=None):
    idx = pd.bdate_range("2026-03-02", periods=n)
    c = np.full(n, 100.0)
    df = pd.DataFrame({"Open": c, "High": c * 1.005, "Low": c * 0.995, "Close": c, "Adj Close": c,
                       "Volume": np.full(n, 1e6)}, index=idx)
    for i, (o, h, lo, cl) in (son_gunler or {}).items():
        df.iloc[i, :4] = [o, h, lo, cl]
        df.iloc[i, 4] = cl
    return df


def test_forward_test_uses_next_open_and_logged_levels():
    df = _fiyat(son_gunler={150: (101, 102, 100, 101), 152: (103, 111, 102, 110)})
    tarih = df.index[149].date().isoformat()
    g = pd.DataFrame([{"tarih": tarih, "vade": "kisa", "tur": "AL", "kod": "T", "skor": 70.0, "not": "A",
                       "giris_referans": 100.0, "stop": 95.0, "hedef": 108.0}])
    t = gl.degerlendir(g, {"T": df}, None)
    assert len(t) == 1
    satir = t.iloc[0]
    assert satir["giris"] == pytest.approx(101.0)     # ertesi gün açılışı
    assert (satir["sonuc"], satir["gun"]) == ("hedef", 3)
    assert satir["cikis"] == pytest.approx(108.0)


def test_forward_test_rescales_levels_after_later_adjustment():
    # Kayıttan sonra temettü düzeltmesi geçmişi %10 aşağı ölçekledi: sinyal günü kapanışı artık 90
    df = _fiyat(n=200)  # 20 günlük pencere dolsun
    df["Adj Close"] = df["Close"] * 0.9
    tarih = df.index[149].date().isoformat()
    g = pd.DataFrame([{"tarih": tarih, "vade": "kisa", "tur": "AL", "kod": "T", "skor": 70.0, "not": "",
                       "giris_referans": 100.0, "stop": 95.0, "hedef": 105.0}])
    satir = gl.degerlendir(g, {"T": df}, None).iloc[0]
    assert satir["giris"] == pytest.approx(90.0)  # düzeltilmiş ertesi gün açılışı
    assert satir["stop"] == pytest.approx(85.5) and satir["hedef"] == pytest.approx(94.5)
    assert satir["sonuc"] == "zaman"
    # pencere dolmamış (açık) işlemde de ölçeklenmiş seviyeler gösterilir
    acik = gl.degerlendir(g, {"T": df.iloc[:160]}, None).iloc[0]
    assert acik["sonuc"] == "acik" and acik["stop"] == pytest.approx(85.5)


def test_summary_and_threshold():
    t = pd.DataFrame({"vade": ["kisa"] * 3, "tur": ["AL", "AL", "SAT"], "kod": ["A", "B", "C"],
                      "tarih": pd.to_datetime(["2026-11-10"] * 3), "sonuc": ["hedef", "acik", "stop"],
                      "r": [2.0, 0.0, -1.0], "getiri": [0.04, 0.0, -0.02], "gun": [3, np.nan, 2],
                      "mfe_r": [2.0, 0.0, 0.2], "mae_r": [-0.2, 0.0, -1.0]})
    o = gl.ozetle(t).set_index("tur")
    assert o.loc["AL", "sinyal"] == 1 and o.loc["AL", "acik"] == 1
    assert gl.tamamlanan(t) == 2 and not gl.yeterli_mi(t)
