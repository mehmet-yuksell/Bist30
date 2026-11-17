"""Sinyal Günlüğü ve İleri Test (arayüzden bağımsız).

Günlük (data/sinyal_gunlugu.csv): her iş günü kapanıştan sonra o günün sinyalleri yazılır
(tools/sinyal_gunlugu.py, GitHub Actions). Kayıt yalnızca o gün bilinenle yapılır; böylece
günlükteki sinyallerin sonucu geleceğe bakmadan, gerçek zamanlı bir "ileri test" olur.

- Kısa vade (günlük) ve FIRSAT: son günlük bar bugünse kaydedilir.
- Orta vade (haftalık): yalnızca hafta tamamlandığında (son haftalık bar bugün bitiyorsa) kaydedilir;
  cuma tatilse o haftanın sinyali kaydedilmez (sınırlama).
- giris_referans: sinyal günü kapanışı. Gerçek giriş, Aşama 1 kuralıyla ertesi barın açılışıdır.

İleri test, Aşama 1 değerlendirmesini (evaluation.py) aynen kullanır. Kayıttan sonra temettü/bölünme
düzeltmesi geçmiş fiyatları ölçeklerse stop ve hedef de aynı oranla (sinyal günü kapanışı /
giris_referans) ölçeklenir.
"""

import pandas as pd

import evaluation as ev
import firsat
import motor_veri
import panel_veri as pv
import tarayici_motor as motor

SUTUNLAR = ["tarih", "vade", "tur", "kod", "skor", "not", "giris_referans", "stop", "hedef"]
ANAHTAR = ["tarih", "vade", "tur", "kod"]
SAYISAL = ["skor", "giris_referans", "stop", "hedef"]
SATIS_SIDE = {"SAT", "KAR_AL", "CIK"}
TIMEOUT = {pv.KISA: 20, pv.ORTA: 12}
MIN_SINYAL = 30


# ---------------------------------------------------------------------------
# Kayıt
# ---------------------------------------------------------------------------

def _satis_seviyeleri(satir: pd.Series, ayar) -> tuple[float, float]:
    """Satış sinyali için alım seviyelerinin aynası (raporla aynı): stop yukarıda, hedef aşağıda."""
    mesafe = float(satir["ATR"]) * ayar.stop_atr
    return float(satir["Close"]) + mesafe, float(satir["Close"]) - mesafe * ayar.risk_odul


def vade_satirlari(sonuc: pd.DataFrame, vade: str, kod: str, not_bul) -> list[dict]:
    """Bir vadenin son barındaki alım ve (en güçlü) satış sinyali satırları."""
    son = sonuc.iloc[-1]
    tarih = sonuc.index[-1].date().isoformat()
    satirlar = []
    if bool(son[pv.ALIM_SUTUNU]):
        satirlar.append({"tarih": tarih, "vade": vade, "tur": "AL", "kod": kod,
                         "skor": round(float(son["Alim_skor"]), 1), "not": not_bul(float(son["Alim_skor"]), vade) or "",
                         "giris_referans": float(son["Close"]), "stop": float(son["Stop"]), "hedef": float(son["Hedef"])})
    uyari = pv.satis_uyarisi(sonuc)
    if uyari:
        stop, hedef = _satis_seviyeleri(son, pv.VADE_AYARI[vade])
        satirlar.append({"tarih": tarih, "vade": vade, "tur": uyari["tur"], "kod": kod,
                         "skor": round(uyari["skor"], 1), "not": "", "giris_referans": float(son["Close"]),
                         "stop": stop, "hedef": hedef})
    return satirlar


def firsat_satiri(fs: pd.DataFrame, kod: str) -> dict | None:
    """Son gün FIRSAT sinyali varsa satır; hedef referansı EMA 20 ile 2R'nin küçüğü (kapanışa göre)."""
    son = fs.iloc[-1]
    if not bool(son["FIRSAT"]):
        return None
    kapanis, stop = float(son["Close"]), float(son["Stop"])
    hedef = min(float(son["EMA_hedef"]), kapanis + firsat.VARSAYILAN.risk_odul * (kapanis - stop))
    return {"tarih": fs.index[-1].date().isoformat(), "vade": pv.KISA, "tur": "FIRSAT", "kod": kod,
            "skor": None, "not": "", "giris_referans": kapanis, "stop": stop, "hedef": hedef}


def gunun_sinyalleri(histories: dict, endeks: pd.DataFrame | None, bugun, kodlar, not_bul) -> list[dict]:
    """Bugün kapanmış bara ait tüm sinyaller (bugünün verisi olmayan hisse atlanır)."""
    endeks_g = pv.endeks_girdisi(endeks)
    satirlar = []
    for kod in kodlar:
        df = histories.get(kod)
        if df is None or len(df) < motor_veri.MIN_BARS or df.index[-1].date() != bugun:
            continue
        kisa = pv.analiz(df, pv.KISA)
        if kisa is not None:
            satirlar += vade_satirlari(kisa, pv.KISA, kod, not_bul)
        if endeks_g is not None:
            orta = pv.analiz(df, pv.ORTA, endeks_g)
            if orta is not None and orta.index[-1].date() == bugun:  # hafta bugün tamamlandı
                satirlar += vade_satirlari(orta, pv.ORTA, kod, not_bul)
        fs = pv.firsat_analizi(df, endeks_g)
        if fs is not None:
            satir = firsat_satiri(fs, kod)
            if satir:
                satirlar.append(satir)
    return satirlar


