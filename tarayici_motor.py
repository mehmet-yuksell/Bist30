"""
BIST Sinyal Tarayıcı — hesaplama motoru
Bluetsman Alım/Sat v2 mantığının Python versiyonu.
Arayüzden bağımsızdır: veri alır, gösterge ve sinyal hesaplar, geçmiş isabet testi yapar.
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd


# ════════════════════════════ AYARLAR ════════════════════════════
@dataclass
class AlimFiltreleri:
    """AL sinyaline eklenen kalite filtreleri (docs/sistem_raporu.md, Aşama 2).

    Skoru ve AL sütununu değiştirmez; sonuç AL_filtreli sütunundadır. Yalnızca geçmiş
    testte kabul şartlarını sağlayan filtreler açıktır. None olan filtre kullanılmaz.
    """
    aktif: bool = False
    piyasa_ema: int | None = None        # F1: XU100 günlük kapanışı bu günlük EMA'nın üstünde
    uzun_trend_ema: int | None = None    # F5: hisse günlük kapanışı bu günlük EMA'nın üstünde
    tavan_esik: float | None = None      # F8: sinyal günü yükselişi bu oranın altında


@dataclass
class VadeAyari:
    ad: str
    # Alım
    hizli_ema: int
    yavas_ema: int
    kesisim_gecerlilik: int      # kesişimden sonra kaç bar boyunca sinyal verilebilir
    st_carpan_alim: float
    min_skor: int
    trend_filtre: str            # "haftalik" (günlükte) veya "ema" (haftalıkta)
    trend_ema: int
    # Satış
    kisa_ema: int
    orta_ema: int
    uzun_ema: int
    st_carpan_satis: float
    kar_al_min: int
    sat_min: int
    # Risk
    stop_atr: float
    risk_odul: float
    # Test
    test_bar: int                # sinyalden sonra kaç bara bakılacak
    test_yuzde: float            # isabet için gereken hareket (%)
    # Alım kalite filtreleri (kapalıysa AL_filtreli = AL)
    filtreler: AlimFiltreleri = field(default_factory=AlimFiltreleri)


# Kısa vadede hiçbir filtre kabul şartlarını sağlamadı (Aşama 2); filtre yok.
KISA_VADE = VadeAyari(
    ad="Kısa vade (günlük grafik)",
    hizli_ema=13, yavas_ema=34, kesisim_gecerlilik=3, st_carpan_alim=3.0, min_skor=60,
    trend_filtre="haftalik", trend_ema=20,
    kisa_ema=5, orta_ema=13, uzun_ema=34, st_carpan_satis=2.5, kar_al_min=40, sat_min=61,
    stop_atr=1.5, risk_odul=2.0,
    test_bar=10, test_yuzde=3.0,
)

ORTA_VADE = VadeAyari(
    ad="Orta vade (haftalık grafik)",
    hizli_ema=10, yavas_ema=30, kesisim_gecerlilik=2, st_carpan_alim=3.0, min_skor=60,
    trend_filtre="ema", trend_ema=40,
    kisa_ema=5, orta_ema=13, uzun_ema=30, st_carpan_satis=2.5, kar_al_min=40, sat_min=61,
    stop_atr=2.0, risk_odul=2.0,
    test_bar=8, test_yuzde=8.0,
    # Aşama 2'de iki dönemde de beklenen getiriyi artıran filtreler (etkileri küçük; rapora bakın)
    filtreler=AlimFiltreleri(aktif=True, piyasa_ema=100, uzun_trend_ema=300, tavan_esik=0.085),
)


# ════════════════════════════ GÖSTERGELER ════════════════════════════
def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def rma(s: pd.Series, n: int) -> pd.Series:
    """Wilder ortalaması (TradingView'daki ta.rma)."""
    return s.ewm(alpha=1 / n, adjust=False).mean()


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    fark = close.diff()
    yukari = rma(fark.clip(lower=0), n)
    asagi = rma(-fark.clip(upper=0), n)
    rs = yukari / asagi.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(100)


def true_range(df: pd.DataFrame) -> pd.Series:
    onceki = df["Close"].shift()
    return pd.concat(
        [df["High"] - df["Low"], (df["High"] - onceki).abs(), (df["Low"] - onceki).abs()], axis=1
    ).max(axis=1)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    return rma(true_range(df), n)


def macd_hist(close: pd.Series) -> pd.Series:
    macd = ema(close, 12) - ema(close, 26)
    return macd - ema(macd, 9)


def dmi(df: pd.DataFrame, n: int = 14, yumusatma: int = 14):
    yukari = df["High"].diff()
    asagi = -df["Low"].diff()
    arti_dm = pd.Series(np.where((yukari > asagi) & (yukari > 0), yukari, 0.0), index=df.index)
    eksi_dm = pd.Series(np.where((asagi > yukari) & (asagi > 0), asagi, 0.0), index=df.index)
    tr = rma(true_range(df), n).replace(0, np.nan)
    arti_di = 100 * rma(arti_dm, n) / tr
    eksi_di = 100 * rma(eksi_dm, n) / tr
    dx = 100 * (arti_di - eksi_di).abs() / (arti_di + eksi_di).replace(0, np.nan)
    adx = rma(dx.fillna(0), yumusatma)
    return arti_di.fillna(0), eksi_di.fillna(0), adx


def supertrend(df: pd.DataFrame, carpan: float = 3.0, n: int = 10):
    """Standart Supertrend. yon: 1 = yükseliş, -1 = düşüş."""
    hl2 = ((df["High"] + df["Low"]) / 2).values
    a = atr(df, n).values
    ust = hl2 + carpan * a
    alt = hl2 - carpan * a
    kapanis = df["Close"].values
    son_ust, son_alt = ust.copy(), alt.copy()
    yon = np.ones(len(df))
    cizgi = np.full(len(df), np.nan)
    for i in range(1, len(df)):
        son_ust[i] = ust[i] if (ust[i] < son_ust[i - 1] or kapanis[i - 1] > son_ust[i - 1]) else son_ust[i - 1]
        son_alt[i] = alt[i] if (alt[i] > son_alt[i - 1] or kapanis[i - 1] < son_alt[i - 1]) else son_alt[i - 1]
        if yon[i - 1] == 1:
            yon[i] = -1 if kapanis[i] < son_alt[i] else 1
        else:
            yon[i] = 1 if kapanis[i] > son_ust[i] else -1
        cizgi[i] = son_alt[i] if yon[i] == 1 else son_ust[i]
    return pd.Series(cizgi, index=df.index), pd.Series(yon, index=df.index)


def olcekle(v, alt, ust, maks_puan):
    """Değeri alt..ust aralığında 0..maks_puan puana çevirir."""
    v = pd.Series(v)
    return ((v - alt) / (ust - alt)).clip(0, 1).fillna(0) * maks_puan


# ════════════════════════════ VERİ HAZIRLAMA ════════════════════════════
def haftaliga_cevir(df: pd.DataFrame) -> pd.DataFrame:
    h = df.resample("W-FRI").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    )
    return h.dropna(subset=["Close"])


