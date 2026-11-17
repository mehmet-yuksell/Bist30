"""data.py çıktısı ile tarayici_motor arasındaki köprü (arayüzden bağımsız).

- motor_girdisi: Yahoo'nun ham OHLCV tablosunu motorun beklediği biçime getirir, temettü
  düzeltmesi uygular (Adj Close / Close oranı; yfinance'in auto_adjust=True ile yaptığının
  aynısı) ve Yahoo'nun kaçırdığı ya da yanlış güne yazdığı bölünme/bedelsizleri onarır
  (bolunme_onar). Son günün fiyatı değişmez; güncel fiyat, stop ve hedef işlem gören fiyattır.
- analiz: motoru kısa vade ayarıyla çalıştırır; motorun tarama fonksiyonu gibi 120 günden
  kısa verilerde sonuç üretmez.
- son_al / al_gecmisi: AL sinyallerini panelde gösterilecek satırlara çevirir.
"""

import numpy as np
import pandas as pd

import tarayici_motor as motor

AYAR = motor.KISA_VADE
MIN_BARS = 120  # tarayici_motor.tara ile aynı alt sınır
OHLC = ["Open", "High", "Low", "Close"]

# Borsa İstanbul'da günlük fiyat limiti ±%10'dur; açılış bu bandın dışındaysa o gün bir
# kurumsal işlem (bölünme, bedelsiz/bedelli sermaye artırımı) vardır. Yukarı yönde eşik
# yüksek tutulur: 15.02.2023'te deprem sonrası 5 günlük kapanışın ardından açılışta +%22'ye
# varan gerçek boşluklar oluştu; bunlar onarılmamalıdır.
SPLIT_DOWN_CLOSE = -0.125  # kapanıştan kapanışa en az bu kadar düşüş
SPLIT_DOWN_OPEN = -0.105   # ve açılış boşluğu en az bu kadar aşağı
SPLIT_UP_OPEN = 0.25       # yukarı yönde yalnızca bundan büyük açılış boşlukları


def bolunme_onar(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Fiyat limitinin ötesindeki açılış boşluklarını kurumsal işlem sayıp geçmişi düzeltir.

    Oran açılış boşluğudur (Open_t / Close_t-1): yeni taban fiyat o günün açılışına yansır;
    tahminin hatası en fazla o geceki gerçek piyasa hareketi kadardır. Olay gününden önceki
    tüm fiyatlar oranla çarpılır, hacim bölünür (TL cinsinden işlem hacmi korunur).
    Döner: (onarılmış tablo, [{tarih, oran}]).
    """
    out = df.copy()
    events = []
    prev_close = out["Close"].shift(1)
    close_change = out["Close"] / prev_close - 1
    open_gap = out["Open"] / prev_close - 1
    is_event = ((close_change <= SPLIT_DOWN_CLOSE) & (open_gap <= SPLIT_DOWN_OPEN)) | (open_gap >= SPLIT_UP_OPEN)
    for date in out.index[is_event.fillna(False)]:
        ratio = float(1 + open_gap[date])
        before = out.index < date
        out.loc[before, OHLC] = out.loc[before, OHLC] * ratio
        out.loc[before, "Volume"] = out.loc[before, "Volume"] / ratio
        events.append({"tarih": date, "oran": ratio})
    return out, events


def motor_girdisi(df: pd.DataFrame) -> pd.DataFrame:
    """Open/High/Low/Close/Volume sütunlu, tarih indeksli, temettü ve bölünme düzeltmeli günlük tablo."""
    out = df[OHLC + ["Volume"]].astype(float).copy()
    out.columns.name = None
    if "Adj Close" in df.columns:
        factor = (df["Adj Close"] / df["Close"]).astype(float)
        factor = factor.where(np.isfinite(factor) & (factor > 0)).ffill().fillna(1.0)
        out[OHLC] = out[OHLC].mul(factor, axis=0)
    index = pd.DatetimeIndex(out.index)
    if index.tz is not None:
        index = index.tz_localize(None)
    out.index = index
    out = out[~out.index.duplicated(keep="last")].sort_index()
    out["Volume"] = out["Volume"].fillna(0.0)
    out = out.dropna(subset=OHLC)
    return bolunme_onar(out)[0]


def analiz(df: pd.DataFrame) -> pd.DataFrame | None:
    """Ham Yahoo tablosundan motor sonucu (gösterge, skor, AL/SAT sütunları); veri azsa None."""
    girdi = motor_girdisi(df)
    if len(girdi) < MIN_BARS:
        return None
    return motor.hisse_analiz(girdi, AYAR)


def skor_kirilimi(df: pd.DataFrame) -> pd.Series:
    """Son günün alım skoru kalemleri (puan); indeks motor.ALIM_KALEMLERI sırasıyla."""
    return motor.alim_skor_kalemleri(motor_girdisi(df), AYAR).iloc[-1]


def al_sinyalleri(sonuc: pd.DataFrame, son_bar: int) -> list[dict]:
    """Son `son_bar` işlem günündeki tüm AL sinyalleri, en yeni önce.

    Her biri: once (kaç işlem günü önce, 0 = son gün), tarih, skor, fiyat (sinyal kapanışı),
    stop, hedef, degisim (sinyal kapanışından son kapanışa %).
    """
    son_kapanis = float(sonuc["Close"].iloc[-1])
    pencere = sonuc.iloc[-son_bar:]
    sinyaller = []
    for tarih, satir in pencere[pencere["AL"].astype(bool)].iloc[::-1].iterrows():
        sinyaller.append({
            "once": len(sonuc) - 1 - sonuc.index.get_loc(tarih),
            "tarih": tarih,
            "skor": float(satir["Alim_skor"]),
            "fiyat": float(satir["Close"]),
            "stop": float(satir["Stop"]),
            "hedef": float(satir["Hedef"]),
            "degisim": (son_kapanis / float(satir["Close"]) - 1) * 100,
        })
    return sinyaller


def son_al(sonuc: pd.DataFrame, son_bar: int) -> dict | None:
    """Son `son_bar` işlem günündeki en yeni AL sinyali (motor.son_sinyal ile aynı seçim)."""
    sinyaller = al_sinyalleri(sonuc, son_bar)
    return sinyaller[0] if sinyaller else None


def al_gecmisi(sonuc: pd.DataFrame, horizon: int = 10) -> pd.DataFrame:
    """Tüm AL sinyalleri (en yeni üstte): skor, kapanış, stop, hedef ve `horizon` gün sonraki getiri.

    Henüz `horizon` işlem günü geçmemiş sinyallerde getiri NaN'dır.
    """
    forward = (sonuc["Close"].shift(-horizon) / sonuc["Close"] - 1) * 100
    hits = sonuc["AL"].astype(bool)
    return pd.DataFrame({
        "score": sonuc.loc[hits, "Alim_skor"],
        "close": sonuc.loc[hits, "Close"],
        "stop": sonuc.loc[hits, "Stop"],
        "target": sonuc.loc[hits, "Hedef"],
        "forward_return": forward[hits],
    }).iloc[::-1]
