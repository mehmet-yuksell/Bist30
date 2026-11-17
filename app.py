"""BIST Teknik Analiz Paneli — Streamlit giriş noktası.

Sayfa düzeni burada kurulur; sekmelerin içeriği tabs/, tasarım sistemi ve ortak
bileşenler ui/ altındadır. Hesaplama modülleri (indicators, signals, backtest, data)
arayüzden bağımsızdır.
"""

import streamlit as st

import takip
from config import BIST100_TICKERS
from tabs import hisse_detay, karsilastirma, performans, tarama
from tabs import takip as takip_sekmesi
from ui import takip_deposu
from ui.components import footer, header_html
from ui.format import fmt_date
from ui.styles import inject_styles
from ui.viewport import detect_device
from ui_text import (
    APP_TITLE,
    TAB_HISSE_DETAY,
    TAB_KARSILASTIRMA,
    TAB_PERFORMANS,
    TAB_TAKIP,
    TAB_TARAMA,
    VADE_LABEL,
    VADE_OPTIONS,
)

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

# Vade seçimi tüm sekmelerde geçerlidir; anahtar sayesinde oturum boyunca korunur.
vade = st.segmented_control(
    VADE_LABEL, options=list(VADE_OPTIONS), format_func=VADE_OPTIONS.get,
    default="kisa", required=True, key="vade",
) or "kisa"

# Takip listesi tarayıcıdan (localStorage) yüklenir; BIST 100 dışı takip hisseleri, Tarama ile
# Takip Listem'in paylaştığı tek toplu indirmeye eklenir (ikisi aynı kod listesini kullanır).
takip_listesi = takip_deposu.senkronize()
toplu_kodlar = tuple(BIST100_TICKERS) + ("XU100",) + takip.ekstra_kodlar(takip_listesi, BIST100_TICKERS)

# Sekmeler, okudukları verinin son işlem gününü buraya ekler; başlıkta gösterilir.
ctx = {"last_dates": [], "vade": vade, "tickers": toplu_kodlar}

# Tarama ilk sekmedir: Bluetsman sinyali veren hisseler açılışta görünür.
tab1, tab_takip, tab2, tab3, tab4 = st.tabs([
    f":material/grid_view: {TAB_TARAMA}",
    f":material/star: {TAB_TAKIP}",
    f":material/candlestick_chart: {TAB_HISSE_DETAY}",
    f":material/compare_arrows: {TAB_KARSILASTIRMA}",
    f":material/monitoring: {TAB_PERFORMANS}",
])

with tab1:
    tarama.render(device, ctx)

with tab_takip:
    takip_sekmesi.render(device, ctx)

with tab2:
    hisse_detay.render(device, ctx)

with tab3:
    karsilastirma.render(device, ctx)

with tab4:
    performans.render(device, ctx)

if ctx["last_dates"]:
    header.html(header_html(fmt_date(max(ctx["last_dates"]))))

footer()
