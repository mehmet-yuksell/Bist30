"""Sistem Performansı sekmesi: portföy simülasyonunun sermaye eğrisi, düşüşü ve metrikleri.

Veri canlı hesaplanmaz (10 yıllık simülasyon dakikalar sürer); tools/sistem_raporu.py'nin
ürettiği data/sistem_performansi.csv ve .json dosyalarından okunur.
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

import portfoy
from ui import charts
from ui.components import callout, legend, section_title, subtitle
from ui.format import fmt_date, fmt_num, fmt_pct
from ui_text import (
    EXPLANATIONS,
    EXPANDER_LABEL,
    SP_AS_OF,
    SP_CAPTION,
    SP_COL_ANNUAL,
    SP_COL_DD_DAYS,
    SP_COL_MAXDD,
    SP_COL_PORTFOLIO,
    SP_COL_RATIO,
    SP_COL_SHARPE,
    SP_COL_SORTINO,
    SP_COL_TOTAL,
    SP_COL_TRADES,
    SP_COL_VOL,
    SP_DRAWDOWN_TITLE,
    SP_EQUITY_TITLE,
    SP_METRICS_TITLE,
    SP_MISSING,
    SP_NOTES,
    SP_NOTES_TITLE,
    SP_PERIOD_LABEL,
    SP_PERIODS,
    SP_TITLE,
)

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "sistem_performansi.csv"
JSON_PATH = ROOT / "data" / "sistem_performansi.json"
EXPANDER_ICON = ":material/help_outline:"


@st.cache_data(show_spinner=False)
def _yukle(_csv_mtime: float, _json_mtime: float) -> tuple[pd.DataFrame, dict]:
    """Dosyalar değişince (mtime) yeniden okunur."""
    seriler = pd.read_csv(CSV_PATH, parse_dates=["tarih"])
    meta = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    return seriler, meta


def _yuzde(value, signed: bool = True) -> str:
    return "—" if value is None else fmt_pct(value * 100, 1, signed=signed)


def _metrik_tablosu(meta: dict, donem: str, sira: list[str]) -> pd.DataFrame:
    satirlar = []
    for ad in sira:
        m = meta["metrikler"][donem][ad]
        satirlar.append({
            SP_COL_PORTFOLIO: ad,
            SP_COL_TRADES: str(m["islem"]) if m.get("islem") is not None else "—",
            SP_COL_TOTAL: _yuzde(m.get("toplam_getiri")),
            SP_COL_ANNUAL: _yuzde(m.get("yillik_getiri")),
            SP_COL_VOL: _yuzde(m.get("yillik_oynaklik"), signed=False),
            SP_COL_SHARPE: fmt_num(m.get("sharpe"), 2),
            SP_COL_SORTINO: fmt_num(m.get("sortino"), 2),
            SP_COL_MAXDD: _yuzde(m.get("max_dusus")),
            SP_COL_DD_DAYS: str(int(m["max_dusus_suresi"])) if m.get("max_dusus_suresi") is not None else "—",
            SP_COL_RATIO: fmt_num(m.get("getiri_dusus_orani"), 2),
        })
    return pd.DataFrame(satirlar)


def render(device: str, ctx: dict) -> None:
    section_title(SP_TITLE, SP_CAPTION)
    if not (CSV_PATH.exists() and JSON_PATH.exists()):
        callout("info", None, SP_MISSING)
        return
    seriler, meta = _yukle(CSV_PATH.stat().st_mtime, JSON_PATH.stat().st_mtime)

    donem = st.segmented_control(
        SP_PERIOD_LABEL, options=list(SP_PERIODS), format_func=SP_PERIODS.get, default="TEST", key="sp_donem",
    ) or "TEST"
    sira = meta["kombinasyonlar"] + meta["kiyaslar"]
    stiller = charts.performans_renkleri(meta["kombinasyonlar"], meta["kiyaslar"])
    secili = seriler[seriler["donem"] == donem]
    sermaye = {ad: secili[secili["seri"] == ad].set_index("tarih")["sermaye"] for ad in sira}
    sermaye = {ad: s for ad, s in sermaye.items() if not s.empty}

    legend([(ad, stiller[ad][0], "line") for ad in sermaye])
    subtitle(SP_EQUITY_TITLE)
    charts.show_chart(charts.build_performance_figure(sermaye, stiller, device), device, key="sp_equity")
    subtitle(SP_DRAWDOWN_TITLE)
    dusus = {ad: portfoy.dusus_serisi(s) for ad, s in sermaye.items()}
    charts.show_chart(charts.build_performance_figure(dusus, stiller, device, percent=True), device, key="sp_dd")

    section_title(SP_METRICS_TITLE)
    st.dataframe(_metrik_tablosu(meta, donem, list(sermaye)), hide_index=True, width="stretch")
    st.caption(SP_AS_OF.format(data=fmt_date(pd.Timestamp(meta["veri_sonu"])),
                               computed=fmt_date(pd.Timestamp(meta["olusturma"]))))
    callout("warn", SP_NOTES_TITLE, SP_NOTES)
    with st.expander(EXPANDER_LABEL, icon=EXPANDER_ICON):
        st.write(EXPLANATIONS["portfolio"])
