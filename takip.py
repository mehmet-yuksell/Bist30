"""Takip Listem: liste modeli, hisse satırları ve karar özeti (arayüzden bağımsız).

Liste kaydı: {"kod": "THYAO", "alis": 310.5 | None, "adet": 100 | None, "not": "..."}.
Alış fiyatı girilmiş hisse "elimde var" sayılır.

Karar özeti (bir hisse birden fazla grupta olabilir; "yakın" = son 5 bar içinde):
- Satışı değerlendir: elimde ve SAT/ÇIK sinyali geldi ya da son alım sinyalinin stop'u kırıldı.
- Kâr almayı düşün: elimde ve KAR AL geldi ya da son alım sinyalinin hedefine ulaştı.
- Alımı değerlendir: elimde değil ve notu A/B olan alım sinyali ya da bugün FIRSAT sinyali geldi.
  Orta vadede not sistemi doğrulanmadığı için orta vade sinyalleri bu gruba girmez.
- Takipte kal: hızlı EMA yavaş EMA'nın %1'inden yakın ve alım skoru son 3 gündür yükseliyor (kısa vade).
- Dikkat: hisse düşen bıçak riski listesinde.
"""

import json
import re

import numpy as np
import pandas as pd

import panel_veri as pv

KOD_DESENI = re.compile(r"^[A-Z0-9]{2,6}$")
SURUM = 1
SINYAL_PENCERESI = 10  # son sinyal ve stop/hedef için bakılan bar
YAKIN = 5              # karar özetinde "geldi" sayılan bar
EMA_YAKINLIK = 0.01

GRUPLAR = {
    "sat": "🔴 Satışı değerlendir",
    "kar": "🟡 Kâr almayı düşün",
    "al": "🟢 Alımı değerlendir",
    "izle": "👀 Takipte kal",
    "dikkat": "⚠️ Dikkat",
}


# ---------------------------------------------------------------------------
# Liste modeli
# ---------------------------------------------------------------------------

def kod_temizle(kod: str | None) -> str | None:
    """'thyao.is' -> 'THYAO'; geçersizse None."""
    if not kod:
        return None
    kod = str(kod).strip().upper().removesuffix(".IS")
    return kod if KOD_DESENI.match(kod) else None


def _sayi(deger, tam: bool = False):
    if deger is None or (isinstance(deger, float) and np.isnan(deger)) or deger == "":
        return None
    try:
        sayi = float(deger)
    except (TypeError, ValueError):
        return None
    if sayi <= 0:
        return None
    return int(sayi) if tam else sayi


def yeni_kayit(kod: str, alis=None, adet=None, not_: str = "") -> dict:
    temiz = kod_temizle(kod)
    if temiz is None:
        raise ValueError(f"Geçersiz hisse kodu: {kod!r}")
    return {"kod": temiz, "alis": _sayi(alis), "adet": _sayi(adet, tam=True), "not": str(not_ or "").strip()[:200]}


def elimde(kayit: dict) -> bool:
    return kayit.get("alis") is not None


def ekle(liste: list[dict], kayit: dict) -> list[dict]:
    """Aynı kod varsa günceller, yoksa sona ekler (yeni liste döner)."""
    yeni = [k for k in liste if k["kod"] != kayit["kod"]]
    konum = next((i for i, k in enumerate(liste) if k["kod"] == kayit["kod"]), len(yeni))
    yeni.insert(konum, kayit)
    return yeni


def json_yaz(liste: list[dict]) -> str:
    return json.dumps({"surum": SURUM, "hisseler": liste}, ensure_ascii=False)


def json_oku(metin: str | bytes) -> list[dict]:
    """İndirilen/yüklenen ya da localStorage'daki JSON'dan liste; bozuksa ValueError."""
    if isinstance(metin, bytes):
        metin = metin.decode("utf-8")
    if not metin or not metin.strip():
        return []
    try:
        veri = json.loads(metin)
    except json.JSONDecodeError as exc:
        raise ValueError("Dosya geçerli bir JSON değil.") from exc
    hisseler = veri.get("hisseler") if isinstance(veri, dict) else veri
    if not isinstance(hisseler, list):
        raise ValueError("JSON içinde hisse listesi bulunamadı.")
    liste: list[dict] = []
    for h in hisseler:
        if not isinstance(h, dict):
            continue
        try:
            liste = ekle(liste, yeni_kayit(h.get("kod"), h.get("alis"), h.get("adet"), h.get("not", "")))
        except ValueError:
            continue
    return liste


def ekstra_kodlar(liste: list[dict], bist100: set[str] | dict) -> tuple[str, ...]:
    """Toplu indirmeye eklenecek BIST 100 dışı kodlar (sıralı, önbellek anahtarı kararlı kalsın)."""
    return tuple(sorted({k["kod"] for k in liste} - set(bist100)))


# ---------------------------------------------------------------------------
# Satırlar
# ---------------------------------------------------------------------------

