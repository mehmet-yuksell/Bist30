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


def _vade(al=None, sat=None, stop=90.0, hedef=120.0, yakin=False, artiyor=False):
    return {"skor": 65.0, "satis_baskisi": 30.0, "al": al, "sat": sat, "stop": stop, "hedef": hedef,
            "seviye_sinyalden": al is not None, "skor_artiyor": artiyor, "ema_yakin": yakin}


def _satir(kod, fiyat=100.0, alis=None, kisa=None, orta=None, firsat=None):
    return {"kod": kod, "alis": alis, "adet": None, "not": "", "veri": True, "fiyat": fiyat,
            "kisa": kisa, "orta": orta, "firsat": firsat}


def _not(skor, vade):
    """Gerçek kısa vade notları gibi: 70-79 A, 60-69 B, 80+ C; orta vadede not yok."""
    if vade != "kisa":
        return None
    return "C" if skor >= 80 else ("A" if skor >= 70 else "B")


def test_decision_summary_rules():
    satirlar = [
        # elimde, ÇIK sinyali 2 bar önce ve stop kırık
        _satir("H1", fiyat=85, alis=100, kisa=_vade(al={"once": 7, "skor": 72, "stop": 90, "hedef": 120},
                                                     sat={"tur": "CIK", "ad": "ÇIK", "once": 2})),
        # elimde, hedefe ulaştı
        _satir("H2", fiyat=125, alis=100, kisa=_vade(al={"once": 8, "skor": 65, "stop": 90, "hedef": 120})),
        # elimde değil, not A alım sinyali 1 bar önce
        _satir("N1", kisa=_vade(al={"once": 1, "skor": 75, "stop": 90, "hedef": 120})),
        # elimde değil, not C alım sinyali: alım grubuna girmez
        _satir("N2", kisa=_vade(al={"once": 1, "skor": 85, "stop": 90, "hedef": 120})),
        # orta vade sinyali: not doğrulanmadığı için girmez
        _satir("N3", orta=_vade(al={"once": 0, "skor": 75, "stop": 90, "hedef": 120})),
        # FIRSAT ve bıçak, takipte kal
        _satir("F1", firsat={"firsat": True, "bicak": False}, kisa=_vade(yakin=True, artiyor=True)),
        _satir("K1", firsat={"firsat": False, "bicak": True}),
    ]
    g = tk.karar_ozeti(satirlar, _not)
    assert g["sat"] == [("H1", "ÇIK sinyali (kısa vade)"), ("H1", "stop kırıldı (kısa vade)")]
    assert g["kar"] == [("H2", "hedefe ulaştı (kısa vade)")]
    assert [k for k, _ in g["al"]] == ["N1", "F1"]
    assert [k for k, _ in g["izle"]] == ["F1"]
    assert [k for k, _ in g["dikkat"]] == ["K1"]


def test_old_signals_do_not_trigger():
    eski = _satir("H3", alis=100, kisa=_vade(sat={"tur": "SAT", "ad": "SAT", "once": 6}))
    assert tk.karar_ozeti([eski], _not)["sat"] == []


def test_row_without_data():
    s = tk.satir(tk.yeni_kayit("YOKK"), None, None)
    assert s["veri"] is False
    assert tk.karar_ozeti([s], _not) == {g: [] for g in tk.GRUPLAR}


def test_row_profit_and_loss():
    idx = pd.bdate_range("2025-01-01", periods=200)
    df = pd.DataFrame({"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0, "Volume": 1e6}, index=idx)
    df.iloc[-1, df.columns.get_loc("Close")] = 110.0
    s = tk.satir(tk.yeni_kayit("TEST", alis=100, adet=10), df, None)
    assert s["kz_pct"] == pytest.approx(10.0) and s["kz_tl"] == pytest.approx(100.0)
    assert s["degisim"] == pytest.approx(10.0)
    assert s["kisa"] is not None and s["orta"] is None  # endeks yoksa orta vade hesaplanmaz
