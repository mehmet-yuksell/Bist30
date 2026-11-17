"""Portföy bazlı test: sinyal işlemlerini sermaye, pozisyon sınırı ve risk kurallarıyla birleştirir.

İşlemlerin giriş/çıkış fiyatları ve tarihleri evaluation.py'de (ertesi gün açılış girişi,
stop/hedef/zaman aşımı) zaten simüle edilmiştir; çıkış, pozisyon büyüklüğünden bağımsızdır.
Bu modül yalnızca hangi işlemin alınacağına ve kaç adet alınacağına karar verir.

Kurallar (docs/sistem_raporu.md, Aşama 3d):
- Başlangıç sermayesi 100.000 TL. Her işlemde sermayenin %1'i riske girer:
  adet = (sermaye × risk) / (giriş − stop); tek pozisyon sermayenin %20'sini geçmez; kaldıraç yok.
- Sermaye, girişten önceki günün kapanışındaki piyasa değeridir (giriş açılışta yapılır).
- Aynı anda en fazla 6 açık pozisyon; aynı hissede ikinci pozisyon açılmaz. Yer yetmezse trend
  sinyalleri skora göre önce, FIRSAT sinyalleri sonra (RSI(2) düşük olan önce) alınır.
- Oynaklık: XU100'ün 20 günlük gerçekleşen oynaklığı son 1 yılın %80'lik diliminin üstündeyse
  risk %0,5.
- Piyasa filtresi: XU100 kapanışı 50 günlük EMA'nın altındaysa trend sistemine yeni alım yok;
  FIRSAT'a izin var ama risk %0,5. Rejim sinyal günü kapanışında bilinen değerdir.
- Maliyet: her yönde %0,1 (gidiş-dönüş %0,2).
- Gün sırası: önce açılışta girişler (bir önceki günün kapanışındaki boş yerlere göre), sonra
  gün içi çıkışlar, sonra kapanışta piyasa değerlemesi.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tarayici_motor import ema


@dataclass(frozen=True)
class PortfoyAyari:
    sermaye: float = 100_000.0
    risk: float = 0.01
    dusuk_risk: float = 0.005
    max_pozisyon_orani: float = 0.20
    max_pozisyon: int = 6
    maliyet_yon: float = 0.001
    oynaklik_pencere: int = 20
    oynaklik_yil: int = 252
    oynaklik_yuzdelik: float = 0.80
    piyasa_ema: int = 50


VARSAYILAN = PortfoyAyari()
SISTEM_SIRASI = {"trend": 0, "firsat": 1}


def rejim(endeks: pd.DataFrame, ayar: PortfoyAyari = VARSAYILAN) -> pd.DataFrame:
    """Her gün için (o günün kapanışıyla bilinen) yüksek oynaklık ve zayıf piyasa durumu."""
    c = endeks["Close"]
    getiri = c.pct_change()
    oynaklik = getiri.rolling(ayar.oynaklik_pencere).std() * np.sqrt(252)
    esik = oynaklik.rolling(ayar.oynaklik_yil, min_periods=ayar.oynaklik_yil // 2).quantile(ayar.oynaklik_yuzdelik)
    return pd.DataFrame({
        "oynaklik": oynaklik,
        "yuksek_oynaklik": (oynaklik > esik).fillna(False),
        "piyasa_zayif": (c < ema(c, ayar.piyasa_ema)).fillna(False),
    }, index=endeks.index)


def _rejim_degeri(rejim_df: pd.DataFrame, tarih: pd.Timestamp, sutun: str) -> bool:
    """Sinyal günü ya da öncesinde bilinen son rejim değeri."""
    gecmis = rejim_df.loc[:tarih, sutun]
    return bool(gecmis.iloc[-1]) if len(gecmis) else False


def simule(adaylar: pd.DataFrame, kapanislar: pd.DataFrame, rejim_df: pd.DataFrame,
           bas: pd.Timestamp, bit: pd.Timestamp, ayar: PortfoyAyari = VARSAYILAN) -> tuple[pd.Series, pd.DataFrame]:
    """Dönem içi sinyallerden portföy oluşturur.

    adaylar: kod, sistem ('trend'|'firsat'), tarih (sinyal), giris_tarihi, giris, stop,
             cikis_tarihi (NaT: henüz çıkmadı), cikis, oncelik (yüksek önce).
    kapanislar: tarih × kod kapanış tablosu (düzeltilmiş, işlem günü takvimi).
    Döner: günlük sermaye serisi ve alınan işlemlerin kaydı.
    """
    takvim = kapanislar.index[(kapanislar.index >= bas) & (kapanislar.index <= bit)]
    kapanislar = kapanislar.ffill()
    secili = adaylar[(adaylar["tarih"] >= bas) & (adaylar["tarih"] <= bit) & adaylar["giris_tarihi"].notna()].copy()
    secili["_sira"] = secili["sistem"].map(SISTEM_SIRASI)
    secili = secili.sort_values(["giris_tarihi", "_sira", "oncelik"], ascending=[True, True, False])
    girisler = {d: g for d, g in secili.groupby("giris_tarihi")}

    nakit = ayar.sermaye
    acik: dict[str, dict] = {}
    kayit = []
    sermaye_dun = ayar.sermaye
    seri = {}
    for gun in takvim:
        # 1) Açılışta girişler
        for _, a in girisler.get(gun, pd.DataFrame()).iterrows():
            if a["kod"] in acik or len(acik) >= ayar.max_pozisyon:
                continue
            zayif = _rejim_degeri(rejim_df, a["tarih"], "piyasa_zayif")
            if a["sistem"] == "trend" and zayif:
                continue
            dusuk = _rejim_degeri(rejim_df, a["tarih"], "yuksek_oynaklik") or (a["sistem"] == "firsat" and zayif)
            risk_orani = ayar.dusuk_risk if dusuk else ayar.risk
            birim_risk = a["giris"] - a["stop"]
            if not birim_risk > 0:
                continue
            adet = np.floor(sermaye_dun * risk_orani / birim_risk)
            adet = min(adet, np.floor(sermaye_dun * ayar.max_pozisyon_orani / a["giris"]),
                       np.floor(nakit / (a["giris"] * (1 + ayar.maliyet_yon))))
            if adet < 1:
                continue
            nakit -= adet * a["giris"] * (1 + ayar.maliyet_yon)
            acik[a["kod"]] = {"adet": adet, "cikis_tarihi": a["cikis_tarihi"], "cikis": a["cikis"]}
            kayit.append({**a.drop(labels="_sira").to_dict(), "adet": adet, "risk_orani": risk_orani,
                          "pozisyon_tl": adet * a["giris"]})
        # 2) Gün içi çıkışlar
        for kod in [k for k, p in acik.items() if p["cikis_tarihi"] == gun]:
            p = acik.pop(kod)
            nakit += p["adet"] * p["cikis"] * (1 - ayar.maliyet_yon)
        # 3) Kapanışta değerleme
        deger = sum(p["adet"] * kapanislar.at[gun, kod] for kod, p in acik.items())
        sermaye_dun = nakit + deger
        seri[gun] = sermaye_dun
    return pd.Series(seri, dtype=float), pd.DataFrame(kayit)


def al_tut_esit(kapanislar: pd.DataFrame, bas: pd.Timestamp, bit: pd.Timestamp,
                sermaye: float = VARSAYILAN.sermaye) -> pd.Series:
    """Dönem başında verisi olan hisselere eşit ağırlıkla al-tut (yeniden dengeleme yok)."""
    donem = kapanislar.loc[(kapanislar.index >= bas) & (kapanislar.index <= bit)]
    ilk = donem.iloc[0]
    hisseler = ilk.index[ilk.notna()]
    oran = donem[hisseler].ffill() / ilk[hisseler]
    return oran.mean(axis=1) * sermaye


def al_tut_endeks(endeks: pd.DataFrame, bas: pd.Timestamp, bit: pd.Timestamp,
                  sermaye: float = VARSAYILAN.sermaye) -> pd.Series:
    c = endeks.loc[(endeks.index >= bas) & (endeks.index <= bit), "Close"]
    return c / c.iloc[0] * sermaye


def metrikler(sermaye: pd.Series) -> dict:
    """Yıllık getiri, oynaklık, Sharpe/Sortino (risksiz getiri 0), maksimum düşüş ve süresi."""
    s = sermaye.dropna()
    if len(s) < 2:
        return {}
    gunluk = s.pct_change().dropna()
    yil = len(gunluk) / 252
    toplam = s.iloc[-1] / s.iloc[0] - 1
    yillik = (1 + toplam) ** (1 / yil) - 1 if yil > 0 and toplam > -1 else np.nan
    std = gunluk.std()
    asagi = np.sqrt((np.minimum(gunluk, 0) ** 2).mean())
    tepe = s.cummax()
    dusus = s / tepe - 1
    # En uzun düşüş süresi: tepeden yeniden tepeye (ya da döneme sonuna) işlem günü
    en_uzun = mevcut = 0
    for d in dusus:
        mevcut = mevcut + 1 if d < 0 else 0
        en_uzun = max(en_uzun, mevcut)
    max_dusus = dusus.min()
    return {
        "toplam_getiri": toplam,
        "yillik_getiri": yillik,
        "yillik_oynaklik": std * np.sqrt(252),
        "sharpe": gunluk.mean() / std * np.sqrt(252) if std > 0 else np.nan,
        "sortino": gunluk.mean() / asagi * np.sqrt(252) if asagi > 0 else np.nan,
        "max_dusus": max_dusus,
        "max_dusus_suresi": en_uzun,
        "getiri_dusus_orani": yillik / abs(max_dusus) if max_dusus < 0 else np.nan,
    }


def dusus_serisi(sermaye: pd.Series) -> pd.Series:
    return sermaye / sermaye.cummax() - 1
