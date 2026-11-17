"""BIST 100 Tarama sekmesi: Bugünün Alım Sinyalleri, özet şeridi ve alım skorlu tablo / liste.

Sinyal ve skor tarayici_motor'dan (Bluetsman Alım/Sat v2, kısa vade) gelir; veri feed.batch
ile piyasa saatine göre güncel tutulur ve sekme seans boyunca 15 dakikada bir kendini yeniler.
Görünüm cihaza göre seçilir (telefonda liste, geniş ekranda tablo).
"""

from datetime import timedelta

import pandas as pd
import streamlit as st

import feed
import market
import motor_veri
from config import BIST100_TICKERS
from data import DataFetchError
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
)
from ui.format import arrow, direction, fmt_date, fmt_num, fmt_pct
from ui.viewport import MOBILE
from ui import theme as t
from ui_text import (
    BL_DAYS_AGO,
    BL_TODAY,
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
    TR_AS_OF,
    TR_COL_CHANGE,
    TR_COL_COMPANY,
    TR_COL_PRICE,
    TR_COL_RSI,
    TR_COL_SCORE,
    TR_COL_SIGNAL,
    TR_COL_TICKER,
    TR_COL_VOLUME,
    TR_FALLING,
    TR_FILTER_ALL,
    TR_FILTER_LABEL,
    TR_FILTER_SIGNAL,
    TR_LIST_CAPTION,
    TR_LIST_META,
    TR_LIST_TITLE,
    TR_MISSING,
    TR_NO_DATA,
    TR_NO_RESULTS,
    TR_NO_SIGNALS,
    TR_RISING,
    TR_SEARCH_LABEL,
    TR_SEARCH_PLACEHOLDER,
    TR_SIGNAL_RECENT,
    TR_SIGNAL_TODAY,
    TR_SIGNAL_TODAY_SUB,
    TR_SORT_LABEL,
    TR_SORT_OPTIONS,
    TR_STRIP_FLAT,
    TR_STRIP_OF,
    TS_CAPTION,
    TS_NONE,
    TS_PROVISIONAL_BADGE,
    TS_PROVISIONAL_TITLE,
    TS_RECENT_NONE,
    TS_RECENT_TITLE,
    TS_RSI,
    TS_SIGNAL_PRICE,
    TS_SINCE,
    TS_STOP,
    TS_TARGET,
    TS_TITLE,
    TS_VOLUME,
    TS_VOLUME_VALUE,
)

SIGNAL_LOOKBACK = 10  # tablo ve "son 10 günde sinyal" için
RECENT_DAYS = 5       # bugün sinyal yoksa gösterilen geçmiş
NO_SIGNAL = "—"

SORTERS = {
    "score_desc": (TR_COL_SCORE, False),
    "change_desc": (TR_COL_CHANGE, False),
    "change_asc": (TR_COL_CHANGE, True),
    "ticker": (TR_COL_TICKER, True),
}


def _signal_text(days_since: int | None) -> str:
    if days_since is None:
        return NO_SIGNAL
    return BL_TODAY if days_since == 0 else BL_DAYS_AGO.format(days=days_since)