def vade_ozeti(sonuc: pd.DataFrame | None) -> dict | None:
    """Bir vadenin son bar özeti: skor, satış baskısı, son alım/satış sinyali, stop/hedef."""
    if sonuc is None or sonuc.empty:
        return None
    son = sonuc.iloc[-1]
    al = pv.al_sinyalleri(sonuc, SINYAL_PENCERESI)
    al = al[0] if al else None
    sat = pv.son_satis(sonuc, SINYAL_PENCERESI)
    skorlar = sonuc["Alim_skor"].iloc[-3:].to_numpy()
    yavas = float(son["EMA_yavas"])
    return {
        "skor": float(son["Alim_skor"]),
        "satis_baskisi": float(son["Satis_skor"]),
        "al": al,                      # {once, skor, stop, hedef, ...} ya da None
        "sat": sat,                    # {ad, tur, once, ...} ya da None
        # Stop/hedef: son alım sinyalininki; yoksa bugünkü bara göre (kapanış ∓ ATR katları)
        "stop": al["stop"] if al else float(son["Stop"]),
        "hedef": al["hedef"] if al else float(son["Hedef"]),
        "seviye_sinyalden": al is not None,
        "skor_artiyor": len(skorlar) == 3 and bool(skorlar[0] < skorlar[1] < skorlar[2]),
        "ema_yakin": yavas > 0 and abs(float(son["EMA_hizli"]) - yavas) / yavas < EMA_YAKINLIK,
    }


def satir(kayit: dict, df: pd.DataFrame | None, endeks: pd.DataFrame | None) -> dict:
    """Bir takip listesi hissesinin iki vade özeti, fiyat ve (elimdeyse) kâr/zarar."""
    out = {**kayit, "veri": df is not None and len(df) >= 2}
    if not out["veri"]:
        return out
    close = df["Close"]
    fiyat = float(close.iloc[-1])
    out["fiyat"] = fiyat
    out["degisim"] = float((close.iloc[-1] / close.iloc[-2] - 1) * 100)
    out[pv.KISA] = vade_ozeti(pv.analiz(df, pv.KISA))
    out[pv.ORTA] = vade_ozeti(pv.analiz(df, pv.ORTA, endeks)) if endeks is not None else None
    fs = pv.firsat_analizi(df, endeks)
    out["firsat"] = pv.firsat_durumu(fs) if fs is not None else None
    if elimde(kayit):
        out["kz_pct"] = (fiyat / kayit["alis"] - 1) * 100
        out["kz_tl"] = (fiyat - kayit["alis"]) * kayit["adet"] if kayit.get("adet") else None
    return out


# ---------------------------------------------------------------------------
# Karar özeti
# ---------------------------------------------------------------------------

def karar_ozeti(satirlar: list[dict], not_bul) -> dict[str, list[tuple[str, str]]]:
    """{grup: [(kod, neden)]}. not_bul(skor, vade) -> 'A'|'B'|'C'|None (doğrulanmış not)."""
    gruplar = {g: [] for g in GRUPLAR}
    for s in satirlar:
        if not s.get("veri"):
            continue
        kod, fiyat, sahip = s["kod"], s["fiyat"], elimde(s)
        for vade in (pv.KISA, pv.ORTA):
            v = s.get(vade)
            if not v:
                continue
            etiket = "kısa" if vade == pv.KISA else "orta"
            sat, al = v["sat"], v["al"]
            if sahip:
                if sat and sat["tur"] in ("SAT", "CIK") and sat["once"] <= YAKIN:
                    gruplar["sat"].append((kod, f"{sat['ad']} sinyali ({etiket} vade)"))
                if al and fiyat < al["stop"]:
                    gruplar["sat"].append((kod, f"stop kırıldı ({etiket} vade)"))
                if sat and sat["tur"] == "KAR_AL" and sat["once"] <= YAKIN:
                    gruplar["kar"].append((kod, f"KAR AL sinyali ({etiket} vade)"))
                if al and fiyat >= al["hedef"]:
                    gruplar["kar"].append((kod, f"hedefe ulaştı ({etiket} vade)"))
            elif al and al["once"] <= YAKIN:
                notu = not_bul(al["skor"], vade)
                if notu in ("A", "B"):
                    gruplar["al"].append((kod, f"not {notu} alım sinyali ({etiket} vade)"))
        firsat = s.get("firsat")
        if firsat and firsat["firsat"] and not sahip:
            gruplar["al"].append((kod, "FIRSAT sinyali"))
        kisa = s.get(pv.KISA)
        if kisa and kisa["ema_yakin"] and kisa["skor_artiyor"]:
            gruplar["izle"].append((kod, "EMA'lar kesişmeye yakın, skor 3 gündür yükseliyor"))
        if firsat and firsat["bicak"]:
            gruplar["dikkat"].append((kod, "düşen bıçak riski"))
    return gruplar