def haftalik_trend_gunluge(df_gunluk: pd.DataFrame, ema_n: int) -> pd.Series:
    """Her gün için: en son tamamlanmış (veya o gün biten) haftanın kapanışı haftalık EMA'nın üstünde mi?
    Geleceğe bakmaz: hafta içindeki günler bir önceki haftanın durumunu kullanır."""
    h = haftaliga_cevir(df_gunluk)
    durum = (h["Close"] > ema(h["Close"], ema_n)).astype(float)
    birlesik = durum.reindex(df_gunluk.index.union(durum.index)).ffill()
    return birlesik.reindex(df_gunluk.index).fillna(0).astype(bool)


# ════════════════════════════ SİNYAL HESAPLAMA ════════════════════════════
def sinyalleri_hesapla(df: pd.DataFrame, ayar: VadeAyari, trend_ok: pd.Series | None = None) -> pd.DataFrame:
    """df: Open/High/Low/Close/Volume sütunlu OHLCV. Gösterge + skor + sinyal sütunları ekler."""
    df = df.copy()
    c, o = df["Close"], df["Open"]
    a = atr(df).replace(0, np.nan)
    r = rsi(c)
    mh = macd_hist(c)
    arti_di, eksi_di, adx = dmi(df)
    hacim_ort = df["Volume"].rolling(20).mean()
    hacim_kat = (df["Volume"] / hacim_ort.replace(0, np.nan)).fillna(0)

    # ---------------- ALIM ----------------
    hizli, yavas = ema(c, ayar.hizli_ema), ema(c, ayar.yavas_ema)
    st_alim, yon_alim = supertrend(df, ayar.st_carpan_alim)
    trend_yukari = yon_alim == 1
    fiyat_ustte = c > yavas

    kesisim = (hizli > yavas) & (hizli.shift() <= yavas.shift())
    sira = pd.Series(np.arange(len(df)), index=df.index, dtype=float)
    son_kesisim = sira.where(kesisim).ffill()
    kesisimden_beri = sira - son_kesisim
    taze_kesisim = (kesisimden_beri <= ayar.kesisim_gecerlilik) & (hizli > yavas)

    if trend_ok is None:
        trend_ok = c > ema(c, ayar.trend_ema)

    alim_skor = (
        pd.Series(np.where(taze_kesisim, 15 * (1 - kesisimden_beri / (ayar.kesisim_gecerlilik + 1)), 0), index=df.index)
        + np.where(fiyat_ustte, 10, 0)
        + np.where(trend_yukari, 10, 0)
        + np.where((r >= 50) & (r <= 75), olcekle(r, 50, 65, 15), 0)
        + np.where(c > o, olcekle(hacim_kat, 1, 2, 15), 0)
        + np.where(mh > 0, olcekle(mh / a, 0, 0.3, 10), 0)
        + np.where(mh > mh.shift(), 5, 0)
        + olcekle((c - c.shift()) / a, 0, 1, 10).values
        + np.where(arti_di > eksi_di, olcekle(adx, 20, 40, 10), 0)
    ).fillna(0)

    kosul = taze_kesisim & fiyat_ustte & trend_ok & (alim_skor >= ayar.min_skor)
    grup = kesisim.cumsum()
    al = kosul & (kosul.astype(int).groupby(grup).cumsum() == 1)   # her kesişime tek sinyal

    # ---------------- SATIŞ ----------------
    kisa, orta, uzun = ema(c, ayar.kisa_ema), ema(c, ayar.orta_ema), ema(c, ayar.uzun_ema)
    st_satis, yon_satis = supertrend(df, ayar.st_carpan_satis)
    trend_yukari_s = yon_satis == 1
    asagi_kesisim = (kisa < orta) & (kisa.shift() >= orta.shift())
    asiri_alimdi = r.rolling(5, min_periods=1).max() >= 70
    di_fark = arti_di - eksi_di

    satis_skor = (
        olcekle(65 - r, 0, 25, 15)
        + np.where(asiri_alimdi, 5, 0)
        + np.where(c < o, olcekle(hacim_kat, 1, 2, 15), 0)
        + olcekle((c.shift(2) - c) / a, 0, 1.5, 15).values
        + np.where(mh < 0, olcekle(-mh / a, 0, 0.3, 10), 0)
        + np.where(mh < mh.shift(), 5, 0)
        + np.where(eksi_di > arti_di, 10, np.where(di_fark < di_fark.shift(3), 5, 0))
        + np.where(c < uzun, 15, 0)
        + np.where(trend_yukari_s, olcekle(2 - (c - st_satis) / a, 0, 2, 10), 10)
    ).fillna(0)
    satis_skor.index = df.index

    satis_taban = asagi_kesisim & trend_yukari_s
    kar_al = satis_taban & (satis_skor >= ayar.kar_al_min) & (satis_skor < ayar.sat_min)
    sat = satis_taban & (satis_skor >= ayar.sat_min)
    cik = (yon_satis == -1) & (yon_satis.shift() == 1)

    df["EMA_hizli"], df["EMA_yavas"] = hizli, yavas
    df["EMA_kisa"], df["EMA_orta"] = kisa, orta
    df["Supertrend"] = st_alim
    df["RSI"], df["ATR"], df["ADX"], df["Hacim_kat"] = r, a, adx, hacim_kat
    df["Alim_skor"], df["Satis_skor"] = alim_skor, satis_skor
    df["AL"], df["KAR_AL"], df["SAT"], df["CIK"] = al, kar_al, sat, cik
    df["Stop"] = c - a * ayar.stop_atr
    df["Hedef"] = c + a * ayar.stop_atr * ayar.risk_odul
    return df


