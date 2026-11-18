"""takip.py için testler: liste modeli, JSON, karar özeti."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import takip as tk


def test_code_cleaning_and_record():
    assert tk.kod_temizle(" thyao.is ") == "THYAO"
    assert tk.kod_temizle("A") is None and tk.kod_temizle("THY AO") is None and tk.kod_temizle(None) is None
    k = tk.yeni_kayit("garan", alis="150,5".replace(",", "."), adet=10.7, not_="  uzun vade ")
    assert k == {"kod": "GARAN", "alis": 150.5, "adet": 10, "not": "uzun vade"}
    assert tk.elimde(k)
    assert not tk.elimde(tk.yeni_kayit("ASELS", alis=0))  # sıfır/negatif fiyat girilmemiş sayılır
    with pytest.raises(ValueError):
        tk.yeni_kayit("??")


def test_add_updates_in_place():
    liste = [tk.yeni_kayit("A1"), tk.yeni_kayit("B2"), tk.yeni_kayit("C3")]
    liste = tk.ekle(liste, tk.yeni_kayit("B2", alis=10))
    assert [k["kod"] for k in liste] == ["A1", "B2", "C3"] and liste[1]["alis"] == 10
    liste = tk.ekle(liste, tk.yeni_kayit("D4"))
    assert [k["kod"] for k in liste][-1] == "D4"


def test_json_roundtrip_and_validation():
    liste = [tk.yeni_kayit("THYAO", 310, 5, "x"), tk.yeni_kayit("SASA")]
    assert tk.json_oku(tk.json_yaz(liste)) == liste
    # eski/elle yazılmış dosya: düz liste, geçersiz ve tekrarlı kayıtlar ayıklanır
    assert [k["kod"] for k in tk.json_oku('[{"kod": "thyao"}, {"kod": "??"}, {"kod": "THYAO", "alis": 5}, 3]')] == ["THYAO"]
    assert tk.json_oku("") == []
    with pytest.raises(ValueError):
        tk.json_oku("{bozuk")
    with pytest.raises(ValueError):
        tk.json_oku('{"baska": 1}')


def test_extra_codes_outside_bist100():
    liste = [tk.yeni_kayit("THYAO"), tk.yeni_kayit("ZZZZ"), tk.yeni_kayit("AAAA")]
    assert tk.ekstra_kodlar(liste, {"THYAO", "GARAN"}) == ("AAAA", "ZZZZ")


def _vade(al=None, acik_al=None, sat=None, yakin=False, artiyor=False):
    return {"skor": 65.0, "al": al, "acik_al": acik_al, "sat": sat, "skor_artiyor": artiyor, "ema_yakin": yakin}


def _satir(kod, fiyat=100.0, alis=None, kisa=None, orta=None):
    return {"kod": kod, "alis": alis, "adet": None, "not": "", "veri": True, "fiyat": fiyat,
            "kisa": kisa, "orta": orta}


def test_decision_summary_rules():
    alim = {"once": 1, "skor": 75.0}
    satirlar = [
        # elimde, SAT sinyali 2 bar önce (günlük)
        _satir("H1", alis=100, kisa=_vade(sat={"tur": "sat", "ad": "SAT", "once": 2, "skor": 66.0})),
        # elimde, KAR AL haftalık vadede
        _satir("H2", alis=100, orta=_vade(sat={"tur": "kar_al", "ad": "KAR AL", "once": 0, "skor": 45.0})),
        # elimde değil, ardından satış gelmemiş alım sinyali
        _satir("N1", kisa=_vade(al=alim, acik_al=alim)),
        # elimde değil, alım sinyalinden sonra satış geldi: girmez
        _satir("N2", kisa=_vade(al=alim, sat={"tur": "kar_al", "ad": "KAR AL", "once": 0, "skor": 45.0})),
        # elimde: alım sinyali alım grubuna girmez
        _satir("H3", alis=100, kisa=_vade(al=alim, acik_al=alim)),
        # takipte kal
        _satir("I1", kisa=_vade(yakin=True, artiyor=True)),
    ]
    g = tk.karar_ozeti(satirlar)
    assert g["sat"] == [("H1", "SAT sinyali, skor 66 (günlük)")]
    assert g["kar"] == [("H2", "KAR AL sinyali, skor 45 (haftalık)")]
    assert g["al"] == [("N1", "alım sinyali, skor 75 (günlük)")]
    assert [k for k, _ in g["izle"]] == ["I1"]
    assert set(g) == {"sat", "kar", "al", "izle"}


def test_old_signals_do_not_trigger():
    eski = _satir("H3", alis=100, kisa=_vade(sat={"tur": "sat", "ad": "SAT", "once": 6, "skor": 70.0}))
    assert tk.karar_ozeti([eski])["sat"] == []


def test_row_without_data():
    s = tk.satir(tk.yeni_kayit("YOKK"), None)
    assert s["veri"] is False
    assert tk.karar_ozeti([s]) == {g: [] for g in tk.GRUPLAR}


def test_row_profit_and_loss():
    idx = pd.bdate_range("2025-01-01", periods=300)
    df = pd.DataFrame({"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0, "Volume": 1e6}, index=idx)
    df.iloc[-1, df.columns.get_loc("Close")] = 110.0
    s = tk.satir(tk.yeni_kayit("TEST", alis=100, adet=10), df)
    assert s["kz_pct"] == pytest.approx(10.0) and s["kz_tl"] == pytest.approx(100.0)
    assert s["degisim"] == pytest.approx(10.0)
    assert s["kisa"] is not None and s["orta"] is not None  # 300 gün = 60 hafta
