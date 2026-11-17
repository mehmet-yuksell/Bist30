"""Orijinal 8 koşullu Bluetsman'ı (bluetsman.py) Aşama 1 değerlendirmesiyle ölçer ve yeni sistemin
kısa vade AL'si ile yan yana koyar -> docs/bluetsman_karsilastirma.md

Kullanım (önce python tools/sistem_raporu.py çalışmış olmalı; onun önbelleğini kullanır):
    python tools/bluetsman_karsilastirma.py

Hiçbir parametre ayarlanmaz: sinyal bluetsman.compute()'un buy_signal sütunudur (8 koşulun hepsi).
Değerlendirme yeni sistemin kısa vade AL'si ile aynıdır: ertesi gün açılış girişi, stop = kapanış −
1,5 ATR, hedef = kapanış + 3 ATR (2R), 20 iş günü zaman aşımı, %0,2 gidiş-dönüş maliyet, ilk 120 gün
ısınma, GELİŞTİRME 2021-2024 / TEST 2025-. ATR tarayici_motor.atr (Wilder, 14).
"""

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

import bluetsman  # noqa: E402
import evaluation as ev  # noqa: E402
import motor_veri  # noqa: E402
import tarayici_motor as motor  # noqa: E402

CACHE = ROOT / ".eval_cache"
CIKTI = ROOT / "docs" / "bluetsman_karsilastirma.md"
STOP_ATR, RISK_ODUL, TIMEOUT = motor.KISA_VADE.stop_atr, motor.KISA_VADE.risk_odul, 20


def bluetsman_islemleri(hisseler: dict, endeks: pd.DataFrame, ham: bool = False) -> pd.DataFrame:
    """ham=True: düzeltmesiz Yahoo fiyatı (orijinal panelin kullandığı); aksi halde motor_girdisi."""
    kurallar = ev.Kurallar(timeout=TIMEOUT, side=1)
    parcalar = []
    for kod, df in hisseler.items():
        girdi = (df[["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"]).astype(float)
                 if ham else motor_veri.motor_girdisi(df))
        if len(girdi) < motor_veri.MIN_BARS:
            continue
        sinyal = bluetsman.compute(girdi)["buy_signal"]
        mesafe = motor.atr(girdi) * STOP_ATR
        t = ev.islemler(girdi, sinyal, girdi["Close"] - mesafe, girdi["Close"] + mesafe * RISK_ODUL,
                        kurallar, kod, motor_veri.MIN_BARS)
        if not t.empty:
            parcalar.append(t)
    t = pd.concat(parcalar, ignore_index=True)
    t = t[t["tarih"] >= ev.GELISTIRME[0]].reset_index(drop=True)
    t["endeks"] = ev.endeks_getirisi(t, endeks)
    return t


def _f(x, nd=1):
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{nd}f}".replace(".", ",")


def tablo(satirlar: list[tuple[str, pd.DataFrame]], donem: str) -> list[str]:
    out = ["| Sistem | Sinyal sayısı | Hedef % | Stop % | Beklenen getiri (R) | Standart hata | Hedefe medyan gün "
           "| XU100 aynı tarihlerde % | XU100'e göre fark % |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for ad, t in satirlar:
        s = ev.doneme_gore(t)[donem]
        if not s.get("sinyal"):
            out.append(f"| {ad} | 0 | — | — | — | — | — | — | — |")
            continue
        out.append(f"| {ad} | {s['sinyal']} | {_f(s['hedef_pct'])} | {_f(s['stop_pct'])} | "
                   f"**{_f(s['beklenen_r'], 3)}** | ±{_f(s['r_std_hata'], 3)} | {_f(s['hedef_medyan_gun'], 0)} | "
                   f"{_f(s.get('endeks_ort_pct'), 2)} | {_f(s.get('endeks_fazla_pct'), 2)} |")
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    hisseler = pd.read_pickle(CACHE / "hisseler_10y.pkl")
    endeks = pd.read_pickle(CACHE / "xu100.pkl")
    endeks.index = pd.DatetimeIndex(endeks.index).tz_localize(None) if endeks.index.tz else endeks.index
    yeni = pd.read_pickle(CACHE / "islemler.pkl")["kisa"]

    satirlar = [
        ("Orijinal Bluetsman (8 koşul, buy_signal)", bluetsman_islemleri(hisseler, endeks)),
        ("Yeni sistem kısa vade AL (tarayici_motor)", yeni["AL"]),
        ("Rastgele gün (aynı stop/hedef/süre)", yeni["RASTGELE_AL"]),
        ("Orijinal Bluetsman, ham fiyatla (eski panelin verisi)", bluetsman_islemleri(hisseler, endeks, ham=True)),
    ]
    out = [
        "# Orijinal Bluetsman ile yeni sistemin karşılaştırması",
        "",
        "> Eğitim amaçlıdır, yatırım tavsiyesi değildir. `python tools/bluetsman_karsilastirma.py` ile üretilir.",
        "",
        "Orijinal Bluetsman (`bluetsman.py`, Pine Script'in birebir aktarımı) hiçbir parametresi değiştirilmeden "
        "ölçüldü: sinyal, 8 koşulun hepsinin aynı gün tuttuğu `buy_signal`. Değerlendirme yeni sistemin kısa vade "
        "AL'si ile aynı: ertesi gün açılıştan giriş, stop = kapanış − 1,5 ATR, hedef = kapanış + 3 ATR (2R), "
        "20 iş günü zaman aşımı, %0,2 gidiş-dönüş maliyet, temettü/bölünme düzeltmeli fiyat, bugünkü BIST 100 "
        "listesi (hayatta kalma yanlılığı), hissenin ilk 120 günü sinyal sayılmaz. Ayrıntılı yöntem: "
        "`docs/sistem_raporu.md`.",
        "",
        "Son satır bilgi içindir: orijinal panel düzeltilmemiş Yahoo fiyatıyla çalışıyordu; bedelsiz/bölünme "
        "günleri orada sahte düşüş olarak görünür.",
        "",
    ]
    for donem in ("TEST", "GELİŞTİRME"):
        out += [f"## {donem}{' (asıl sonuç)' if donem == 'TEST' else ''}", ""] + tablo(satirlar, donem) + [""]
    CIKTI.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
