"""Sinyal kalitesi notunun arayüz metinleri (kalite.py + data/sinyal_kalitesi.json)."""

import streamlit as st

import kalite
from ui.format import fmt_num
from ui_text import KQ_GRADE, KQ_STATS, KQ_STATS_DAYS


@st.cache_data(show_spinner=False)
def _kalibrasyon(_mtime: float) -> dict:
    return kalite.yukle()


def kalibrasyon() -> dict:
    """Dosya değişince (mtime) yeniden okunur; dosya yoksa boş sözlük."""
    if not kalite.DOSYA.exists():
        return {}
    return _kalibrasyon(kalite.DOSYA.stat().st_mtime)


def ozet(skor: float | None, vade: str = "kisa", filtre: bool | None = None) -> dict:
    """{grade, label, stats}: not (doğrulanmadıysa None), 'Not A' etiketi, tarihsel istatistik cümlesi."""
    bos = {"grade": None, "label": "", "stats": None}
    if skor is None:
        return bos
    bilgi = kalite.bilgi(kalibrasyon(), vade, skor, filtre)
    if not bilgi or not bilgi.get("sinyal"):
        return bos
    gun = bilgi.get("medyan_gun")
    stats = KQ_STATS.format(
        hit=fmt_num(bilgi["hedef_pct"], 0), stop=fmt_num(bilgi["stop_pct"], 0), n=bilgi["sinyal"],
        days=KQ_STATS_DAYS.format(days=fmt_num(gun, 0)) if gun is not None else "",
    )
    grade = bilgi.get("not")
    return {"grade": grade, "label": KQ_GRADE.format(grade=grade) if grade else "", "stats": stats}
