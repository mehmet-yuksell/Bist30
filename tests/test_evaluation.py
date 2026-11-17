"""evaluation.py için testler: elle kurulmuş küçük fiyat serileri."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import evaluation as ev
from evaluation import Kurallar, simule_et

UZUN = Kurallar(timeout=5, cost=0.0)


def bars(rows):
    """rows: (open, high, low, close) listesi -> numpy dizileri."""
    a = np.array(rows, dtype=float)
    return a[:, 0], a[:, 1], a[:, 2], a[:, 3]


def test_entry_is_next_day_open():
    o, h, lo, c = bars([(100, 101, 99, 100), (102, 103, 101, 102), (102, 103, 101, 102),
                        (102, 103, 101, 102), (102, 103, 101, 102), (102, 103, 101, 102)])
    sonuc = simule_et(o, h, lo, c, 0, stop=95, hedef=120, k=UZUN)
    assert sonuc["giris"] == 102  # sinyal günü kapanışı (100) değil, ertesi gün açılışı
    assert sonuc["giris_i"] == 1


def test_target_on_third_day():
    o, h, lo, c = bars([
        (100, 100, 100, 100),   # 0: sinyal
        (100, 101, 99, 100),    # 1: giriş
        (100, 103, 99, 102),    # 2
        (102, 111, 101, 109),   # 3: hedef (110)
        (109, 112, 108, 110),
    ])
    sonuc = simule_et(o, h, lo, c, 0, stop=95, hedef=110, k=UZUN)
    assert (sonuc["sonuc"], sonuc["gun"]) == ("hedef", 3)
    assert sonuc["cikis"] == 110
    assert sonuc["r"] == pytest.approx(2.0)  # (110-100)/(100-95)


def test_same_bar_target_and_stop_counts_as_stop():
    o, h, lo, c = bars([(100, 100, 100, 100), (100, 101, 99, 100), (100, 112, 94, 100)])
    sonuc = simule_et(o, h, lo, c, 0, stop=95, hedef=110, k=UZUN)
    assert (sonuc["sonuc"], sonuc["gun"]) == ("stop", 2)
    assert sonuc["r"] == pytest.approx(-1.0)


def test_gap_through_stop_exits_at_open():
    o, h, lo, c = bars([(100, 100, 100, 100), (100, 101, 99, 100), (90, 92, 89, 91)])
    sonuc = simule_et(o, h, lo, c, 0, stop=95, hedef=110, k=UZUN)
    assert sonuc["sonuc"] == "stop" and sonuc["cikis"] == 90
    assert sonuc["r"] == pytest.approx(-2.0)  # kayıp 1R'yi aşabilir


def test_entry_open_beyond_stop_is_invalid():
    o, h, lo, c = bars([(100, 100, 100, 100), (94, 96, 93, 95)])
    assert simule_et(o, h, lo, c, 0, stop=95, hedef=110, k=UZUN)["sonuc"] == "gecersiz"


def test_timeout_exits_at_last_close_and_cost_applied():
    rows = [(100, 100, 100, 100)] + [(100, 102, 98, 101)] * 4 + [(101, 103, 99, 103)]
    o, h, lo, c = bars(rows)
    k = Kurallar(timeout=5, cost=0.002)
    sonuc = simule_et(o, h, lo, c, 0, stop=95, hedef=110, k=k)
    assert (sonuc["sonuc"], sonuc["gun"]) == ("zaman", 5)
    assert sonuc["cikis"] == 103
    assert sonuc["getiri"] == pytest.approx(0.03 - 0.002)
    assert sonuc["r"] == pytest.approx((0.03 - 0.002) * 100 / 5)
    assert sonuc["mfe"] == pytest.approx(0.03) and sonuc["mae"] == pytest.approx(-0.02)


def test_incomplete_window_is_open():
    o, h, lo, c = bars([(100, 100, 100, 100), (100, 101, 99, 100), (100, 101, 99, 100)])
    assert simule_et(o, h, lo, c, 0, stop=95, hedef=110, k=UZUN)["sonuc"] == "acik"
    assert simule_et(o, h, lo, c, 2, stop=95, hedef=110, k=UZUN)["sonuc"] == "acik"


def test_short_side_mirrors_long():
    o, h, lo, c = bars([(100, 100, 100, 100), (100, 101, 99, 100), (99, 100, 89, 90)])
    sonuc = simule_et(o, h, lo, c, 0, stop=105, hedef=90, k=Kurallar(timeout=5, side=-1, cost=0.0))
    assert (sonuc["sonuc"], sonuc["gun"]) == ("hedef", 2)
    assert sonuc["r"] == pytest.approx(2.0)
    o, h, lo, c = bars([(100, 100, 100, 100), (100, 101, 99, 100), (100, 106, 89, 100)])
    sonuc = simule_et(o, h, lo, c, 0, stop=105, hedef=90, k=Kurallar(timeout=5, side=-1, cost=0.0))
    assert sonuc["sonuc"] == "stop"


def _trades(rs, sonuclar=None, gunler=None, start="2024-12-20"):
    n = len(rs)
    return pd.DataFrame({
        "kod": ["X"] * n,
        "tarih": pd.bdate_range(start, periods=n),
        "sonuc": sonuclar or ["hedef" if r > 0 else "stop" for r in rs],
        "r": rs,
        "getiri": [r / 50 for r in rs],
        "gun": gunler or [3] * n,
        "mfe_r": [1.0] * n,
        "mae_r": [-0.5] * n,
    })


def test_summary_metrics():
    t = _trades([2.0, -1.0, -1.0, -1.0, 2.0, 0.5], gunler=[2, 1, 1, 1, 6, 9],
                sonuclar=["hedef", "stop", "stop", "stop", "hedef", "zaman"])
    s = ev.ozet(t)
    assert s["sinyal"] == 6
    assert s["hedef_pct"] == pytest.approx(100 * 2 / 6)
    assert s["stop_pct"] == pytest.approx(50.0)
    assert s["beklenen_r"] == pytest.approx(1.5 / 6)
    assert s["kar_faktoru"] == pytest.approx(4.5 / 3)
    assert s["kayip_serisi"] == 3
    assert s["hedef_medyan_gun"] == pytest.approx(4.0)


def test_open_and_invalid_are_counted_not_measured():
    t = _trades([2.0, -1.0, 0.0], sonuclar=["hedef", "acik", "gecersiz"])
    s = ev.ozet(t)
    assert (s["sinyal"], s["acik"], s["gecersiz"]) == (1, 1, 1)
    assert s["beklenen_r"] == pytest.approx(2.0)


def test_split_by_signal_date():
    t = _trades([1.0] * 10, start="2024-12-24")  # 24-31 Aralık 2024: 6 iş günü
    donem = ev.doneme_gore(t)
    assert donem["GELİŞTİRME"]["sinyal"] == 6
    assert donem["TEST"]["sinyal"] == 4


def test_index_return_uses_same_dates():
    idx = pd.bdate_range("2025-01-01", periods=5)
    endeks = pd.DataFrame({"Open": [100, 101, 102, 103, 104], "Close": [101, 102, 103, 104, 110]}, index=idx)
    t = pd.DataFrame({"giris_tarihi": [idx[1]], "cikis_tarihi": [idx[4]]})
    assert ev.endeks_getirisi(t, endeks).iloc[0] == pytest.approx(110 / 101 - 1)


def test_completed_weeks_drop_partial_week():
    haftalik = pd.DataFrame({"Close": [1, 2, 3]}, index=pd.to_datetime(["2026-11-06", "2026-11-13", "2026-11-20"]))
    assert len(ev.tamamlanmis_haftalar(haftalik, pd.Timestamp("2026-11-17"))) == 2
    assert len(ev.tamamlanmis_haftalar(haftalik, pd.Timestamp("2026-11-20"))) == 3


def test_islemler_skips_warmup_and_maps_dates():
    idx = pd.bdate_range("2025-01-01", periods=8)
    df = pd.DataFrame({"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0}, index=idx)
    sinyal = pd.Series([True, False, False, True, False, False, False, False], index=idx)
    t = ev.islemler(df, sinyal, pd.Series(95.0, index=idx), pd.Series(110.0, index=idx),
                    Kurallar(timeout=3), kod="X", ilk_bar=2)
    assert list(t["tarih"]) == [idx[3]]
    assert t["giris_tarihi"].iloc[0] == idx[4]
    assert t["sonuc"].iloc[0] == "zaman"


def test_delayed_entry_keeps_signal_levels_and_date():
    idx = pd.bdate_range("2025-01-01", periods=6)
    df = pd.DataFrame({
        "Open":  [100, 101, 104, 104, 104, 104],
        "High":  [100, 102, 105, 111, 105, 105],
        "Low":   [100, 100, 103, 103, 103, 103],
        "Close": [100, 101, 104, 104, 104, 104],
    }, index=idx, dtype=float)
    sinyal = pd.Series([True, False, False, False, False, False], index=idx)
    t = ev.islemler_gecikmeli(df, sinyal, pd.Series(95.0, index=idx), pd.Series(110.0, index=idx),
                              Kurallar(timeout=4, cost=0.0), kod="X")
    satir = t.iloc[0]
    assert satir["tarih"] == idx[0]                 # dönem asıl sinyal tarihine göre
    assert satir["giris_tarihi"] == idx[2]          # 1 bar gecikmeli giriş
    assert satir["giris"] == 104
    assert (satir["sonuc"], satir["gun"]) == ("hedef", 3)  # asıl sinyalden 3 bar
    assert satir["r"] == pytest.approx((110 - 104) / (104 - 95))