def _gunluk_hizala(seri: pd.Series, index: pd.DatetimeIndex) -> pd.Series:
    """Günlük seriyi hedef indekse 'o tarihte ya da öncesinde bilinen son değer' ile taşır."""
    return seri.reindex(seri.index.union(index)).ffill().reindex(index)


def alim_filtreleri_uygula(sonuc: pd.DataFrame, df_gunluk: pd.DataFrame,
                           endeks: pd.DataFrame | None, f: AlimFiltreleri) -> pd.DataFrame:
    """AL_filtreli sütununu ekler. Koşullar günlük veriyle, yalnızca geçmişe bakarak hesaplanır;
    haftalık sonuçta haftanın son işlem gününün değeri kullanılır."""
    sonuc = sonuc.copy()
    gecti = pd.Series(True, index=sonuc.index)
    if f.aktif:
        c = df_gunluk["Close"]
        if f.piyasa_ema:
            if endeks is None:
                raise ValueError("Piyasa rejimi filtresi için endeks (XU100) verisi gerekir.")
            xu = endeks["Close"]
            ust = (xu > ema(xu, f.piyasa_ema)).astype(float)
            sonuc["F_piyasa"] = _gunluk_hizala(ust, sonuc.index).fillna(0).astype(bool)
            gecti &= sonuc["F_piyasa"]
        if f.uzun_trend_ema:
            ust = (c > ema(c, f.uzun_trend_ema)).astype(float)
            sonuc["F_uzun_trend"] = _gunluk_hizala(ust, sonuc.index).fillna(0).astype(bool)
            gecti &= sonuc["F_uzun_trend"]
        if f.tavan_esik is not None:
            alt = (c / c.shift() - 1 < f.tavan_esik).astype(float)
            sonuc["F_tavan"] = _gunluk_hizala(alt, sonuc.index).fillna(0).astype(bool)
            gecti &= sonuc["F_tavan"]
    sonuc["AL_filtreli"] = sonuc["AL"] & gecti
    return sonuc


