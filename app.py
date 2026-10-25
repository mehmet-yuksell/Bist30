"""BIST Teknik Analiz Paneli — Streamlit giriş noktası.

Sayfa düzeni burada kurulur; sekmelerin içeriği tabs/, tasarım sistemi ve ortak
bileşenler ui/ altındadır. Hesaplama modülleri (indicators, signals, backtest, data)
arayüzden bağımsızdır.
"""

import streamlit as st

from tabs import hisse_detay, karsilastirma, tarama
from ui.components import footer, header_html
from ui.format import fmt_date
from ui.styles import inject_styles
from ui.viewport import detect_device
from ui_text import APP_TITLE, TAB_HISSE_DETAY, TAB_KARSILASTIRMA, TAB_TARAMA

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=":material/candlestick_chart:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_styles()
device = detect_device()

header = st.empty()
header.html(header_html())

# Sekmeler, okudukları verinin son işlem gününü buraya ekler; başlıkta gösterilir.
ctx = {"last_dates": []}

tab1, tab2, tab3 = st.tabs([
    f":material/candlestick_chart: {TAB_HISSE_DETAY}",
    f":material/grid_view: {TAB_TARAMA}",
    f":material/compare_arrows: {TAB_KARSILASTIRMA}",
])

with tab1:
    hisse_detay.render(device, ctx)

with tab2:
    tarama.render(device, ctx)

with tab3:
    karsilastirma.render(device, ctx)

if ctx["last_dates"]:
    header.html(header_html(fmt_date(max(ctx["last_dates"]))))

footer()
