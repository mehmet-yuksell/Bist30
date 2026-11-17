"""İleri Test sekmesi: Sinyal Günlüğü'ndeki sinyallerin gerçek zamanlı sonucu (Aşama 1 kurallarıyla).

Günlük (data/sinyal_gunlugu.csv) her iş günü GitHub Actions ile güncellenir. Fiyat verisi Tarama ile
aynı toplu indirmeden gelir; değerlendirme gunluk.degerlendir (evaluation.py) ile yapılır.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

import feed
import gunluk
from data import DataFetchError
from ui.components import callout, error_state, section_title, skeleton_html
from ui.format import fmt_date, fmt_num
from ui_text import (
    IT_CAPTION,
    IT_COL_CODE,
    IT_COL_COUNT,
    IT_COL_DATE,
    IT_COL_DAYS,
    IT_COL_EXP,
    IT_COL_GRADE,
    IT_COL_HIT,
    IT_COL_HORIZON,
    IT_COL_MEDIAN,
    IT_COL_OPEN,
    IT_COL_R,
    IT_COL_REF,
    IT_COL_RESULT,
    IT_COL_SCORE,
    IT_COL_STOP,
    IT_COL_STOPPCT,
    IT_COL_TARGET,
    IT_COL_TYPE,
    IT_EMPTY,
    IT_LOG_TITLE,
    IT_NOT_ENOUGH,
    IT_NOT_ENOUGH_TITLE,
    IT_RESULTS,
    IT_SINCE,
    IT_SUMMARY_TITLE,
    IT_TITLE,
    IT_TYPES,
    TK_VADE_SHORT,
    VADE_BIRIM,
)

DOSYA = Path(__file__).resolve().parent.parent / "data" / "sinyal_gunlugu.csv"
BOS = "—"


@st.cache_data(show_spinner=False)
def _gunluk(_mtime: float) -> pd.DataFrame:
    return gunluk.oku(DOSYA)


@st.cache_data(max_entries=4, show_spinner=False)
def _sonuclar(gunluk_mtime: float, data_key: str, _log: pd.DataFrame, _histories: dict) -> pd.DataFrame:
    """Günlük ya da veri değişince yeniden değerlendirilir."""
    return gunluk.degerlendir(_log, _histories, _histories.get("XU100"))


def _ozet_tablosu(islemler: pd.DataFrame) -> pd.DataFrame:
    satirlar = []
    for _, s in gunluk.ozetle(islemler).iterrows():
        medyan = s.get("hedef_medyan_gun")
        satirlar.append({
            IT_COL_HORIZON: TK_VADE_SHORT.get(s["vade"], s["vade"]),
            IT_COL_TYPE: IT_TYPES.get(s["tur"], s["tur"]),
            IT_COL_COUNT: int(s["sinyal"]),
            IT_COL_OPEN: int(s.get("acik", 0)),
            IT_COL_HIT: fmt_num(s.get("hedef_pct"), 1),
            IT_COL_STOPPCT: fmt_num(s.get("stop_pct"), 1),
            IT_COL_EXP: fmt_num(s.get("beklenen_r"), 3),
            IT_COL_MEDIAN: f"{fmt_num(medyan, 0)} {VADE_BIRIM[s['vade']]}" if pd.notna(medyan) else BOS,
        })
    return pd.DataFrame(satirlar)


def _gunluk_tablosu(log: pd.DataFrame, islemler: pd.DataFrame) -> pd.DataFrame:
    sonuc = {}
    if not islemler.empty:
        for _, t in islemler.iterrows():
            sonuc[(t["tarih"].date().isoformat(), t["vade"], t["tur"], t["kod"])] = t
    satirlar = []
    for _, r in log.sort_values(["tarih", "kod"], ascending=[False, True]).iterrows():
        t = sonuc.get((r["tarih"], r["vade"], r["tur"], r["kod"]))
        satirlar.append({
            IT_COL_DATE: fmt_date(pd.Timestamp(r["tarih"])),
            IT_COL_HORIZON: TK_VADE_SHORT.get(r["vade"], r["vade"]),
            IT_COL_TYPE: IT_TYPES.get(r["tur"], r["tur"]),
            IT_COL_CODE: r["kod"],
            IT_COL_SCORE: fmt_num(r["skor"], 0) if pd.notna(r["skor"]) else BOS,
            IT_COL_GRADE: r["not"] or BOS,
            IT_COL_REF: fmt_num(r["giris_referans"], 2),
            IT_COL_STOP: fmt_num(t["stop"] if t is not None else r["stop"], 2),
            IT_COL_TARGET: fmt_num(t["hedef"] if t is not None else r["hedef"], 2),
            IT_COL_RESULT: IT_RESULTS.get(t["sonuc"], t["sonuc"]) if t is not None else BOS,
            IT_COL_DAYS: fmt_num(t["gun"], 0) if t is not None and pd.notna(t.get("gun")) else BOS,
            IT_COL_R: fmt_num(t["r"], 2) if t is not None and pd.notna(t.get("r")) else BOS,
        })
    return pd.DataFrame(satirlar)


def render(device: str, ctx: dict) -> None:
    section_title(IT_TITLE, IT_CAPTION)
    if not DOSYA.exists():
        callout("empty", None, IT_EMPTY)
        return
    log = _gunluk(DOSYA.stat().st_mtime)
    if log.empty:
        callout("empty", None, IT_EMPTY)
        return

    loading = st.empty()
    loading.html(skeleton_html("list"))
    try:
        data = feed.batch(ctx["tickers"])  # Tarama ile aynı toplu indirme
    except DataFetchError as exc:
        loading.empty()
        error_state(str(exc), key="it_retry")
        return
    islemler = _sonuclar(DOSYA.stat().st_mtime, data.fetched_at.isoformat(), log, data.data)
    loading.empty()

    tamam = gunluk.tamamlanan(islemler)
    st.caption(IT_SINCE.format(ilk=fmt_date(pd.Timestamp(log["tarih"].min())),
                               son=fmt_date(pd.Timestamp(log["tarih"].max())), n=len(log), m=tamam))
    if not gunluk.yeterli_mi(islemler):
        callout("info", IT_NOT_ENOUGH_TITLE, IT_NOT_ENOUGH.format(min=gunluk.MIN_SINYAL, m=tamam))
    else:
        section_title(IT_SUMMARY_TITLE)
        st.dataframe(_ozet_tablosu(islemler), hide_index=True, width="stretch")

    section_title(IT_LOG_TITLE)
    st.dataframe(_gunluk_tablosu(log, islemler), hide_index=True, width="stretch")