def hisse_analiz(df_gunluk: pd.DataFrame, ayar: VadeAyari, endeks: pd.DataFrame | None = None) -> pd.DataFrame:
    """Vadeye göre doğru zaman dilimini seçip sinyalleri hesaplar.

    Vadenin alım filtreleri açıksa AL_filtreli sütunu eklenir (endeks = XU100 günlük verisi).
    """
    if ayar.trend_filtre == "haftalik":
        trend = haftalik_trend_gunluge(df_gunluk, ayar.trend_ema)
        sonuc = sinyalleri_hesapla(df_gunluk, ayar, trend)
    else:
        sonuc = sinyalleri_hesapla(haftaliga_cevir(df_gunluk), ayar)
    if not ayar.filtreler.aktif:
        sonuc["AL_filtreli"] = sonuc["AL"]
        return sonuc
    return alim_filtreleri_uygula(sonuc, df_gunluk, endeks, ayar.filtreler)


# ════════════════════════════ SKOR KIRILIMI ════════════════════════════
# Panelde alım skorunun hangi kalemden kaç puan aldığını göstermek için. Sinyal mantığına
# dokunmaz: sinyalleri_hesapla'daki alım skoru formülünün aynı kalemlerini ayrı sütunlarda
# döndürür. Kalemlerin toplamı Alim_skor'a eşittir (tests/test_tarayici_motor.py denetler).
ALIM_KALEMLERI = {           # sütun -> maksimum puan
    "kesisim": 15,
    "fiyat_ema": 10,
    "supertrend": 10,
    "rsi": 15,
    "hacim": 15,
    "macd": 15,
    "momentum": 10,
    "adx": 10,
}