def ekle(gunluk: pd.DataFrame, yeni: list[dict]) -> pd.DataFrame:
    """Yeni satırları ekler; aynı (tarih, vade, tür, kod) ikinci kez yazılmaz (iş tekrar çalışırsa)."""
    parcalar = [x for x in (gunluk, pd.DataFrame(yeni, columns=SUTUNLAR)) if not x.empty]
    birlesik = pd.concat(parcalar, ignore_index=True) if parcalar else pd.DataFrame(columns=SUTUNLAR)
    birlesik = birlesik.drop_duplicates(subset=ANAHTAR, keep="first")
    for sutun in SAYISAL:
        birlesik[sutun] = pd.to_numeric(birlesik[sutun], errors="coerce")
    birlesik["not"] = birlesik["not"].fillna("").astype(str)
    return birlesik.sort_values(ANAHTAR).reset_index(drop=True)[SUTUNLAR]


def oku(yol) -> pd.DataFrame:
    try:
        df = pd.read_csv(yol, dtype={"not": str}, keep_default_na=False, na_values=[""])
    except FileNotFoundError:
        return pd.DataFrame(columns=SUTUNLAR)
    df["not"] = df["not"].fillna("")
    return df[SUTUNLAR]


# ---------------------------------------------------------------------------
# İleri test
# ---------------------------------------------------------------------------

def degerlendir(gunluk: pd.DataFrame, histories: dict, endeks: pd.DataFrame | None) -> pd.DataFrame:
    """Günlükteki her sinyalin Aşama 1 kurallarıyla sonucu (satır başına bir işlem)."""
    endeks_g = pv.endeks_girdisi(endeks)
    satirlar = []
    for kod, grup in gunluk.groupby("kod"):
        df = histories.get(kod)
        if df is None or df.empty:
            continue
        girdi = motor_veri.motor_girdisi(df)
        haftalik = motor.haftaliga_cevir(girdi)
        fs = None
        for _, r in grup.iterrows():
            tarih = pd.Timestamp(r["tarih"])
            bars = haftalik if r["vade"] == pv.ORTA else girdi
            if tarih not in bars.index:
                continue
            i = bars.index.get_loc(tarih)
            sonuc = None
            seviyeler = {}
            if r["tur"] == "FIRSAT":
                fs = fs if fs is not None else firsat.firsat_hesapla(girdi, endeks_g)
                isaret = pd.Series(fs.index == tarih, index=fs.index)
                t = firsat.islemler(fs, isaret)
                sonuc = t.iloc[0].to_dict() if not t.empty else None
            else:
                oran = float(bars["Close"].iloc[i]) / float(r["giris_referans"])
                seviyeler = {"stop": float(r["stop"]) * oran, "hedef": float(r["hedef"]) * oran}
                k = ev.Kurallar(timeout=TIMEOUT[r["vade"]], side=-1 if r["tur"] in SATIS_SIDE else 1)
                o, h, lo, c = (bars[col].to_numpy(dtype=float) for col in ("Open", "High", "Low", "Close"))
                sonuc = ev.simule_et(o, h, lo, c, i, seviyeler["stop"], seviyeler["hedef"], k)
            if sonuc is None:
                continue
            # Açık/geçersiz işlemde simülasyon seviye döndürmez; ölçeklenmiş seviyeler yine de yazılır
            satirlar.append({**{c: r[c] for c in SUTUNLAR}, **seviyeler,
                             **{k: v for k, v in sonuc.items() if k not in ("kod", "tarih")}})
    t = pd.DataFrame(satirlar)
    if not t.empty:
        t["tarih"] = pd.to_datetime(t["tarih"])
    return t


def ozetle(islemler: pd.DataFrame) -> pd.DataFrame:
    """Vade × tür için Aşama 1 metrikleri (yalnızca tamamlanmış işlemler ölçülür)."""
    if islemler.empty:
        return pd.DataFrame()
    satirlar = []
    for (vade, tur), t in islemler.groupby(["vade", "tur"]):
        s = ev.ozet(t, -1 if tur in SATIS_SIDE else 1)
        satirlar.append({"vade": vade, "tur": tur, **s})
    return pd.DataFrame(satirlar)


def tamamlanan(islemler: pd.DataFrame) -> int:
    return 0 if islemler.empty else int(islemler["sonuc"].isin(ev.OUTCOMES).sum())


def yeterli_mi(islemler: pd.DataFrame) -> bool:
    return tamamlanan(islemler) >= MIN_SINYAL

