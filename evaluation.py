"""Sinyal değerlendirme altyapısı (arayüzden bağımsız).

Kurallar (docs/sistem_raporu.md, "Metodoloji"):
- Sinyal gün (hafta) sonunda oluşur; işleme ERTESİ barın açılışından girilir.
- Stop ve hedef sinyal barında bilinen seviyelerdir. Bir barda önce stop kontrol edilir: aynı
  barda hem stop hem hedef görüldüyse sonuç stop sayılır (gün içi sıra bilinmez, kötümser seçim).
- Fiyat stop'un ötesinde açılırsa çıkış açılıştandır (kayıp 1R'yi aşabilir); hedefin ötesinde
  açılırsa çıkış yine açılıştandır.
- Giriş açılışı zaten stop'un ya da hedefin ötesindeyse işlem açılmaz ("gecersiz").
- Zaman aşımında zaman penceresinin son barının kapanışından çıkılır. Pencere giriş barı dahil
  `timeout` bardır. Veri pencereyi tamamlamadan biterse ve çıkış olmadıysa sonuç "acik"tır;
  açık ve geçersiz işlemler metriklere girmez, sayıları ayrıca raporlanır.
- Her işleme gidiş-dönüş `cost` (varsayılan %0,2) maliyet uygulanır; R getirisi maliyet sonrasıdır.
- 1R = giriş ile stop arasındaki mesafe.

Uzun (AL) işlemler side=1, satış sinyalleri açığa satış gibi side=-1 ile değerlendirilir:
satış sinyalinin isabeti "sonrasında fiyat düştü mü" sorusudur.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

GELISTIRME = (pd.Timestamp("2021-01-01"), pd.Timestamp("2024-12-31"))
TEST = (pd.Timestamp("2025-01-01"), pd.Timestamp("2100-01-01"))
DONEMLER = {"GELİŞTİRME": GELISTIRME, "TEST": TEST}

COST = 0.002
OUTCOMES = ("hedef", "stop", "zaman")


@dataclass(frozen=True)
class Kurallar:
    timeout: int          # giriş barı dahil en fazla kaç bar tutulur
    side: int = 1         # 1: alım, -1: satış (açığa satış gibi)
    cost: float = COST    # gidiş-dönüş maliyet oranı


def simule_et(o: np.ndarray, h: np.ndarray, lo: np.ndarray, c: np.ndarray,
              sinyal: int, stop: float, hedef, k: Kurallar) -> dict:
    """Tek bir sinyali sinyal barından (indeks) itibaren simüle eder.

    hedef: sabit seviye ya da bar bar geçerli hedef dizisi (o barın açılışından önce bilinen
    değerlerle hesaplanmış olmalı; ör. bir önceki günün EMA'sı).
    """
    n = len(c)
    giris_i = sinyal + 1
    if giris_i >= n:
        return {"sonuc": "acik"}
    giris = float(o[giris_i])
    s = k.side
    hedef_dizisi = np.ndim(hedef) > 0
    hedef_bar = (lambda j: float(hedef[j])) if hedef_dizisi else (lambda j: float(hedef))
    # Açılış zaten stop'un ya da hedefin ötesinde (ya da hedef bilinmiyor): işlem açılmaz
    ilk_hedef = hedef_bar(giris_i)
    if not np.isfinite(ilk_hedef) or s * (giris - stop) <= 0 or s * (ilk_hedef - giris) <= 0:
        return {"sonuc": "gecersiz", "giris_i": giris_i, "giris": giris}
    risk = abs(giris - stop)

    son_i = sinyal + k.timeout
    en_iyi, en_kotu = giris, giris
    cikis = cikis_i = None
    sonuc = None
    for j in range(giris_i, min(son_i, n - 1) + 1):
        lehte = h[j] if s == 1 else lo[j]      # işlem yönünde en uç fiyat
        aleyhte = lo[j] if s == 1 else h[j]    # ters yönde en uç fiyat
        en_kotu = min(en_kotu, aleyhte) if s == 1 else max(en_kotu, aleyhte)
        if s * (aleyhte - stop) <= 0:          # stop görüldü (aynı barda hedef de olsa stop)
            # Bar stop'un ötesinde açıldıysa çıkış açılıştan (giriş barında açılış = giriş)
            cikis = o[j] if s * (o[j] - stop) < 0 else stop
            cikis_i, sonuc = j, "stop"
            en_iyi = max(en_iyi, lehte) if s == 1 else min(en_iyi, lehte)
            break
        en_iyi = max(en_iyi, lehte) if s == 1 else min(en_iyi, lehte)
        hedef_j = hedef_bar(j)
        if np.isfinite(hedef_j) and s * (lehte - hedef_j) >= 0:
            cikis = o[j] if s * (o[j] - hedef_j) > 0 else hedef_j
            cikis_i, sonuc, hedef_son = j, "hedef", hedef_j
            break
    if sonuc is None:
        if son_i >= n:
            return {"sonuc": "acik", "giris_i": giris_i, "giris": giris}
        cikis, cikis_i, sonuc = float(c[son_i]), son_i, "zaman"
    if sonuc != "hedef":
        hedef_son = hedef_bar(cikis_i)

    brut = s * (cikis - giris) / giris
    net = brut - k.cost
    return {
        "sonuc": sonuc,
        "giris_i": giris_i,
        "cikis_i": cikis_i,
        "giris": giris,
        "cikis": float(cikis),
        "stop": float(stop),
        "hedef": float(hedef_son),              # çıkış barında geçerli hedef
        "gun": cikis_i - sinyal,
        "getiri": net,                          # maliyet sonrası, oran
        "r": net * giris / risk,                # maliyet sonrası, R
        "mfe": s * (en_iyi - giris) / giris,    # en yüksek kâr (oran)
        "mae": s * (en_kotu - giris) / giris,   # en büyük ters hareket (oran, ≤ 0)
        "mfe_r": s * (en_iyi - giris) / risk,
        "mae_r": s * (en_kotu - giris) / risk,
    }


def islemler(df: pd.DataFrame, sinyal_sutunu: pd.Series, stop: pd.Series, hedef: pd.Series,
             k: Kurallar, kod: str = "", ilk_bar: int = 0) -> pd.DataFrame:
    """`sinyal_sutunu` True olan her bar için işlem satırı (tarih indeksli değil, satır listesi).

    ilk_bar: göstergelerin oturması için bu bardan önceki sinyaller alınmaz.
    """
    o, h, lo, c = (df[col].to_numpy(dtype=float) for col in ("Open", "High", "Low", "Close"))
    stop_a, hedef_a = stop.to_numpy(dtype=float), hedef.to_numpy(dtype=float)
    satirlar = []
    for i in np.flatnonzero(sinyal_sutunu.to_numpy(dtype=bool)):
        if i < ilk_bar or not (np.isfinite(stop_a[i]) and np.isfinite(hedef_a[i])):
            continue
        sonuc = simule_et(o, h, lo, c, int(i), stop_a[i], hedef_a[i], k)
        sonuc["kod"] = kod
        sonuc["tarih"] = df.index[i]
        if "giris_i" in sonuc:
            sonuc["giris_tarihi"] = df.index[sonuc["giris_i"]]
        if "cikis_i" in sonuc:
            sonuc["cikis_tarihi"] = df.index[sonuc["cikis_i"]]
        satirlar.append(sonuc)
    return pd.DataFrame(satirlar)


def islemler_gecikmeli(df: pd.DataFrame, sinyal_sutunu: pd.Series, stop: pd.Series, hedef: pd.Series,
                       k: Kurallar, kod: str = "", ilk_bar: int = 0, gecikme: int = 1) -> pd.DataFrame:
    """Teyit beklenen girişler: stop/hedef sinyal barından, giriş `gecikme` bar sonraki barın açılışı.

    Satırın "tarih"i asıl sinyal tarihidir (dönem ataması değişmesin); "gun" da asıl sinyal
    barından sayılır, böylece gecikmenin süresi de ölçüme girer.
    """
    o, h, lo, c = (df[col].to_numpy(dtype=float) for col in ("Open", "High", "Low", "Close"))
    stop_a, hedef_a = stop.to_numpy(dtype=float), hedef.to_numpy(dtype=float)
    satirlar = []
    for i in np.flatnonzero(sinyal_sutunu.to_numpy(dtype=bool)):
        if i < ilk_bar or not (np.isfinite(stop_a[i]) and np.isfinite(hedef_a[i])):
            continue
        sonuc = simule_et(o, h, lo, c, int(i) + gecikme, stop_a[i], hedef_a[i], k)
        if "gun" in sonuc:
            sonuc["gun"] += gecikme
        sonuc["kod"] = kod
        sonuc["tarih"] = df.index[i]
        if "giris_i" in sonuc:
            sonuc["giris_tarihi"] = df.index[sonuc["giris_i"]]
        if "cikis_i" in sonuc:
            sonuc["cikis_tarihi"] = df.index[sonuc["cikis_i"]]
        satirlar.append(sonuc)
    return pd.DataFrame(satirlar)


def endeks_getirisi(trades: pd.DataFrame, endeks: pd.DataFrame) -> pd.Series:
    """Her işlem için endeksin aynı tarihlerde (giriş açılışı → çıkış kapanışı) getirisi."""
    if trades.empty or "giris_tarihi" not in trades:
        return pd.Series(dtype=float)
    acilis = endeks["Open"].reindex(trades["giris_tarihi"]).to_numpy()
    kapanis = endeks["Close"].reindex(trades["cikis_tarihi"]).to_numpy()
    return pd.Series(kapanis / acilis - 1, index=trades.index)


def en_uzun_kayip_serisi(r: pd.Series) -> int:
    en_uzun = mevcut = 0
    for deger in r:
        mevcut = mevcut + 1 if deger < 0 else 0
        en_uzun = max(en_uzun, mevcut)
    return en_uzun


def ozet(trades: pd.DataFrame, side: int = 1) -> dict:
    """Tamamlanmış işlemlerin metrikleri; açık/geçersiz işlemler yalnızca sayılır.

    Kayıp serisi, işlemler sinyal tarihine (sonra koda) göre sıralanarak hesaplanır.
    endeks_fazla: aynı tarihlerde endekse göre fazla getiri (satışta endeksin tersi).
    """
    if trades.empty:
        return {"sinyal": 0, "acik": 0, "gecersiz": 0}
    bitti = trades[trades["sonuc"].isin(OUTCOMES)].sort_values(["tarih", "kod"])
    n = len(bitti)
    sonuc = {
        "sinyal": n,
        "acik": int((trades["sonuc"] == "acik").sum()),
        "gecersiz": int((trades["sonuc"] == "gecersiz").sum()),
    }
    if n == 0:
        return sonuc
    r = bitti["r"]
    kazanc, kayip = r[r > 0].sum(), -r[r < 0].sum()
    hedef_gun = bitti.loc[bitti["sonuc"] == "hedef", "gun"]
    sonuc.update({
        "hedef_pct": (bitti["sonuc"] == "hedef").mean() * 100,
        "stop_pct": (bitti["sonuc"] == "stop").mean() * 100,
        "zaman_pct": (bitti["sonuc"] == "zaman").mean() * 100,
        "beklenen_r": r.mean(),
        "r_std_hata": r.std() / np.sqrt(n) if n > 1 else np.nan,
        "ort_getiri_pct": bitti["getiri"].mean() * 100,
        "kar_faktoru": kazanc / kayip if kayip > 0 else np.inf,
        "hedef_medyan_gun": hedef_gun.median() if len(hedef_gun) else np.nan,
        "hedef_gun_q1": hedef_gun.quantile(0.25) if len(hedef_gun) else np.nan,
        "hedef_gun_q3": hedef_gun.quantile(0.75) if len(hedef_gun) else np.nan,
        "kayip_serisi": en_uzun_kayip_serisi(r),
        "mfe_r_medyan": bitti["mfe_r"].median(),
        "mae_r_medyan": bitti["mae_r"].median(),
    })
    if "endeks" in bitti:
        brut = bitti["getiri"] + COST
        sonuc["endeks_ort_pct"] = bitti["endeks"].mean() * 100
        sonuc["endeks_fazla_pct"] = (brut - side * bitti["endeks"]).mean() * 100
    return sonuc


def doneme_gore(trades: pd.DataFrame, side: int = 1) -> dict[str, dict]:
    """GELİŞTİRME ve TEST dönemleri için ayrı özet (dönem = sinyal tarihi)."""
    sonuc = {}
    for ad, (bas, bit) in DONEMLER.items():
        if trades.empty:
            sonuc[ad] = ozet(trades, side)
            continue
        maske = (trades["tarih"] >= bas) & (trades["tarih"] <= bit)
        sonuc[ad] = ozet(trades[maske], side)
    return sonuc


def al_tut(endeks: pd.DataFrame, bas: pd.Timestamp, bit: pd.Timestamp) -> float:
    """Endeksin dönem içindeki al-tut getirisi (ilk açılıştan son kapanışa, oran)."""
    donem = endeks.loc[(endeks.index >= bas) & (endeks.index <= bit)]
    if donem.empty:
        return np.nan
    return float(donem["Close"].iloc[-1] / donem["Open"].iloc[0] - 1)


def tamamlanmis_haftalar(haftalik: pd.DataFrame, son_gunluk: pd.Timestamp) -> pd.DataFrame:
    """W-FRI etiketli haftalık tablodan, son günlük veriden sonra biten (yarım) haftayı atar."""
    return haftalik.loc[haftalik.index <= son_gunluk]
