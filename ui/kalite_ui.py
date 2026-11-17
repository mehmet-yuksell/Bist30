"""Sinyal kalitesi notunun arayüz metinleri (kalite.py + data/sinyal_kalitesi.json)."""

import streamlit as st

import kalite
from ui.components import callout
from ui.format import fmt_num
from ui_text import ALIM_UYARISI, KQ_GRADE, KQ_STATS, KQ_STATS_DAYS, SATIS_IYI


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


def iyi_satis_turleri(vade: str = "kisa") -> list[str]:
    """Geçmiş testte iki dönemde de rastgele satıştan iyi uyaran satış türlerinin adları."""
    adlar = {"SAT": "SAT", "KAR_AL": "KAR AL", "CIK": "ÇIK"}
    satis = kalibrasyon().get("satis", {}).get(vade, {})
    return [adlar[t] for t, s in satis.items()
            if s.get("gel_fark") is not None and s.get("test_fark") is not None and s["gel_fark"] > 0 and s["test_fark"] > 0]


def alim_uyarisi() -> None:
    """Alım sinyali bölümlerinin üstündeki uyarı (TEST sonucu ve iyi çalışan satış uyarıları)."""
    metin = ALIM_UYARISI
    iyi = iyi_satis_turleri()
    if iyi:
        metin += " " + SATIS_IYI.format(adlar=" ve ".join(iyi))
    callout("warn", None, metin)