@st.cache_data(max_entries=3, show_spinner=False)
def _scan(data_key: str, _histories: dict) -> dict:
    """Her hisse için motoru çalıştırır; yalnızca ekranda gereken özetleri döndürür.

    data_key verinin çekildiği an olduğundan aynı veri için hesap bir kez yapılır
    (`_histories` önbellek anahtarına katılmaz).
    """
    rows, today, recent = [], [], []
    last_date = None
    for ticker, name in BIST100_TICKERS.items():
        df = _histories.get(ticker)
        if df is None or len(df) < 2:
            continue
        close = df["Close"]
        daily_change = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100
        last_date = max(last_date, df.index[-1]) if last_date is not None else df.index[-1]

        sonuc = motor_veri.analiz(df)
        last = sonuc.iloc[-1] if sonuc is not None else None
        signals = motor_veri.al_sinyalleri(sonuc, SIGNAL_LOOKBACK) if sonuc is not None else []
        days_since = signals[0]["once"] if signals else None

        rows.append({
            TR_COL_TICKER: ticker,
            TR_COL_COMPANY: name,
            TR_COL_PRICE: round(float(close.iloc[-1]), 2),
            TR_COL_CHANGE: round(float(daily_change), 2),
            TR_COL_SCORE: round(float(last["Alim_skor"])) if last is not None else None,
            TR_COL_SIGNAL: _signal_text(days_since),
            TR_COL_RSI: round(float(last["RSI"]), 1) if last is not None else None,
            TR_COL_VOLUME: round(float(last["Hacim_kat"]), 2) if last is not None else None,
            "_days_since": days_since,
        })

        for signal in signals:
            if signal["once"] == 0:
                today.append({
                    "ticker": ticker, "name": name, "score": signal["skor"],
                    "price": float(close.iloc[-1]), "change": float(daily_change),
                    "stop": signal["stop"], "target": signal["hedef"],
                    "rsi": float(last["RSI"]), "volume_ratio": float(last["Hacim_kat"]),
                })
            elif signal["once"] <= RECENT_DAYS:
                recent.append({"ticker": ticker, "name": name, **signal})

    today.sort(key=lambda s: s["score"], reverse=True)
    recent.sort(key=lambda s: (s["once"], -s["skor"]))
    return {"rows": pd.DataFrame(rows), "today": today, "recent": recent, "last_date": last_date}


# ---------------------------------------------------------------------------
# Bugünün Alım Sinyalleri
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


def _render_today(scan: dict, provisional: bool, is_open: bool) -> None:
    if provisional:
        callout("info", None, LIVE_SESSION_NOTE if is_open else LIVE_SETTLING_NOTE)

    today = scan["today"]
    if today:
        if provisional:
            st.caption(TS_PROVISIONAL_TITLE)
        signal_cards([
            {
                "ticker": s["ticker"], "name": s["name"], "score": s["score"],
                "price": fmt_num(s["price"], 2), "change": s["change"],
                "badge": TS_PROVISIONAL_BADGE if provisional else None,
                "rows": [
                    (TS_STOP, fmt_num(s["stop"], 2)),
                    (TS_TARGET, fmt_num(s["target"], 2)),
                    (TS_RSI, fmt_num(s["rsi"], 1)),
                    (TS_VOLUME, TS_VOLUME_VALUE.format(ratio=fmt_num(s["volume_ratio"], 2))),
                ],
            }
            for s in today
        ])
    else:
        callout("empty", TS_NONE, None)

    # Bugün sinyal yoksa ya da bugünküler henüz ön sinyalse, kesinleşmiş son günleri de göster.
    if not today or provisional:
        st.caption(TS_RECENT_TITLE)
        if scan["recent"]:
            recent_signal_list([
                {
                    "ticker": s["ticker"], "name": s["name"],
                    "when": BL_DAYS_AGO.format(days=s["once"]),
                    "price_label": f"{TS_SIGNAL_PRICE} {fmt_num(s['fiyat'], 2)} · skor {s['skor']:.0f}",
                    "change": s["degisim"], "since_label": TS_SINCE,
                }
                for s in scan["recent"]
            ])
        else:
            callout("empty", None, TS_RECENT_NONE)


# ---------------------------------------------------------------------------
# Özet ve liste
# ---------------------------------------------------------------------------

def _render_summary(table_df: pd.DataFrame, provisional: bool) -> None:
    changes = table_df[TR_COL_CHANGE]
    rising = int((changes.round(2) > 0).sum())
    falling = int((changes.round(2) < 0).sum())
    flat = len(changes) - rising - falling
    days = table_df["_days_since"]
    today_count = int((days == 0).sum())
    recent_count = int(days.notna().sum())

    cards = [
        metric_html(TR_RISING, f"▲ {rising}", sub=TR_STRIP_OF.format(count=len(changes)), value_class="ui-up"),
        metric_html(TR_FALLING, f"▼ {falling}", sub=TR_STRIP_FLAT.format(count=flat), value_class="ui-down"),
        metric_html(TR_SIGNAL_TODAY, str(today_count), sub=TR_SIGNAL_TODAY_SUB if provisional else None,
                    value_class="ui-accent" if today_count else ""),
        metric_html(TR_SIGNAL_RECENT.format(days=SIGNAL_LOOKBACK), str(recent_count),
                    value_class="ui-accent" if recent_count else ""),
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
        .map(signal_color, subset=[TR_COL_SIGNAL])
    )


