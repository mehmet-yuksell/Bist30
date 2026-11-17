"""BIST 100 Tarama sekmesi: alım sinyalleri, satış uyarıları, fırsat düşüşleri, düşen bıçak riski
ve iki vadenin skorlarıyla tablo / liste.

Sinyal ve skor tarayici_motor'dan (Bluetsman Alım/Sat v2) gelir: kısa vade günlük, orta vade
haftalık barlarla. Fırsat ve düşen bıçak (firsat.py) yalnızca günlüktür. Veri feed.batch ile
piyasa saatine göre güncel tutulur (XU100 aynı toplu indirmede); sekme seans boyunca 15 dakikada
bir kendini yeniler. Vade seçimi sayfanın üstündedir (app.py) ve tüm sekmelerde geçerlidir.
"""

from datetime import timedelta

import pandas as pd
import streamlit as st

import feed
import firsat
import market
import panel_veri as pv
from config import BIST100_TICKERS
from data import DataFetchError
from ui import kalite_ui
from ui import theme as t
from ui.components import (
    callout,
    error_state,
    metric_html,
    recent_signal_list,
    section_title,
    signal_cards,
    skeleton_html,
    stat_strip,
    status_bar,
    stock_list,
    tagged_list,
)
from ui.format import arrow, direction, fmt_date, fmt_num, fmt_pct
from ui.viewport import MOBILE
from ui_text import (
    BK_CAPTION,
    BK_HONEST,
    BK_NONE,
    BK_TITLE,
    FR_2R_TARGET,
    FR_CAPTION,
    FR_EMA_TARGET,
    FR_HONEST,
    FR_NONE,
    FR_RSI2,
    FR_TITLE,
    FR_WAITING_ROW,
    FR_WAITING_TITLE,
    FR_WARN_MARKET,
    FR_WARN_STOCK,
    KQ_CAPTION,
    LIVE_CLOSED,
    LIVE_LAST_DATA,
    LIVE_MARKET,
    LIVE_OPEN,
    LIVE_REFRESH,
    LIVE_REFRESH_WAIT,
    LIVE_SESSION_NOTE,
    LIVE_SETTLING_NOTE,
    LIVE_STALE,
    LIVE_UPDATED,
    SL_CAPTION,
    SL_NONE,
    SL_NONE_ORTA,
    SL_SCORE,
    SL_STATS,
    SL_TITLE,
    SL_VERDICT_BAD,
    SL_VERDICT_GOOD,
    TR_AS_OF,
    TR_COL_CHANGE,
    TR_COL_COMPANY,
    TR_COL_GRADE,
    TR_COL_PRICE,
    TR_COL_RSI,
    TR_COL_SCORE_K,
    TR_COL_SCORE_O,
    TR_COL_SIGNAL_K,
    TR_COL_SIGNAL_O,
    TR_COL_TICKER,
    TR_COL_VOLUME,
    TR_FALLING,
    TR_FILTER_ALL,
    TR_FILTER_LABEL,
    TR_FILTER_SIGNAL,
    TR_FILTER_SIGNAL_ORTA,
    TR_LIST_CAPTION,
    TR_LIST_META_VADE,
    TR_LIST_TITLE,
    TR_MISSING,
    TR_NO_DATA,
    TR_NO_RESULTS,
    TR_NO_SIGNALS,
    TR_RISING,
    TR_SEARCH_LABEL,
    TR_SEARCH_PLACEHOLDER,
    TR_SIGNAL_RECENT,
    TR_SIGNAL_RECENT_ORTA,
    TR_SIGNAL_TODAY,
    TR_SIGNAL_TODAY_SUB,
    TR_SORT_LABEL,
    TR_SORT_OPTIONS,
    TR_STRIP_FLAT,
    TR_STRIP_OF,
    TS_CAPTION,
    TS_CAPTION_ORTA,
    TS_NONE,
    TS_NONE_ORTA,
    TS_PROVISIONAL_BADGE,
    TS_PROVISIONAL_TITLE,
    TS_RECENT_NONE,
    TS_RECENT_NONE_ORTA,
    TS_RECENT_TITLE,
    TS_RECENT_TITLE_ORTA,
    TS_RSI,
    TS_SIGNAL_PRICE,
    TS_SINCE,
    TS_STOP,
    TS_TARGET,
    TS_TITLE,
    TS_VOLUME,
    TS_VOLUME_VALUE,
    VADE_BUGUN,
    VADE_ONCE,
    VADE_WEEK_NOTE,
)

