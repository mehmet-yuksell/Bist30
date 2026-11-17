"""Sinyal kalitesi notu: skora dayalı tahmin yerine geçmiş performansa dayalı not (kalibrasyon).

- GELİŞTİRME'deki AL sinyalleri skor aralığına (60-69, 70-79, 80+) ve vadenin kabul edilmiş
  alım filtrelerinden geçip geçmediğine göre gruplanır.
- Gruplar GELİŞTİRME'deki beklenen getiriye göre sıralanıp A, B, C notu alır (grup sayısı
  3'ten fazlaysa eşit dilimlere bölünür).
- Notlar TEST'te doğrulanır: not ortalamaları TEST'te de A > B > C sıralamasını koruyorsa not
  sistemi geçerlidir; korumuyorsa panelde not gösterilmez (yalnızca tarihsel istatistik).
Makine öğrenmesi yoktur; yalnızca gruplama ve sıralama.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

SKOR_ARALIKLARI = [("60-69", 60, 70), ("70-79", 70, 80), ("80+", 80, 101)]
NOTLAR = ("A", "B", "C")
DOSYA = Path(__file__).resolve().parent / "data" / "sinyal_kalitesi.json"


def skor_araligi(skor: float) -> str | None:
    for ad, alt, ust in SKOR_ARALIKLARI:
        if alt <= skor < ust:
            return ad
    return None


def grup_anahtari(skor: float, filtre: bool | None) -> str | None:
    """'70-79' ya da filtreli vadede '70-79 · filtre ✓' / '70-79 · filtre ✗'."""
    aralik = skor_araligi(skor)
    if aralik is None:
        return None
    if filtre is None:
        return aralik
    return f"{aralik} · filtre {'✓' if filtre else '✗'}"


def not_ata(gelistirme_r: dict[str, float]) -> dict[str, str]:
    """Grupları GELİŞTİRME beklenen getirisine göre sıralayıp A/B/C notu verir."""
    gecerli = [g for g, r in gelistirme_r.items() if np.isfinite(r)]
    sirali = sorted(gecerli, key=lambda g: gelistirme_r[g], reverse=True)
    if not sirali:
        return {}
    dilimler = np.array_split(np.array(sirali, dtype=object), len(NOTLAR))
    return {g: NOTLAR[i] for i, dilim in enumerate(dilimler) for g in dilim}


def sira_tutuyor_mu(not_r: dict[str, float]) -> bool:
    """TEST'te not ortalamaları A > B > C mi (eksik not atlanır, en az iki not gerekir)."""
    degerler = [not_r[n] for n in NOTLAR if n in not_r and np.isfinite(not_r[n])]
    return len(degerler) >= 2 and all(a > b for a, b in zip(degerler, degerler[1:]))


def yukle(yol: Path = DOSYA) -> dict:
    if not yol.exists():
        return {}
    return json.loads(yol.read_text(encoding="utf-8"))


def bilgi(kalibrasyon: dict, vade: str, skor: float, filtre: bool | None = None) -> dict | None:
    """Panel için: grubun notu (geçerliyse) ve tarihsel istatistikleri.

    Döner: {grup, not (str | None), hedef_pct, stop_pct, medyan_gun, sinyal} ya da None.
    """
    v = kalibrasyon.get(vade)
    if not v:
        return None
    anahtar = grup_anahtari(skor, filtre if v.get("filtreli") else None)
    grup = v.get("gruplar", {}).get(anahtar) if anahtar else None
    if grup is None:
        return None
    return {**grup, "grup": anahtar, "not": grup.get("not") if v.get("gecerli") else None}


def istatistik(t: pd.DataFrame) -> dict:
    """Bir grup işlemin panelde gösterilecek tarihsel özeti (tamamlanmış işlemler)."""
    bitti = t[t["sonuc"].isin(("hedef", "stop", "zaman"))]
    if bitti.empty:
        return {"sinyal": 0}
    hedef = bitti[bitti["sonuc"] == "hedef"]
    return {
        "sinyal": int(len(bitti)),
        "hedef_pct": float((bitti["sonuc"] == "hedef").mean() * 100),
        "stop_pct": float((bitti["sonuc"] == "stop").mean() * 100),
        "medyan_gun": float(hedef["gun"].median()) if len(hedef) else None,
        "beklenen_r": float(bitti["r"].mean()),
    }
