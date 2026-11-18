"""Panel verisi: ham Yahoo tablosundan Bluetsman Alım 1.2 ve Satım 1.2 sinyalleri (arayüzden bağımsız).

- girdi: Yahoo'nun OHLCV tablosunu göstergelerin beklediği biçime getirir ve Yahoo'nun kaçırdığı
  ya da yanlış güne yazdığı bölünme/bedelsizleri onarır (bolunme_onar). Temettü düzeltmesi
  yapılmaz: TradingView'in varsayılan grafiği de yalnızca bölünmeye göre düzeltilmiştir, böylece
  sinyaller TradingView'de görülenle aynı fiyatlardan hesaplanır.
- Günlük vade günlük, haftalık vade haftalık (cuma kapanışlı) barlarla çalışır; iki gösterge de
  her iki vadede aynı Pine kurallarıyla hesaplanır. Haftalık son bar, haftanın son işlem günü
  kapanmadan tamamlanmış sayılmaz.
- Satış sinyalinin iki türü vardır: SAT (skor 61-100) ve KAR AL (skor 40-60).
"""

import pandas as pd

import bluetsman

KISA, ORTA = "kisa", "orta"
MIN_BARS = {KISA: 60, ORTA: 40}  # EMA 34 + ADX ısınması için en az bu kadar bar
OHLC = ["Open", "High", "Low", "Close"]
SATIS_TURLERI = (("sat", "SAT"), ("kar_al", "KAR AL"))  # öncelik sırası
SATIS_ONEKI = "s_"

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


def girdi(df: pd.DataFrame) -> pd.DataFrame:
    """Open/High/Low/Close/Volume sütunlu, tarih indeksli, bölünme onarımlı günlük tablo."""
    out = df[OHLC + ["Volume"]].astype(float).copy()
    out.columns.name = None
    index = pd.DatetimeIndex(out.index)
    if index.tz is not None:
        index = index.tz_localize(None)
    out.index = index
    out = out[~out.index.duplicated(keep="last")].sort_index()
    out["Volume"] = out["Volume"].fillna(0.0)
    out = out.dropna(subset=OHLC)
    return bolunme_onar(out)[0]


def haftalik(df: pd.DataFrame) -> pd.DataFrame:
    """Günlük OHLCV'den cuma kapanışlı haftalık barlar (TradingView'in haftalık mumu gibi)."""
    h = df.resample("W-FRI").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"})
    return h.dropna(subset=["Close"])


def analiz(df: pd.DataFrame, vade: str) -> pd.DataFrame | None:
    """Vadenin barları + Alım 1.2 sütunları + Satım 1.2 sütunları ('s_' önekli); veri azsa None."""
    bars = girdi(df)
    if vade == ORTA:
        bars = haftalik(bars)
    if len(bars) < MIN_BARS[vade]:
        return None
    return pd.concat([bars, bluetsman.compute(bars), bluetsman.compute_sell(bars).add_prefix(SATIS_ONEKI)], axis=1)


def hafta_tamamlandi(son_gunluk: pd.Timestamp, son_hafta: pd.Timestamp) -> bool:
    """Haftalık son bar (W-FRI etiketi) tamamlandı mı: etiket son günlük tarihten sonra değilse."""
    return pd.Timestamp(son_hafta) <= pd.Timestamp(son_gunluk)


def _once(sonuc: pd.DataFrame, tarih) -> int:
    return len(sonuc) - 1 - sonuc.index.get_loc(tarih)


def satis_turu(satir: pd.Series) -> tuple[str, str] | None:
    """Bir barın satış sinyali türü: ('sat', 'SAT') / ('kar_al', 'KAR AL') ya da None."""
    for tur, ad in SATIS_TURLERI:
        if bool(satir[SATIS_ONEKI + tur]):
            return tur, ad
    return None


def alim_sinyalleri(sonuc: pd.DataFrame, son_bar: int) -> list[dict]:
    """Son `son_bar` bardaki Alım 1.2 sinyalleri, en yeni önce.

    Her biri: once (kaç bar önce, 0 = son bar), tarih, skor, fiyat (sinyal kapanışı),
    degisim (sinyal kapanışından son kapanışa %).
    """
    son_kapanis = float(sonuc["Close"].iloc[-1])
    pencere = sonuc.iloc[-son_bar:]
    return [
        {"once": _once(sonuc, tarih), "tarih": tarih, "skor": float(satir["score"]),
         "fiyat": float(satir["Close"]), "degisim": (son_kapanis / float(satir["Close"]) - 1) * 100}
        for tarih, satir in pencere[pencere["buy_signal"].astype(bool)].iloc[::-1].iterrows()
    ]


def satis_sinyalleri(sonuc: pd.DataFrame, son_bar: int) -> list[dict]:
    """Son `son_bar` bardaki KAR AL / SAT sinyalleri, en yeni önce: once, tarih, tur, ad, skor, fiyat."""
    pencere = sonuc.iloc[-son_bar:]
    sinyaller = []
    for tarih, satir in pencere.iloc[::-1].iterrows():
        tur = satis_turu(satir)
        if tur:
            sinyaller.append({"once": _once(sonuc, tarih), "tarih": tarih, "tur": tur[0], "ad": tur[1],
                              "skor": float(satir[SATIS_ONEKI + "sell_score"]), "fiyat": float(satir["Close"])})
    return sinyaller


def son_alim(sonuc: pd.DataFrame, son_bar: int) -> dict | None:
    sinyaller = alim_sinyalleri(sonuc, son_bar)
    return sinyaller[0] if sinyaller else None


def son_satis(sonuc: pd.DataFrame, son_bar: int) -> dict | None:
    sinyaller = satis_sinyalleri(sonuc, son_bar)
    return sinyaller[0] if sinyaller else None


def acik_alim(sonuc: pd.DataFrame, son_bar: int) -> dict | None:
    """Son `son_bar` bardaki en yeni alım sinyali, ardından satış sinyali gelmediyse (yoksa None)."""
    alim = son_alim(sonuc, son_bar)
    satis = son_satis(sonuc, son_bar)
    if alim is None or (satis is not None and satis["once"] < alim["once"]):
        return None
    return alim


def sinyal_gecmisi(sonuc: pd.DataFrame, horizon: int = 10) -> pd.DataFrame:
    """Tüm alım ve satış sinyalleri (en yeni üstte): tur, skor, kapanış, `horizon` bar sonraki getiri %.

    Henüz `horizon` bar geçmemiş sinyallerde getiri NaN'dır. tur: 'alim', 'sat', 'kar_al'.
    """
    forward = (sonuc["Close"].shift(-horizon) / sonuc["Close"] - 1) * 100
    tur = pd.Series(None, index=sonuc.index, dtype=object)
    for t, _ in reversed(SATIS_TURLERI):
        tur[sonuc[SATIS_ONEKI + t].astype(bool)] = t
    tur[sonuc["buy_signal"].astype(bool)] = "alim"
    hits = tur.notna()
    skor = sonuc["score"].where(tur == "alim", sonuc[SATIS_ONEKI + "sell_score"])
    return pd.DataFrame({
        "tur": tur[hits], "score": skor[hits], "close": sonuc.loc[hits, "Close"], "forward_return": forward[hits],
    }).iloc[::-1]