ENDEKS = "XU100"      # toplu indirmeye eklenir; orta vade filtresi ve fırsat uyarıları için
SIGNAL_LOOKBACK = 10  # tablo ve "son 10 gün/hafta" için
RECENT_BARS = 5       # bugün sinyal yoksa gösterilen geçmiş
NO_SIGNAL = "—"
SKOR_SUTUNU = {pv.KISA: TR_COL_SCORE_K, pv.ORTA: TR_COL_SCORE_O}
SINYAL_SUTUNU = {pv.KISA: TR_COL_SIGNAL_K, pv.ORTA: TR_COL_SIGNAL_O}
SELL_COLOR = t.DOWN_TEXT


def _signal_text(once: int | None, vade: str) -> str:
    if once is None:
        return NO_SIGNAL
    return VADE_BUGUN[vade] if once == 0 else VADE_ONCE[vade].format(days=once)


def _vade_ozeti(ticker: str, name: str, sonuc: pd.DataFrame | None, vade: str, price: float, change: float):
    """Bir vadenin tablo sütunları, bugünkü/son alım sinyalleri ve son bar satış uyarısı."""
    if sonuc is None:
        return {"skor": None, "once": None, "sinyal_skor": None}, [], [], None
    last = sonuc.iloc[-1]
    sinyaller = pv.al_sinyalleri(sonuc, SIGNAL_LOOKBACK)
    bugun, yakin = [], []
    for s in sinyaller:
        if s["once"] == 0:
            bugun.append({"ticker": ticker, "name": name, "score": s["skor"], "price": price, "change": change,
                          "stop": s["stop"], "target": s["hedef"], "rsi": float(last["RSI"]),
                          "volume_ratio": float(last["Hacim_kat"])})
        elif s["once"] <= RECENT_BARS:
            yakin.append({"ticker": ticker, "name": name, **s})
    uyari = pv.satis_uyarisi(sonuc)
    satis = {"ticker": ticker, "name": name, "price": price, "change": change, **uyari} if uyari else None
    ozet = {"skor": float(last["Alim_skor"]), "once": sinyaller[0]["once"] if sinyaller else None,
            "sinyal_skor": sinyaller[0]["skor"] if sinyaller else None}
    return ozet, bugun, yakin, satis