def alim_skor_kalemleri(df: pd.DataFrame, ayar: VadeAyari) -> pd.DataFrame:
    """sinyalleri_hesapla'ya verilen aynı OHLCV tablosu için alım skoru kalemlerini döndürür."""
    c, o = df["Close"], df["Open"]
    a = atr(df).replace(0, np.nan)
    r = rsi(c)
    mh = macd_hist(c)
    arti_di, eksi_di, adx = dmi(df)
    hacim_kat = (df["Volume"] / df["Volume"].rolling(20).mean().replace(0, np.nan)).fillna(0)

    hizli, yavas = ema(c, ayar.hizli_ema), ema(c, ayar.yavas_ema)
    _, yon_alim = supertrend(df, ayar.st_carpan_alim)
    kesisim = (hizli > yavas) & (hizli.shift() <= yavas.shift())
    sira = pd.Series(np.arange(len(df)), index=df.index, dtype=float)
    kesisimden_beri = sira - sira.where(kesisim).ffill()
    taze_kesisim = (kesisimden_beri <= ayar.kesisim_gecerlilik) & (hizli > yavas)

    def seri(degerler) -> pd.Series:
        return pd.Series(np.asarray(degerler, dtype=float), index=df.index).fillna(0)

    return pd.DataFrame({
        "kesisim": seri(np.where(taze_kesisim, 15 * (1 - kesisimden_beri / (ayar.kesisim_gecerlilik + 1)), 0)),
        "fiyat_ema": seri(np.where(c > yavas, 10, 0)),
        "supertrend": seri(np.where(yon_alim == 1, 10, 0)),
        "rsi": seri(np.where((r >= 50) & (r <= 75), olcekle(r, 50, 65, 15), 0)),
        "hacim": seri(np.where(c > o, olcekle(hacim_kat, 1, 2, 15), 0)),
        "macd": seri(np.where(mh > 0, olcekle(mh / a, 0, 0.3, 10), 0) + np.where(mh > mh.shift(), 5, 0)),
        "momentum": seri(olcekle((c - c.shift()) / a, 0, 1, 10).values),
        "adx": seri(np.where(arti_di > eksi_di, olcekle(adx, 20, 40, 10), 0)),
    })


# ════════════════════════════ TARAMA ════════════════════════════
def son_sinyal(df: pd.DataFrame, sutun: str, son_bar: int):
    """Son `son_bar` bar içindeki en yeni sinyali döndürür (yoksa None)."""
    pencere = df.iloc[-son_bar:]
    isaretli = pencere[pencere[sutun]]
    if isaretli.empty:
        return None
    satir = isaretli.iloc[-1]
    kac_bar_once = len(df) - 1 - df.index.get_loc(isaretli.index[-1])
    return satir, kac_bar_once


def tara(veriler: dict[str, pd.DataFrame], ayar: VadeAyari, son_bar: int, endeks: pd.DataFrame | None = None):
    """Tüm hisseleri tarar. Alım ve satış listelerini + her hissenin analiz tablosunu döndürür."""
    alimlar, satislar, analizler = [], [], {}
    for kod, df in veriler.items():
        if df is None or len(df) < 120:
            continue
        try:
            sonuc = hisse_analiz(df, ayar, endeks)
        except Exception:
            continue
        analizler[kod] = sonuc
        son = sonuc.iloc[-1]

        bulunan = son_sinyal(sonuc, "AL", son_bar)
        if bulunan:
            satir, once = bulunan
            alimlar.append({
                "Hisse": kod, "Skor": round(satir["Alim_skor"]), "Sinyal": "Bugün" if once == 0 else f"{once} bar önce",
                "Sinyal fiyatı": round(satir["Close"], 2), "Güncel fiyat": round(son["Close"], 2),
                "Değişim %": round((son["Close"] / satir["Close"] - 1) * 100, 1),
                "Stop": round(satir["Stop"], 2), "Hedef": round(satir["Hedef"], 2),
                "RSI": round(son["RSI"], 1), "Hacim x": round(son["Hacim_kat"], 2),
                "_once": once,
            })

        for sutun, ad in (("SAT", "SAT"), ("KAR_AL", "KAR AL"), ("CIK", "ÇIK (trend döndü)")):
            bulunan = son_sinyal(sonuc, sutun, son_bar)
            if bulunan:
                satir, once = bulunan
                satislar.append({
                    "Hisse": kod, "Sinyal türü": ad, "Skor": round(satir["Satis_skor"]),
                    "Sinyal": "Bugün" if once == 0 else f"{once} bar önce",
                    "Sinyal fiyatı": round(satir["Close"], 2), "Güncel fiyat": round(son["Close"], 2),
                    "RSI": round(son["RSI"], 1), "_once": once,
                })
                break   # bir hisse için en güçlü satış sinyali yeterli (SAT > KAR AL > ÇIK)

    alim_sutunlar = ["Hisse", "Skor", "Sinyal", "Sinyal fiyatı", "Güncel fiyat", "Değişim %",
                     "Stop", "Hedef", "RSI", "Hacim x", "_once"]
    satis_sutunlar = ["Hisse", "Sinyal türü", "Skor", "Sinyal", "Sinyal fiyatı", "Güncel fiyat", "RSI", "_once"]
    alim_df = pd.DataFrame(alimlar, columns=alim_sutunlar)
    satis_df = pd.DataFrame(satislar, columns=satis_sutunlar)
    alim_df = alim_df.sort_values(["_once", "Skor"], ascending=[True, False]).drop(columns="_once")
    satis_df = satis_df.sort_values(["_once", "Skor"], ascending=[True, False]).drop(columns="_once")
    return alim_df, satis_df, analizler