def _render_filters(device: str) -> tuple[bool, str, str]:
    mobile = device == MOBILE
    signal_option = TR_FILTER_SIGNAL.format(days=SIGNAL_LOOKBACK)
    with st.container(horizontal=True, vertical_alignment="bottom", gap="small", key="tr_filters", wrap=True):
        show = st.segmented_control(
            TR_FILTER_LABEL, options=[TR_FILTER_ALL, signal_option], default=TR_FILTER_ALL, key="tr_show",
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


def _render_results(table_df: pd.DataFrame, device: str) -> None:
    only_signals, search, sort_key = _render_filters(device)

    filtered = table_df
    if only_signals:
        filtered = filtered[filtered["_days_since"].notna()]
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

    column, ascending = SORTERS[sort_key]
    ordered = filtered.sort_values(column, ascending=ascending, na_position="last")

    if device == MOBILE:
        stock_list([
            {
                "ticker": row[TR_COL_TICKER],
                "name": row[TR_COL_COMPANY],
                "price": fmt_num(row[TR_COL_PRICE], 2),
                "change": row[TR_COL_CHANGE],
                "meta": TR_LIST_META.format(
                    score=NO_SIGNAL if pd.isna(row[TR_COL_SCORE]) else int(row[TR_COL_SCORE]),
                    rsi=fmt_num(row[TR_COL_RSI], 1),
                ),
                "signal": None if row[TR_COL_SIGNAL] == NO_SIGNAL else row[TR_COL_SIGNAL],
            }
            for _, row in ordered.iterrows()
        ])
        return

    columns = [
        TR_COL_TICKER, TR_COL_COMPANY, TR_COL_PRICE, TR_COL_CHANGE,
        TR_COL_SCORE, TR_COL_SIGNAL, TR_COL_RSI, TR_COL_VOLUME,
    ]
    st.dataframe(
        _style_table(ordered[columns]),
        width="stretch",
        height=min(36 * (len(ordered) + 1) + 4, 640),
        hide_index=True,
        column_config={
            TR_COL_TICKER: st.column_config.TextColumn(TR_COL_TICKER, width="small"),
            TR_COL_PRICE: st.column_config.NumberColumn(TR_COL_PRICE),
            TR_COL_CHANGE: st.column_config.NumberColumn(TR_COL_CHANGE),
            TR_COL_SCORE: st.column_config.ProgressColumn(
                TR_COL_SCORE, min_value=0, max_value=100, format="%d", width="small",
            ),
            TR_COL_RSI: st.column_config.NumberColumn(TR_COL_RSI, width="small"),
            TR_COL_VOLUME: st.column_config.NumberColumn(TR_COL_VOLUME, width="small"),
        },
    )


# Seans boyunca sayfa açık kalırsa veri ve tablolar kendiliğinden yenilenir. Yalnızca bu
# parça yeniden çalışır; sekme, arama ve filtre seçimleri korunur. Seans dışında önbellek
# anahtarı değişmediği için yeniden çalışma veri indirmez.
@st.fragment(run_every=timedelta(minutes=market.REFRESH_MINUTES))
def render(device: str, ctx: dict) -> None:
    tickers = tuple(BIST100_TICKERS.keys())

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
    ctx["last_dates"].append(last_date)

    now = market.now()
    is_open = market.market_open(now, last_date.date())
    provisional = market.provisional(now, last_date.date())

    section_title(TS_TITLE, TS_CAPTION)
    _render_status(data, last_date, is_open)
    _render_today(scan, provisional, is_open)

    caption = TR_AS_OF.format(date=fmt_date(last_date))
    missing_count = len(tickers) - len(table_df)
    if missing_count > 0:
        caption += " · " + TR_MISSING.format(count=missing_count)

    _render_summary(table_df, provisional)
    st.caption(caption)

    section_title(TR_LIST_TITLE, TR_LIST_CAPTION)
    _render_results(table_df, device)
