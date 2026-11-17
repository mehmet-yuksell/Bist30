"""FIRSAT sistemi: sağlam hissede ani sert düşüş sonrası toparlanma (mean reversion).

Trend takip sisteminden (tarayici_motor AL) bağımsızdır. Yalnızca kısa vade (günlük).
Tüm koşullar yalnızca o güne kadarki veriyle hesaplanır; sinyal gün sonunda oluşur,
giriş ertesi günün açılışıdır.

KURULUM (günlük, t günü; hepsi gerekli)
- Ani düşüş: 1-5 gün önceki kapanıştan t kapanışına düşüş ≥ 2,5 ATR ya da ≥ %8,
  ve RSI(2) < 10.
- Sağlam: düşüşün başladığı günün kapanışı 200 günlük EMA'nın üstünde ve haftalık trend
  yukarı (tamamlanmış son haftalık kapanış 30 haftalık EMA'nın üstünde).
TETİK
- Son kurulum gününden sonraki ilk 5 gün içinde kapanış bir önceki günün en yükseğinin
  üstünde (dönüş günü). Her düşüş bölümüne (episode) en fazla bir tetik.
DÜŞEN BIÇAK (bölüm başından tetik gününe kadar herhangi bir gün biri bile görüldüyse eleme)
- K1: kapanış 200 günlük EMA'nın altında ve son 3 günün en az 2'sinde altında kapandı.
- K2: son 5 günden birinde düşüş günü, hacim önceki 20 günün ortalamasının 3 katından fazla
  ve kapanış günün aralığının alt %20'sinde (kurumsal satış işareti).
- K3: 52 haftanın (252 işlem günü) en düşük seviyesi kırıldı.
- K4: haftalık Supertrend (10, 3; tamamlanmış haftalar) aşağı yönde.
UYARILAR (tetik günü; sinyali engellemez)
- Hisseye özel düşüş: hisse son 5 günde %8+ düştü, XU100 %2'den az düştü.
- Piyasa geneli satış: XU100 son 5 günde %5+ düştü.
RİSK
- Stop: dönüş günü dahil son 10 günün en düşüğünün 0,5 ATR altı.
- Hedef: 20 günlük EMA'ya dönüş ya da 2R, hangisi önce gelirse. EMA bar bar değişir; o barın
  hedefi bir önceki günün EMA'sıdır (gün içinde bilinen değer). Giriş EMA'nın üstündeyse
  işlem açılmaz (zaten "dönmüş").
- Zaman stopu: 10 işlem günü.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tarayici_motor import atr, ema, haftalik_trend_gunluge, haftaliga_cevir, rsi, supertrend


@dataclass(frozen=True)
class FirsatAyari:
    dusus_gun: int = 5
    dusus_atr: float = 2.5
    dusus_yuzde: float = 0.08
    rsi2_esik: float = 10.0
    tetik_gun: int = 5
    ema_uzun: int = 200
    haftalik_ema: int = 30
    # Düşen bıçak
    k1_gun: int = 2            # K1: son k1_pencere günün en az k1_gun'ünde EMA altında kapanış
    k1_pencere: int = 3
    hacim_kat: float = 3.0     # K2
    alt_bant: float = 0.2
    yil_gun: int = 252         # K3: bu kadar günün en düşüğü
    k4_carpan: float = 3.0     # K4: haftalık Supertrend çarpanı
    elemede: tuple = ("K1", "K2", "K3", "K4")  # eleme için kullanılan kriterler
    # Uyarılar
    hisse_dusus: float = 0.08
    endeks_sakin: float = 0.02
    endeks_dusus: float = 0.05
    # Risk
    dip_pencere: int = 10
    stop_atr: float = 0.5
    risk_odul: float = 2.0
    hedef_ema: int = 20
    zaman: int = 10


VARSAYILAN = FirsatAyari()
BICAK_KRITERLERI = {
    "K1": "200 günlük EMA'nın altına yerleşti",
    "K2": "yüksek hacimli dipte kapanış (kurumsal satış)",
    "K3": "52 haftanın en düşüğü kırıldı",
    "K4": "haftalık Supertrend aşağı",
}


def _haftalik_supertrend_asagi(df: pd.DataFrame, carpan: float = 3.0) -> pd.Series:
    """Her gün için: tamamlanmış (ya da o gün biten) son haftanın Supertrend yönü aşağı mı."""
    haftalik = haftaliga_cevir(df)
    _, yon = supertrend(haftalik, carpan, 10)
    asagi = (yon == -1).astype(float)
    return asagi.reindex(df.index.union(asagi.index)).ffill().reindex(df.index).fillna(0).astype(bool)


def gunluk_kosullar(df: pd.DataFrame, endeks: pd.DataFrame | None = None,
                    ayar: FirsatAyari = VARSAYILAN) -> pd.DataFrame:
    """Her gün için kurulum, düşen bıçak kriterleri ve uyarı koşulları."""
    c, h, lo, v = df["Close"], df["High"], df["Low"], df["Volume"]
    a = atr(df)
    ema_uzun = ema(c, ayar.ema_uzun)
    rsi2 = rsi(c, 2)
    out = pd.DataFrame(index=df.index)

    # Ani düşüş + düşüş öncesi sağlamlık (1-5 günlük pencerelerden biri yeterli)
    kurulum_dusus = pd.Series(False, index=df.index)
    for k in range(1, ayar.dusus_gun + 1):
        onceki = c.shift(k)
        dusus = onceki - c
        sert = (dusus >= ayar.dusus_atr * a.shift(k)) | (dusus / onceki >= ayar.dusus_yuzde)
        kurulum_dusus |= (sert & (onceki > ema_uzun.shift(k))).fillna(False)
    out["haftalik_yukari"] = haftalik_trend_gunluge(df, ayar.haftalik_ema)
    out["kurulum"] = kurulum_dusus & (rsi2 < ayar.rsi2_esik) & out["haftalik_yukari"]

    # Düşen bıçak kriterleri (o güne kadarki veriyle)
    alti = c < ema_uzun
    out["K1"] = alti & (alti.astype(int).rolling(ayar.k1_pencere).sum() >= ayar.k1_gun)
    hacim_ort = v.rolling(20).mean().shift(1)
    aralik = (h - lo).replace(0, np.nan)
    satis_gunu = (v > ayar.hacim_kat * hacim_ort) & (c < c.shift(1)) & ((c - lo) / aralik <= ayar.alt_bant)
    out["K2"] = satis_gunu.fillna(False).astype(int).rolling(ayar.dusus_gun, min_periods=1).max().astype(bool)
    onceki_dip = lo.shift(1).rolling(ayar.yil_gun, min_periods=ayar.yil_gun).min()
    out["K3"] = (lo < onceki_dip).fillna(False)
    out["K4"] = _haftalik_supertrend_asagi(df, ayar.k4_carpan)

    # Uyarılar
    hisse5 = c / c.shift(5) - 1
    out["hisse5"] = hisse5
    if endeks is not None:
        xu = endeks["Close"]
        xu5 = (xu / xu.shift(5) - 1).reindex(df.index.union(xu.index)).ffill().reindex(df.index)
    else:
        xu5 = pd.Series(np.nan, index=df.index)
    out["xu5"] = xu5
    out["uyari_hisseye_ozel"] = (hisse5 <= -ayar.hisse_dusus) & (xu5 > -ayar.endeks_sakin)
    out["uyari_piyasa"] = xu5 <= -ayar.endeks_dusus

    out["ATR"] = a
    out["RSI2"] = rsi2
    out["EMA_hedef"] = ema(c, ayar.hedef_ema)
    return out


def firsat_hesapla(df: pd.DataFrame, endeks: pd.DataFrame | None = None,
                   ayar: FirsatAyari = VARSAYILAN) -> pd.DataFrame:
    """Günlük tabloya FIRSAT sütunları ekler.

    Sütunlar: kurulum, bolum_basi (yeni düşüş bölümünün ilk kurulum günü), tetik (dönüş günü,
    elemeden önce), BICAK (tetik var ama düşen bıçak elemesi), FIRSAT (tetik ve eleme yok),
    BICAK_RISKI (kurulum penceresinde ve en az bir bıçak kriteri görülmüş; panel listesi),
    kurulum_penceresi (düşüş bölümü açık, dönüş bekleniyor ya da bugün tetiklendi),
    K1-K4 (bölüm başından o güne kadar görülen), uyarılar, Stop, ATR, EMA_hedef, RSI2.
    """
    k = gunluk_kosullar(df, endeks, ayar)
    c, h = df["Close"].to_numpy(), df["High"].to_numpy()
    kurulum = k["kurulum"].to_numpy()
    kriter = {key: k[key].to_numpy() for key in BICAK_KRITERLERI}
    n = len(df)

    bolum_basi = np.zeros(n, dtype=bool)
    tetik = np.zeros(n, dtype=bool)
    bicak_gorulen = {key: np.zeros(n, dtype=bool) for key in BICAK_KRITERLERI}
    pencerede = np.zeros(n, dtype=bool)

    son_kurulum = -10**9
    bas = None
    tetiklendi = False
    gorulen = {key: False for key in BICAK_KRITERLERI}
    for i in range(n):
        if kurulum[i]:
            if i - son_kurulum > ayar.tetik_gun or tetiklendi:
                # Yeni bölüm: önceki bölümün penceresi kapandı ya da önceki bölüm tetiklendi
                bas, tetiklendi = i, False
                gorulen = {key: False for key in BICAK_KRITERLERI}
                bolum_basi[i] = True
            son_kurulum = i
        aktif = bas is not None and not tetiklendi and i - son_kurulum <= ayar.tetik_gun
        if aktif:
            pencerede[i] = True
            for key in BICAK_KRITERLERI:
                gorulen[key] = gorulen[key] or bool(kriter[key][i])
                bicak_gorulen[key][i] = gorulen[key]
            if i > son_kurulum and c[i] > h[i - 1]:
                tetik[i] = True
                tetiklendi = True

    out = df.copy()
    out["kurulum"] = kurulum
    out["bolum_basi"] = bolum_basi
    out["tetik"] = tetik
    for key in BICAK_KRITERLERI:
        out[key] = bicak_gorulen[key]
    elemede = [key for key in BICAK_KRITERLERI if key in ayar.elemede]
    herhangi = (np.logical_or.reduce([bicak_gorulen[key] for key in elemede]) if elemede
                else np.zeros(n, dtype=bool))
    out["BICAK"] = tetik & herhangi
    out["FIRSAT"] = tetik & ~herhangi
    out["BICAK_RISKI"] = pencerede & herhangi
    out["kurulum_penceresi"] = pencerede
    out["uyari_hisseye_ozel"] = k["uyari_hisseye_ozel"].fillna(False).to_numpy(dtype=bool)
    out["uyari_piyasa"] = k["uyari_piyasa"].fillna(False).to_numpy(dtype=bool)
    out["ATR"] = k["ATR"]
    out["EMA_hedef"] = k["EMA_hedef"]
    out["RSI2"] = k["RSI2"]
    dip = df["Low"].rolling(ayar.dip_pencere, min_periods=1).min()  # dönüş günü dahil son 10 gün
    out["Stop"] = dip - ayar.stop_atr * k["ATR"]
    return out


def hedef_dizisi(sonuc: pd.DataFrame, giris: float, stop: float, ayar: FirsatAyari = VARSAYILAN) -> np.ndarray:
    """Bar bar hedef: bir önceki günün 20 günlük EMA'sı ile giriş + 2R'nin küçüğü."""
    ema_dun = sonuc["EMA_hedef"].shift(1).to_numpy()
    return np.minimum(ema_dun, giris + ayar.risk_odul * (giris - stop))


def islemler(sonuc: pd.DataFrame, sinyal: pd.Series, kod: str = "", ilk_bar: int = 0,
             ayar: FirsatAyari = VARSAYILAN, cost: float | None = None) -> pd.DataFrame:
    """`sinyal` True olan günler için FIRSAT kurallarıyla işlem (ertesi gün açılış girişi)."""
    import evaluation as ev

    k = ev.Kurallar(timeout=ayar.zaman, side=1, cost=ev.COST if cost is None else cost)
    o, h, lo, c = (sonuc[col].to_numpy(dtype=float) for col in ("Open", "High", "Low", "Close"))
    stop = sonuc["Stop"].to_numpy(dtype=float)
    ema_dun = sonuc["EMA_hedef"].shift(1).to_numpy()  # hedef_dizisi ile aynı, bir kez hesaplanır
    satirlar = []
    for i in np.flatnonzero(sinyal.to_numpy(dtype=bool)):
        if i < ilk_bar or i + 1 >= len(sonuc) or not np.isfinite(stop[i]):
            if i >= ilk_bar and i + 1 >= len(sonuc):
                satirlar.append({"sonuc": "acik", "kod": kod, "tarih": sonuc.index[i]})
            continue
        hedef = np.minimum(ema_dun, o[i + 1] + ayar.risk_odul * (o[i + 1] - stop[i]))
        r = ev.simule_et(o, h, lo, c, int(i), stop[i], hedef, k)
        r["kod"], r["tarih"] = kod, sonuc.index[i]
        if "giris_i" in r:
            r["giris_tarihi"] = sonuc.index[r["giris_i"]]
        if "cikis_i" in r:
            r["cikis_tarihi"] = sonuc.index[r["cikis_i"]]
        satirlar.append(r)
    return pd.DataFrame(satirlar)