@st.cache_data(max_entries=3, show_spinner=False)
def _scan(data_key: str, _histories: dict) -> dict:
    """Her hisse için iki vadenin motorunu ve FIRSAT'ı çalıştırır; yalnızca ekran özetlerini döndürür.

    data_key verinin çekildiği an olduğundan aynı veri için hesap bir kez yapılır
    (`_histories` önbellek anahtarına katılmaz).
    """
    endeks = pv.endeks_girdisi(_histories.get(ENDEKS))
    rows = []
    alim = {v: {"today": [], "recent": []} for v in (pv.KISA, pv.ORTA)}
    satis = {pv.KISA: [], pv.ORTA: []}
    firsatlar, bekleyenler, bicaklar = [], [], []
    last_date, last_week = None, None
    for ticker, name in BIST100_TICKERS.items():
        df = _histories.get(ticker)
        if df is None or len(df) < 2:
            continue
        close = df["Close"]
        price = float(close.iloc[-1])
        change = float((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100)
        last_date = max(last_date, df.index[-1]) if last_date is not None else df.index[-1]

        row = {TR_COL_TICKER: ticker, TR_COL_COMPANY: name, TR_COL_PRICE: round(price, 2),
               TR_COL_CHANGE: round(change, 2)}
        kisa = pv.analiz(df, pv.KISA)
        orta = pv.analiz(df, pv.ORTA, endeks) if endeks is not None else None
        if orta is not None:
            last_week = max(last_week, orta.index[-1]) if last_week is not None else orta.index[-1]
        for vade, sonuc in ((pv.KISA, kisa), (pv.ORTA, orta)):
            ozet, bugun, yakin, uyari = _vade_ozeti(ticker, name, sonuc, vade, price, change)
            row[SKOR_SUTUNU[vade]] = round(ozet["skor"]) if ozet["skor"] is not None else None
            row[SINYAL_SUTUNU[vade]] = _signal_text(ozet["once"], vade)
            row[f"_once_{vade}"] = ozet["once"]
            row[f"_sinyal_skor_{vade}"] = ozet["sinyal_skor"]
            alim[vade]["today"] += bugun
            alim[vade]["recent"] += yakin
            if uyari:
                satis[vade].append(uyari)
        row[TR_COL_RSI] = round(float(kisa["RSI"].iloc[-1]), 1) if kisa is not None else None
        row[TR_COL_VOLUME] = round(float(kisa["Hacim_kat"].iloc[-1]), 2) if kisa is not None else None
        rows.append(row)

        fs = pv.firsat_analizi(df, endeks)
        if fs is not None:
            d = pv.firsat_durumu(fs)
            temel = {"ticker": ticker, "name": name, "price": price, "change": change, **d}
            if d["firsat"]:
                firsatlar.append(temel)
            elif d["bekliyor"]:
                bekleyenler.append(temel)
            if d["bicak"]:
                bicaklar.append(temel)

    for vade in alim:
        alim[vade]["today"].sort(key=lambda s: s["score"], reverse=True)
        alim[vade]["recent"].sort(key=lambda s: (s["once"], -s["skor"]))
        satis[vade].sort(key=lambda s: ([a for a, _ in pv.SATIS_TURLERI].index(s["tur"]), -s["skor"]))
    return {"rows": pd.DataFrame(rows), "alim": alim, "satis": satis, "firsat": firsatlar,
            "bekleyen": sorted(bekleyenler, key=lambda s: s["rsi2"]), "bicak": bicaklar,
            "last_date": last_date, "last_week": last_week}


# ---------------------------------------------------------------------------
# Durum satırı
# ---------------------------------------------------------------------------

def _render_status(data: feed.Feed, last_date, is_open: bool) -> None:
    with st.container(horizontal=True, vertical_alignment="center", gap="small", key="ts_status"):
        status_bar([
            (LIVE_LAST_DATA, fmt_date(last_date), None),
            (LIVE_UPDATED, data.fetched_at.strftime("%H:%M"), None),
            (LIVE_MARKET, LIVE_OPEN if is_open else LIVE_CLOSED, "up" if is_open else "down"),
        ])
        if st.button(LIVE_REFRESH, icon=":material/refresh:", key="ts_refresh", width="content"):
            wait = feed.request_refresh()
            if wait:
                st.toast(LIVE_REFRESH_WAIT.format(seconds=wait))
            else:
                st.rerun()  # tüm sayfa: Hisse Detay da yeni veriyle çizilsin
    if data.stale:
        callout("warn", None, LIVE_STALE.format(minutes=data.age_minutes()))


# ---------------------------------------------------------------------------
# Bölümler
# ---------------------------------------------------------------------------

def _render_alim(scan: dict, vade: str, provisional: bool) -> None:
    section_title(TS_TITLE, TS_CAPTION if vade == pv.KISA else TS_CAPTION_ORTA)
    kalite_ui.alim_uyarisi()
    today = scan["alim"][vade]["today"]
    filtre = True if vade == pv.ORTA else None  # orta vadede listedekiler filtreden geçmiş sinyallerdir
    if today:
        if provisional:
            st.caption(TS_PROVISIONAL_TITLE)
        kartlar = []
        for s in today:
            kq = kalite_ui.ozet(s["score"], vade, filtre)
            kartlar.append({
                "ticker": s["ticker"], "name": s["name"], "score": s["score"],
                "price": fmt_num(s["price"], 2), "change": s["change"],
                "badge": TS_PROVISIONAL_BADGE if provisional else None,
                "grade": kq["grade"], "grade_label": kq["label"], "stats": kq["stats"],
                "rows": [
                    (TS_STOP, fmt_num(s["stop"], 2)),
                    (TS_TARGET, fmt_num(s["target"], 2)),
                    (TS_RSI, fmt_num(s["rsi"], 1)),
                    (TS_VOLUME, TS_VOLUME_VALUE.format(ratio=fmt_num(s["volume_ratio"], 2))),
                ],
            })
        signal_cards(kartlar)
        if any(k["grade"] for k in kartlar):
            st.caption(KQ_CAPTION)
    else:
        callout("empty", TS_NONE if vade == pv.KISA else TS_NONE_ORTA, None)

    # Bugün sinyal yoksa ya da bugünküler henüz ön sinyalse, kesinleşmiş son barları da göster.
    if not today or provisional:
        st.caption(TS_RECENT_TITLE if vade == pv.KISA else TS_RECENT_TITLE_ORTA)
        recent = scan["alim"][vade]["recent"]
        if recent:
            satirlar = []
            for s in recent:
                kq = kalite_ui.ozet(s["skor"], vade, filtre)
                satirlar.append({
                    "ticker": s["ticker"], "name": s["name"],
                    "when": VADE_ONCE[vade].format(days=s["once"]),
                    "price_label": f"{TS_SIGNAL_PRICE} {fmt_num(s['fiyat'], 2)} · skor {s['skor']:.0f}",
                    "change": s["degisim"], "since_label": TS_SINCE,
                    "grade": kq["grade"], "grade_label": kq["label"],
                })
            recent_signal_list(satirlar)
        else:
            callout("empty", None, TS_RECENT_NONE if vade == pv.KISA else TS_RECENT_NONE_ORTA)


def _render_satis(scan: dict, vade: str, provisional: bool) -> None:
    section_title(SL_TITLE, SL_CAPTION)
    uyarilar = scan["satis"][vade]
    istatistik = kalite_ui.kalibrasyon().get("satis", {}).get(vade, {})
    if not uyarilar:
        callout("empty", SL_NONE if vade == pv.KISA else SL_NONE_ORTA, None)
    else:
        kartlar = []
        for s in uyarilar:
            st_ = istatistik.get(s["tur"], {})
            stats = (SL_STATS.format(hit=fmt_num(st_["hedef_pct"], 0), stop=fmt_num(st_["stop_pct"], 0), n=st_["sinyal"])
                     if st_.get("sinyal") else None)
            kartlar.append({
                "ticker": s["ticker"], "name": s["name"], "score": s["skor"], "color": SELL_COLOR,
                "price": fmt_num(s["price"], 2), "change": s["change"],
                "badge": f"{s['ad']} · {TS_PROVISIONAL_BADGE}" if provisional else s["ad"], "badge_tone": "down",
                "stats": stats,
                "rows": [(SL_SCORE, fmt_num(s["skor"], 0)), (TS_RSI, fmt_num(s["rsi"], 1))],
            })
        signal_cards(kartlar)
    # Her tür için geçmiş testin hükmü (iki dönemde de rastgeleden iyi mi)
    hukum = []
    for tur, ad in pv.SATIS_TURLERI:
        st_ = istatistik.get(tur)
        if st_ and st_.get("gel_fark") is not None and st_.get("test_fark") is not None:
            iyi = st_["gel_fark"] > 0 and st_["test_fark"] > 0
            hukum.append((SL_VERDICT_GOOD if iyi else SL_VERDICT_BAD).format(ad=ad))
    if hukum:
        st.caption(" ".join(hukum))


def _render_firsat(scan: dict) -> None:
    section_title(FR_TITLE, FR_CAPTION)
    if scan["firsat"]:
        kartlar = []
        for s in scan["firsat"]:
            uyarilar = [w for w, var in ((FR_WARN_STOCK, s["uyari_hisseye_ozel"]), (FR_WARN_MARKET, s["uyari_piyasa"])) if var]
            kartlar.append({
                "ticker": s["ticker"], "name": s["name"], "score": 100 - s["rsi2"], "score_text": "⚡",
                "color": t.ACCENT_TEXT, "price": fmt_num(s["price"], 2), "change": s["change"],
                "badge": "FIRSAT", "badge_tone": "accent",
                "stats": " · ".join(uyarilar) if uyarilar else None,
                "rows": [(TS_STOP, fmt_num(s["stop"], 2)), (FR_EMA_TARGET, fmt_num(s["ema_hedef"], 2)),
                         (FR_2R_TARGET, fmt_num(s["hedef_2r"], 2)), (FR_RSI2, fmt_num(s["rsi2"], 1))],
            })
        signal_cards(kartlar)
    else:
        callout("empty", FR_NONE, None)
    if scan["bekleyen"]:
        st.caption(FR_WAITING_TITLE)
        tagged_list([
            {"ticker": s["ticker"], "name": s["name"], "change": s["change"],
             "tags": [(w, "warn") for w, var in (("KAP?", s["uyari_hisseye_ozel"]), ("Piyasa", s["uyari_piyasa"])) if var],
             "meta": FR_WAITING_ROW.format(drop=fmt_pct(s["dusus5"] * 100, 1), rsi=fmt_num(s["rsi2"], 1))}
            for s in scan["bekleyen"]
        ])
    fr = kalite_ui.kalibrasyon().get("firsat", {})
    if fr.get("test_r") is not None:
        st.caption(FR_HONEST.format(r=fmt_num(fr["test_r"], 2), rr=fmt_num(fr["test_rastgele_r"], 2),
                                    hit=fmt_num(fr["hedef_pct"], 0)))


def _render_bicak(scan: dict) -> None:
    section_title(BK_TITLE, BK_CAPTION)
    if scan["bicak"]:
        tagged_list([
            {"ticker": s["ticker"], "name": s["name"], "change": s["change"],
             "tags": [(k, "warn") for k in s["kriterler"]],
             "meta": " · ".join(firsat.BICAK_KRITERLERI[k] for k in s["kriterler"])}
            for s in scan["bicak"]
        ])
    else:
        callout("empty", BK_NONE, None)
    if not kalite_ui.kalibrasyon().get("bicak", {}).get("ayiriyor", True):
        st.caption(BK_HONEST)


# ---------------------------------------------------------------------------
# Özet ve liste
# ---------------------------------------------------------------------------

def _render_summary(table_df: pd.DataFrame, vade: str, provisional: bool) -> None:
    changes = table_df[TR_COL_CHANGE]
    rising = int((changes.round(2) > 0).sum())
    falling = int((changes.round(2) < 0).sum())
    flat = len(changes) - rising - falling
    once = table_df[f"_once_{vade}"]
    today_count = int((once == 0).sum())
    recent_count = int(once.notna().sum())
    recent_label = (TR_SIGNAL_RECENT if vade == pv.KISA else TR_SIGNAL_RECENT_ORTA).format(days=SIGNAL_LOOKBACK)

    cards = [
        metric_html(TR_RISING, f"▲ {rising}", sub=TR_STRIP_OF.format(count=len(changes)), value_class="ui-up"),
        metric_html(TR_FALLING, f"▼ {falling}", sub=TR_STRIP_FLAT.format(count=flat), value_class="ui-down"),
        metric_html(TR_SIGNAL_TODAY, str(today_count), sub=TR_SIGNAL_TODAY_SUB if provisional else None,
                    value_class="ui-accent" if today_count else ""),
        metric_html(recent_label, str(recent_count), value_class="ui-accent" if recent_count else ""),
    ]
    stat_strip(cards, breadth=(rising, flat, falling))


def _style_table(df: pd.DataFrame):
    def change_color(value):
        tone = direction(value)
        color = {"up": t.UP, "down": t.DOWN_TEXT}.get(tone, t.TEXT_2)
        return f"color: {color}; font-weight: 600"

    def signal_color(value):
        return f"color: {t.TEXT_3}" if value == NO_SIGNAL else f"color: {t.ACCENT_TEXT}; font-weight: 600"

    return (
        df.style
        .format({
            TR_COL_PRICE: lambda v: fmt_num(v, 2),
            TR_COL_CHANGE: lambda v: f"{arrow(v)} {fmt_pct(v)}",
            TR_COL_RSI: lambda v: fmt_num(v, 1),
            TR_COL_VOLUME: lambda v: fmt_num(v, 2),
        })
        .map(change_color, subset=[TR_COL_CHANGE])
        .map(signal_color, subset=[TR_COL_SIGNAL_K, TR_COL_SIGNAL_O])
    )


def _render_filters(device: str, vade: str) -> tuple[bool, str, str]:
    mobile = device == MOBILE
    signal_option = (TR_FILTER_SIGNAL if vade == pv.KISA else TR_FILTER_SIGNAL_ORTA).format(days=SIGNAL_LOOKBACK)
    with st.container(horizontal=True, vertical_alignment="bottom", gap="small", key="tr_filters", wrap=True):
        show = st.segmented_control(
            TR_FILTER_LABEL, options=[TR_FILTER_ALL, signal_option], default=TR_FILTER_ALL, key=f"tr_show_{vade}",
        ) or TR_FILTER_ALL
        search = st.text_input(
            TR_SEARCH_LABEL, "", placeholder=TR_SEARCH_PLACEHOLDER, key="tr_search",
            width="stretch" if mobile else 260,
        )
        # Tabloda sütun başlığına tıklanarak sıralanır; listede bunun yerine seçim kutusu var.
        sort_key = "score_desc"
        if mobile:
            sort_key = st.selectbox(
                TR_SORT_LABEL, options=list(TR_SORT_OPTIONS), format_func=TR_SORT_OPTIONS.get,
                key="tr_sort", width="stretch",
            )
    return show == signal_option, search, sort_key


def _render_results(table_df: pd.DataFrame, device: str, vade: str) -> None:
    only_signals, search, sort_key = _render_filters(device, vade)

    filtered = table_df
    if only_signals:
        filtered = filtered[filtered[f"_once_{vade}"].notna()]
        if filtered.empty:
            callout("empty", None, TR_NO_SIGNALS.format(days=SIGNAL_LOOKBACK))
            return
    if search:
        query = search.strip()
        mask = filtered[TR_COL_TICKER].str.contains(query, case=False, regex=False) | filtered[
            TR_COL_COMPANY
        ].str.contains(query, case=False, regex=False)
        filtered = filtered[mask]

    if filtered.empty:
        callout("empty", None, TR_NO_RESULTS)
        return

    sorters = {
        "score_desc": (SKOR_SUTUNU[vade], False),
        "change_desc": (TR_COL_CHANGE, False),
        "change_asc": (TR_COL_CHANGE, True),
        "ticker": (TR_COL_TICKER, True),
    }
    column, ascending = sorters[sort_key]
    ordered = filtered.sort_values(column, ascending=ascending, na_position="last")

    if device == MOBILE:
        def skor(v):
            return NO_SIGNAL if pd.isna(v) else str(int(v))

        stock_list([
            {
                "ticker": row[TR_COL_TICKER],
                "name": row[TR_COL_COMPANY],
                "price": fmt_num(row[TR_COL_PRICE], 2),
                "change": row[TR_COL_CHANGE],
                "meta": TR_LIST_META_VADE.format(k=skor(row[TR_COL_SCORE_K]), o=skor(row[TR_COL_SCORE_O]),
                                                 rsi=fmt_num(row[TR_COL_RSI], 1)),
                "signal": None if row[SINYAL_SUTUNU[vade]] == NO_SIGNAL else " · ".join(
                    x for x in (row[SINYAL_SUTUNU[vade]],
                                row[TR_COL_GRADE] if vade == pv.KISA and row[TR_COL_GRADE] != NO_SIGNAL else "") if x),
            }
            for _, row in ordered.iterrows()
        ])
        return

    columns = [
        TR_COL_TICKER, TR_COL_COMPANY, TR_COL_PRICE, TR_COL_CHANGE,
        TR_COL_SCORE_K, TR_COL_SIGNAL_K, TR_COL_GRADE, TR_COL_SCORE_O, TR_COL_SIGNAL_O, TR_COL_RSI, TR_COL_VOLUME,
    ]
    progress = {"min_value": 0, "max_value": 100, "format": "%d", "width": "small"}
    st.dataframe(
        _style_table(ordered[columns]),
        width="stretch",
        height=min(36 * (len(ordered) + 1) + 4, 640),
        hide_index=True,
        column_config={
            TR_COL_TICKER: st.column_config.TextColumn(TR_COL_TICKER, width="small"),
            TR_COL_PRICE: st.column_config.NumberColumn(TR_COL_PRICE),
            TR_COL_CHANGE: st.column_config.NumberColumn(TR_COL_CHANGE),
            TR_COL_SCORE_K: st.column_config.ProgressColumn(TR_COL_SCORE_K, **progress),
            TR_COL_SCORE_O: st.column_config.ProgressColumn(TR_COL_SCORE_O, **progress),
            TR_COL_GRADE: st.column_config.TextColumn(TR_COL_GRADE, width="small"),
            TR_COL_RSI: st.column_config.NumberColumn(TR_COL_RSI, width="small"),
            TR_COL_VOLUME: st.column_config.NumberColumn(TR_COL_VOLUME, width="small"),
        },
    )


# Seans boyunca sayfa açık kalırsa veri ve tablolar kendiliğinden yenilenir. Yalnızca bu
# parça yeniden çalışır; sekme, arama ve filtre seçimleri korunur. Seans dışında önbellek
# anahtarı değişmediği için yeniden çalışma veri indirmez.
@st.fragment(run_every=timedelta(minutes=market.REFRESH_MINUTES))
def render(device: str, ctx: dict) -> None:
    vade = ctx.get("vade", pv.KISA)
    # Kod listesi app.py'den: BIST 100 + XU100 + takip listesindeki BIST 100 dışı hisseler
    tickers = ctx.get("tickers") or tuple(BIST100_TICKERS.keys()) + (ENDEKS,)

    loading = st.empty()
    loading.html(skeleton_html("list"))
    try:
        data = feed.batch(tickers)
    except DataFetchError as exc:
        loading.empty()
        error_state(str(exc), key="tr_retry")
        return
    scan = _scan(data.fetched_at.isoformat(), data.data)
    loading.empty()

    table_df, last_date = scan["rows"], scan["last_date"]
    if table_df.empty:
        error_state(TR_NO_DATA, key="tr_retry_empty")
        return
    # Son kısa vade sinyalinin kalite notu (önbellekli tarama dışında: kalibrasyon dosyası değişebilir)
    table_df[TR_COL_GRADE] = [
        (kalite_ui.ozet(skor)["grade"] if pd.notna(skor) else None) or NO_SIGNAL
        for skor in table_df[f"_sinyal_skor_{pv.KISA}"]
    ]
    ctx["last_dates"].append(last_date)

    now = market.now()
    is_open = market.market_open(now, last_date.date())
    gun_kesin_degil = market.provisional(now, last_date.date())
    hafta_yarim = scan["last_week"] is not None and not pv.hafta_tamamlandi(last_date, scan["last_week"])
    provisional = gun_kesin_degil if vade == pv.KISA else (gun_kesin_degil or hafta_yarim)

    _render_status(data, last_date, is_open)
    if vade == pv.ORTA and hafta_yarim:
        callout("info", None, VADE_WEEK_NOTE)
    elif gun_kesin_degil:
        callout("info", None, LIVE_SESSION_NOTE if is_open else LIVE_SETTLING_NOTE)

    _render_alim(scan, vade, provisional)
    _render_satis(scan, vade, provisional)
    _render_firsat(scan)
    _render_bicak(scan)

    caption = TR_AS_OF.format(date=fmt_date(last_date))
    missing_count = len(BIST100_TICKERS) - len(table_df)
    if missing_count > 0:
        caption += " · " + TR_MISSING.format(count=missing_count)

    _render_summary(table_df, vade, provisional)
    st.caption(caption)

    section_title(TR_LIST_TITLE, TR_LIST_CAPTION)
    _render_results(table_df, device, vade)
