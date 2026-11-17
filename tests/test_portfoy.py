"""portfoy.py için testler: elle hesaplanabilen küçük senaryolar."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import portfoy as pf

GUNLER = pd.bdate_range("2025-01-01", periods=6)


def _kapanis(kodlar, fiyat=100.0):
    return pd.DataFrame(fiyat, index=GUNLER, columns=kodlar)


def _rejim(zayif=False, oynak=False):
    return pd.DataFrame({"yuksek_oynaklik": oynak, "piyasa_zayif": zayif}, index=GUNLER)


def _aday(kod, sistem="trend", giris=100.0, stop=95.0, cikis=110.0, cikis_gun=3, oncelik=70.0, giris_gun=1):
    return {
        "kod": kod, "sistem": sistem, "tarih": GUNLER[giris_gun - 1], "giris_tarihi": GUNLER[giris_gun],
        "giris": giris, "stop": stop, "cikis_tarihi": GUNLER[cikis_gun] if cikis_gun is not None else pd.NaT,
        "cikis": cikis, "oncelik": oncelik,
    }


def test_position_size_from_one_percent_risk():
    # 100.000 × %1 = 1.000 TL risk / 10 TL birim risk = 100 adet (10.000 TL < %20 sınırı)
    adaylar = pd.DataFrame([_aday("A", stop=90.0)])
    _, kayit = pf.simule(adaylar, _kapanis(["A"]), _rejim(), GUNLER[0], GUNLER[-1])
    assert kayit["adet"].iloc[0] == 100


def test_position_capped_at_twenty_percent():
    # 1.000 TL risk / 1 TL = 1.000 adet = 100.000 TL; %20 sınırı 200 adet
    adaylar = pd.DataFrame([_aday("A", stop=99.0)])
    _, kayit = pf.simule(adaylar, _kapanis(["A"]), _rejim(), GUNLER[0], GUNLER[-1])
    assert kayit["adet"].iloc[0] == 200


def test_costs_and_equity_accounting():
    adaylar = pd.DataFrame([_aday("A", stop=90.0, cikis=110.0, cikis_gun=3)])
    sermaye, _ = pf.simule(adaylar, _kapanis(["A"]), _rejim(), GUNLER[0], GUNLER[-1])
    beklenen = 100_000 - 100 * 100 * 1.001 + 100 * 110 * 0.999
    assert sermaye.iloc[-1] == pytest.approx(beklenen)
    # Giriş günü kapanışta piyasa değeri: nakit + 100 × 100
    assert sermaye.loc[GUNLER[1]] == pytest.approx(100_000 - 100 * 100 * 1.001 + 100 * 100)


def test_max_six_positions_by_priority():
    adaylar = pd.DataFrame([_aday(f"H{i}", stop=90.0, oncelik=float(i)) for i in range(8)])
    _, kayit = pf.simule(adaylar, _kapanis([f"H{i}" for i in range(8)]), _rejim(), GUNLER[0], GUNLER[-1])
    assert len(kayit) == 6
    assert set(kayit["kod"]) == {f"H{i}" for i in range(2, 8)}  # en düşük öncelikli ikisi dışarıda


def test_trend_before_firsat_when_slots_are_short():
    adaylar = pd.DataFrame([_aday(f"T{i}", stop=90.0, oncelik=60.0) for i in range(5)]
                           + [_aday("F0", sistem="firsat", stop=90.0, oncelik=99.0),
                              _aday("T9", stop=90.0, oncelik=61.0)])
    _, kayit = pf.simule(adaylar, _kapanis([f"T{i}" for i in range(5)] + ["F0", "T9"]), _rejim(),
                         GUNLER[0], GUNLER[-1])
    assert "F0" not in set(kayit["kod"]) and len(kayit) == 6


def test_market_filter_blocks_trend_and_halves_firsat_risk():
    adaylar = pd.DataFrame([_aday("T", stop=90.0), _aday("F", sistem="firsat", stop=90.0)])
    _, kayit = pf.simule(adaylar, _kapanis(["T", "F"]), _rejim(zayif=True), GUNLER[0], GUNLER[-1])
    assert list(kayit["kod"]) == ["F"]
    assert kayit["adet"].iloc[0] == 50 and kayit["risk_orani"].iloc[0] == 0.005


def test_high_volatility_halves_risk():
    adaylar = pd.DataFrame([_aday("T", stop=90.0)])
    _, kayit = pf.simule(adaylar, _kapanis(["T"]), _rejim(oynak=True), GUNLER[0], GUNLER[-1])
    assert kayit["adet"].iloc[0] == 50


def test_no_second_position_in_same_stock_and_open_trades_marked_to_market():
    adaylar = pd.DataFrame([_aday("A", stop=90.0, cikis_gun=None),
                            _aday("A", stop=90.0, giris_gun=2, cikis_gun=None)])
    kapanis = _kapanis(["A"])
    kapanis.iloc[-1] = 120.0
    sermaye, kayit = pf.simule(adaylar, kapanis, _rejim(), GUNLER[0], GUNLER[-1])
    assert len(kayit) == 1
    assert sermaye.iloc[-1] == pytest.approx(100_000 - 100 * 100 * 1.001 + 100 * 120)


def test_signals_outside_period_are_ignored():
    adaylar = pd.DataFrame([_aday("A", stop=90.0)])
    _, kayit = pf.simule(adaylar, _kapanis(["A"]), _rejim(), GUNLER[2], GUNLER[-1])
    assert kayit.empty


def test_metrics_on_known_series():
    s = pd.Series([100.0, 110.0, 99.0, 104.5, 121.0], index=pd.bdate_range("2025-01-01", periods=5))
    m = pf.metrikler(s)
    assert m["toplam_getiri"] == pytest.approx(0.21)
    assert m["max_dusus"] == pytest.approx(99 / 110 - 1)
    assert m["max_dusus_suresi"] == 2
    assert m["getiri_dusus_orani"] == pytest.approx(m["yillik_getiri"] / abs(99 / 110 - 1))


def test_equal_weight_buy_and_hold():
    kapanis = pd.DataFrame({"A": [10.0, 20.0], "B": [10.0, 10.0], "C": [np.nan, 5.0]},
                           index=pd.bdate_range("2025-01-01", periods=2))
    s = pf.al_tut_esit(kapanis, kapanis.index[0], kapanis.index[-1], sermaye=100.0)
    assert s.iloc[-1] == pytest.approx(150.0)  # C dönem başında yok, alınmaz


def test_regime_flags():
    idx = pd.bdate_range("2023-01-02", periods=400)
    c = pd.Series(np.r_[np.full(300, 100.0) * 1.001 ** np.arange(300), np.full(100, 80.0)], index=idx)
    rj = pf.rejim(pd.DataFrame({"Close": c}))
    assert not rj["piyasa_zayif"].iloc[299]
    assert rj["piyasa_zayif"].iloc[-1]  # 80 < EMA 50 bir süre
    assert rj["yuksek_oynaklik"].iloc[305]  # sert düşüş günü sonrası oynaklık yükselir
