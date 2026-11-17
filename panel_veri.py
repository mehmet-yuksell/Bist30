"""Panel listeleri: motor ve FIRSAT çıktılarından ekranda gösterilecek özetler (arayüzden bağımsız).

- Kısa vade günlük, orta vade haftalık barlarla çalışır. Orta vadede alım sinyali, kabul edilmiş
  alım filtrelerinden geçen AL_filtreli sütunudur (Aşama 2).
- Haftalık son bar, haftanın son işlem günü (genelde cuma) kapanmadan tamamlanmış sayılmaz.
- Satış uyarısında öncelik motorun tara() fonksiyonundaki gibidir: SAT > KAR AL > ÇIK.
"""

import numpy as np
import pandas as pd

import firsat
import motor_veri
import tarayici_motor as motor

KISA, ORTA = "kisa", "orta"
VADE_AYARI = {KISA: motor.KISA_VADE, ORTA: motor.ORTA_VADE}
ALIM_SUTUNU = "AL_filtreli"
SATIS_TURLERI = (("SAT", "SAT"), ("KAR_AL", "KAR AL"), ("CIK", "ÇIK"))


def endeks_girdisi(endeks: pd.DataFrame | None) -> pd.DataFrame | None:
    return motor_veri.motor_girdisi(endeks) if endeks is not None and len(endeks) else None


def analiz(df: pd.DataFrame, vade: str, endeks: pd.DataFrame | None = None) -> pd.DataFrame | None:
    """Ham Yahoo tablosundan vadenin motor sonucu (orta vadede haftalık); veri azsa None.

    endeks: motor_girdisi'nden geçmiş XU100 (orta vadenin piyasa filtresi için gerekir).
    """
    girdi = motor_veri.motor_girdisi(df)
    if len(girdi) < motor_veri.MIN_BARS:
        return None
    return motor.hisse_analiz(girdi, VADE_AYARI[vade], endeks if vade == ORTA else None)


def hafta_tamamlandi(son_gunluk: pd.Timestamp, son_hafta: pd.Timestamp) -> bool:
    """Haftalık son bar (W-FRI etiketi) tamamlandı mı: etiket son günlük tarihten sonra değilse."""
    return pd.Timestamp(son_hafta) <= pd.Timestamp(son_gunluk)


def al_sinyalleri(sonuc: pd.DataFrame, son_bar: int) -> list[dict]:
    return motor_veri.al_sinyalleri(sonuc, son_bar, ALIM_SUTUNU)


def satis_uyarisi(sonuc: pd.DataFrame, bar: int = -1) -> dict | None:
    """Belirtilen bardaki en güçlü satış sinyali (SAT > KAR AL > ÇIK) ya da None."""
    satir = sonuc.iloc[bar]
    for sutun, ad in SATIS_TURLERI:
        if bool(satir[sutun]):
            return {"tur": sutun, "ad": ad, "skor": float(satir["Satis_skor"]), "rsi": float(satir["RSI"])}
    return None


def son_satis(sonuc: pd.DataFrame, son_bar: int) -> dict | None:
    """Son `son_bar` bardaki en yeni satış sinyali: {tur, ad, once, skor}."""
    for once in range(min(son_bar, len(sonuc))):
        uyari = satis_uyarisi(sonuc, -1 - once)
        if uyari:
            return {**uyari, "once": once}
    return None


def firsat_analizi(df: pd.DataFrame, endeks: pd.DataFrame | None = None) -> pd.DataFrame | None:
    girdi = motor_veri.motor_girdisi(df)
    if len(girdi) < motor_veri.MIN_BARS:
        return None
    return firsat.firsat_hesapla(girdi, endeks)


def firsat_durumu(fs: pd.DataFrame, ayar: firsat.FirsatAyari = firsat.VARSAYILAN) -> dict:
    """Son gün için FIRSAT durumu.

    firsat: bugün FIRSAT sinyali; bicak: bugün düşen bıçak riski listesinde; bekliyor: düşüş
    bölümü açık, dönüş bekleniyor ve bıçak kriteri yok. Ayrıca görülen kriterler, uyarılar ve
    risk seviyeleri (giriş yarın açılışta olacağı için 2R hedefi bugünkü kapanışa göre tahmindir).
    """
    son = fs.iloc[-1]
    kriterler = [k for k in firsat.BICAK_KRITERLERI if bool(son[k])]
    stop = float(son["Stop"])
    kapanis = float(son["Close"])
    return {
        "firsat": bool(son["FIRSAT"]),
        "bicak": bool(son["BICAK_RISKI"]),
        "bekliyor": bool(son["kurulum_penceresi"]) and not bool(son["tetik"]) and not kriterler,
        "kriterler": kriterler,
        "uyari_hisseye_ozel": bool(son["uyari_hisseye_ozel"]),
        "uyari_piyasa": bool(son["uyari_piyasa"]),
        "stop": stop,
        "ema_hedef": float(son["EMA_hedef"]),
        "hedef_2r": kapanis + ayar.risk_odul * (kapanis - stop),
        "rsi2": float(son["RSI2"]),
        "dusus5": float(son["Close"] / fs["Close"].iloc[-6] - 1) if len(fs) > 5 else np.nan,
    }


def islem_istatistigi(trades: pd.DataFrame) -> dict:
    """Bir hissenin tamamlanmış sinyal işlemleri: sayı, hedef/stop oranı, beklenen R, hedef günleri."""
    if trades.empty:
        return {"sinyal": 0, "hedef_gunleri": []}
    bitti = trades[trades["sonuc"].isin(("hedef", "stop", "zaman"))]
    hedef = bitti[bitti["sonuc"] == "hedef"]
    if bitti.empty:
        return {"sinyal": 0, "hedef_gunleri": []}
    return {
        "sinyal": int(len(bitti)),
        "hedef_pct": float((bitti["sonuc"] == "hedef").mean() * 100),
        "stop_pct": float((bitti["sonuc"] == "stop").mean() * 100),
        "beklenen_r": float(bitti["r"].mean()),
        "medyan_gun": float(hedef["gun"].median()) if len(hedef) else None,
        "hedef_gunleri": [int(g) for g in hedef["gun"]],
    }