# ════════════════════════════ GEÇMİŞ İSABET TESTİ ════════════════════════════
def isabet_testi(analizler: dict[str, pd.DataFrame], ayar: VadeAyari) -> pd.DataFrame:
    """Her sinyal türü için: sinyalden sonraki N bar içinde fiyat %X hareket etti mi?
    Aynı ölçüm tüm barlar için yapılır (rastgele gün). Sinyal ancak rastgeleden iyiyse işe yarar."""
    n, p = ayar.test_bar, ayar.test_yuzde / 100
    toplam = {k: {"adet": 0, "isabet": 0, "getiri": 0.0} for k in ("AL", "KAR_AL", "SAT", "CIK", "taban")}
    taban_dusus = {"adet": 0, "isabet": 0}

    for df in analizler.values():
        d = df.iloc[60:]   # göstergelerin oturması için ilk barları at
        if len(d) <= n + 1:
            continue
        gelecek_max = d["High"][::-1].rolling(n, min_periods=n).max()[::-1].shift(-1)
        gelecek_min = d["Low"][::-1].rolling(n, min_periods=n).min()[::-1].shift(-1)
        getiri = d["Close"].shift(-n) / d["Close"] - 1
        gecerli = getiri.notna() & gelecek_max.notna()
        yukari = (gelecek_max >= d["Close"] * (1 + p)) & gecerli
        asagi = (gelecek_min <= d["Close"] * (1 - p)) & gecerli

        toplam["taban"]["adet"] += int(gecerli.sum())
        toplam["taban"]["isabet"] += int(yukari.sum())
        toplam["taban"]["getiri"] += float(getiri[gecerli].sum())
        taban_dusus["adet"] += int(gecerli.sum())
        taban_dusus["isabet"] += int(asagi.sum())

        for k in ("AL", "KAR_AL", "SAT", "CIK"):
            m = d[k] & gecerli
            hedef = yukari if k == "AL" else asagi
            toplam[k]["adet"] += int(m.sum())
            toplam[k]["isabet"] += int((m & hedef).sum())
            toplam[k]["getiri"] += float(getiri[m].sum())

    def oran(x, y):
        return x / y * 100 if y else np.nan

    taban_yukari = oran(toplam["taban"]["isabet"], toplam["taban"]["adet"])
    taban_asagi = oran(taban_dusus["isabet"], taban_dusus["adet"])
    taban_getiri = oran(toplam["taban"]["getiri"], toplam["taban"]["adet"])

    satirlar = []
    adlar = {"AL": "AL", "KAR_AL": "KAR AL", "SAT": "SAT", "CIK": "ÇIK"}
    for k, ad in adlar.items():
        t = toplam[k]
        isabet = oran(t["isabet"], t["adet"])
        taban = taban_yukari if k == "AL" else taban_asagi
        satirlar.append({
            "Sinyal": ad,
            "Adet": t["adet"],
            "Ne sayıldı": f"{n} bar içinde +%{ayar.test_yuzde:g}" if k == "AL" else f"{n} bar içinde -%{ayar.test_yuzde:g}",
            "İsabet %": round(isabet, 1),
            "Rastgele gün %": round(taban, 1),
            "Avantaj (puan)": round(isabet - taban, 1),
            f"Ort. {n} bar getirisi %": round(oran(t["getiri"], t["adet"]), 2),
            "Rastgele ort. getiri %": round(taban_getiri, 2),
        })
    return pd.DataFrame(satirlar)
