"""Alım sinyali kalite filtreleri (F1-F8): özellik hesabı ve eşik varyantları.

Geleceğe bakmama:
- Günlük özellikler yalnızca o güne kadarki veriyle hesaplanır (EMA, rolling, pct_change).
- Endeks (XU100) hisse tarihlerine "o tarihte ya da öncesinde bilinen son değer" ile
  hizalanır (reindex + ffill); ileri tarihli değer sızmaz.
- Orta vadede (haftalık sinyal) günlük özellikler, haftanın son işlem gününün değeridir.
- F3 sinyalin kendi zaman dilimindeki (günlük/haftalık) EMA ve ATR'yi kullanır.
- F7 sinyalden sonraki barın kapanışını bekler; giriş bir bar gecikir (ayrı simüle edilir).

Her filtre en fazla 3 eşikle denenir (metodoloji kuralı 7).
"""

import numpy as np
import pandas as pd

from tarayici_motor import ema

# filtre -> (açıklama, {varyant etiketi: eşik})
FILTRELER = {
    "F1": ("Piyasa rejimi: XU100 kapanışı N günlük EMA'nın üstünde",
           {"EMA 20": 20, "EMA 50": 50, "EMA 100": 100}),
    "F2": ("Göreceli güç: hissenin 20 ve 60 günlük getirisi XU100'den en az X puan yüksek",
           {"+0 puan": 0.0, "+2 puan": 0.02, "+5 puan": 0.05}),
    "F3": ("Aşırı uzama yok: fiyat yavaş EMA'dan en fazla K ATR uzakta",
           {"2,0 ATR": 2.0, "2,5 ATR": 2.5, "3,0 ATR": 3.0}),
    "F4": ("Likidite: 20 günlük ortalama işlem hacmi (fiyat × adet) en az X TL",
           {"10 mn TL": 10e6, "20 mn TL": 20e6, "50 mn TL": 50e6}),
    "F5": ("Uzun vadeli trend: fiyat N günlük EMA'nın üstünde",
           {"EMA 100": 100, "EMA 200": 200, "EMA 300": 300}),
    "F6": ("Boşluk yok: sinyal günü açılış boşluğu en fazla %X",
           {"%3": 0.03, "%5": 0.05, "%7": 0.07}),
    "F7": ("Teyit günü: ertesi gün kapanış sinyal gününün seviyesinin altına inmezse gir (giriş 1 bar gecikir)",
           {"en düşük": "Low", "orta nokta": "Mid", "kapanış": "Close"}),
    "F8": ("Tavan yok: sinyal günü yükselişi %X'in altında",
           {"%7": 0.07, "%8,5": 0.085, "%9,5": 0.095}),
}


def gunluk_ozellikler(gunluk: pd.DataFrame, endeks: pd.DataFrame) -> pd.DataFrame:
    """Hissenin her işlem günü için filtre özellikleri (yalnızca geçmiş veriyle)."""
    c = gunluk["Close"]
    xu = endeks["Close"]
    xu_hizali = xu.reindex(gunluk.index.union(xu.index)).ffill().reindex(gunluk.index)
    out = pd.DataFrame(index=gunluk.index)
    for n in FILTRELER["F1"][1].values():
        xu_ema = ema(xu, n).reindex(gunluk.index.union(xu.index)).ffill().reindex(gunluk.index)
        out[f"xu_ust_{n}"] = xu_hizali > xu_ema
    out["rs20"] = c.pct_change(20) - xu_hizali.pct_change(20)
    out["rs60"] = c.pct_change(60) - xu_hizali.pct_change(60)
    out["tl_hacim20"] = (c * gunluk["Volume"]).rolling(20).mean()
    for n in FILTRELER["F5"][1].values():
        out[f"ust_ema_{n}"] = c > ema(c, n)
    out["bosluk"] = gunluk["Open"] / c.shift(1) - 1
    out["gun_degisim"] = c / c.shift(1) - 1
    return out


def zaman_dilimine_hizala(ozellik: pd.DataFrame, index: pd.DatetimeIndex) -> pd.DataFrame:
    """Günlük özellikleri sinyal barlarına hizalar (haftalık etiket = haftanın son günü)."""
    return ozellik.reindex(ozellik.index.union(index)).ffill().reindex(index)


def maske(filtre: str, esik, oz: pd.DataFrame, sonuc: pd.DataFrame) -> pd.Series:
    """Sinyal barları için filtre geçti mi (F7 hariç; o giriş zamanını değiştirir).

    oz: sonuc'un indeksine hizalanmış günlük özellikler; sonuc: motor çıktısı (aynı zaman dilimi).
    Eksik veri (NaN) filtreyi geçmez.
    """
    if filtre == "F1":
        return oz[f"xu_ust_{esik}"].fillna(False).astype(bool)
    if filtre == "F2":
        return ((oz["rs20"] > esik) & (oz["rs60"] > esik)).fillna(False)
    if filtre == "F3":
        uzaklik = (sonuc["Close"] - sonuc["EMA_yavas"]) / sonuc["ATR"]
        return (uzaklik <= esik).fillna(False)
    if filtre == "F4":
        return (oz["tl_hacim20"] >= esik).fillna(False)
    if filtre == "F5":
        return oz[f"ust_ema_{esik}"].fillna(False).astype(bool)
    if filtre == "F6":
        return (oz["bosluk"] <= esik).fillna(False)
    if filtre == "F8":
        return (oz["gun_degisim"] < esik).fillna(False)
    raise ValueError(f"maske F7 için kullanılmaz: {filtre}")


def teyit(sonuc: pd.DataFrame, seviye: str) -> pd.Series:
    """F7: sinyal barının ertesi barında kapanış sinyal barının seviyesinin altına inmedi mi.

    Değer sinyal barına yazılır ama ancak ertesi barın kapanışında bilinir; bu yüzden F7'de
    giriş, ertesi barın değil ondan sonraki barın açılışıdır.
    """
    if seviye == "Mid":
        esik = (sonuc["High"] + sonuc["Low"]) / 2
    else:
        esik = sonuc[seviye]
    return (sonuc["Close"].shift(-1) >= esik).fillna(False)


def yillik_tutarlilik(deltalar: dict[int, float]) -> tuple[int, float]:
    """Eşik seçimi (yalnızca GELİŞTİRME): kaç yılda iyileştirdi, en kötü yıldaki iyileşme."""
    gecerli = [d for d in deltalar.values() if np.isfinite(d)]
    if not gecerli:
        return 0, -np.inf
    return sum(d > 0 for d in gecerli), min(gecerli)
