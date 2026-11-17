"""BIST 100 Tarama sekmesi: özet şeridi ve Bluetsman skoruyla sıralanabilir tablo / kompakt liste.

Görünüm cihaza göre seçilir (telefonda liste, geniş ekranda tablo); kullanıcının ayrıca
görünüm, trend veya ısı haritası ayarı yapması gerekmez.
"""

import pandas as pd
import streamlit as st

import bluetsman
from config import BIST100_TICKERS
from data import DataFetchError, get_multiple_price_histories
from ui.components import (
    callout,
    error_state,
    metric_html,
    section_title,
    skeleton_html,
    stat_strip,
    stock_list,
)
from ui.format import arrow, direction, fmt_date, fmt_num, fmt_pct
from ui.viewport import MOBILE
from ui import theme as t
from ui_text import (
    BL_DAYS_AGO,
    BL_TODAY,
    TR_AS_OF,
    TR_COL_CHANGE,
    TR_COL_COMPANY,
    TR_COL_MET,
    TR_COL_PRICE,
    TR_COL_RSI,
    TR_COL_SCORE,
    TR_COL_SIGNAL,
    TR_COL_TICKER,
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
    TR_SORT_LABEL,
    TR_SORT_OPTIONS,
    TR_STRIP_FLAT,
    TR_STRIP_OF,
)

SIGNAL_LOOKBACK = 10  # "son 10 işlem günü"
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


@st.cache_data(ttl=3600, show_spinner=False)
def _scan(tickers: tuple[str, ...]) -> tuple[pd.DataFrame, pd.Timestamp | None]:
    """Tüm hisseler için günlük değişim, RSI ve Bluetsman durumunu tek tabloda toplar."""
    histories = get_multiple_price_histories(tickers)
    rows = []
    last_date = None
    for ticker in tickers:
        df = histories.get(ticker)
        if df is None or len(df) < 2:
            continue

        close = df["Close"]
        daily_change = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100
        signals = bluetsman.compute(df)
        rsi_value = signals["rsi_value"].iloc[-1]  # RSI(14), göstergenin kendi hesabından
        status = bluetsman.latest_status(signals, SIGNAL_LOOKBACK)
        last_date = max(last_date, df.index[-1]) if last_date is not None else df.index[-1]

        rows.append(
            {
                TR_COL_TICKER: ticker,
                TR_COL_COMPANY: BIST100_TICKERS[ticker],
                TR_COL_PRICE: round(float(close.iloc[-1]), 2),
                TR_COL_CHANGE: round(float(daily_change), 2),
                TR_COL_SCORE: round(status["score"]),
                TR_COL_MET: f"{status['met']}/{len(bluetsman.CONDITIONS)}",
                TR_COL_SIGNAL: _signal_text(status["days_since"]),
                TR_COL_RSI: round(float(rsi_value), 1) if pd.notna(rsi_value) else None,
                "_days_since": status["days_since"],
            }
        )
    return pd.DataFrame(rows), last_date


def _render_summary(table_df: pd.DataFrame) -> None:
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
        metric_html(TR_SIGNAL_TODAY, str(today_count), value_class="ui-accent" if today_count else ""),
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
                "meta": TR_LIST_META.format(score=row[TR_COL_SCORE], met=row[TR_COL_MET]),
                "signal": None if row[TR_COL_SIGNAL] == NO_SIGNAL else row[TR_COL_SIGNAL],
            }
            for _, row in ordered.iterrows()
        ])
        return

    columns = [
        TR_COL_TICKER, TR_COL_COMPANY, TR_COL_PRICE, TR_COL_CHANGE,
        TR_COL_SCORE, TR_COL_MET, TR_COL_SIGNAL, TR_COL_RSI,
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
            TR_COL_MET: st.column_config.TextColumn(TR_COL_MET, width="small"),
            TR_COL_RSI: st.column_config.NumberColumn(TR_COL_RSI, width="small"),
        },
    )


@st.fragment
def render(device: str, ctx: dict) -> None:
    tickers = tuple(BIST100_TICKERS.keys())

    loading = st.empty()
    loading.html(skeleton_html("list"))
    try:
        table_df, last_date = _scan(tickers)
    except DataFetchError as exc:
        loading.empty()
        error_state(str(exc), key="tr_retry")
        return
    loading.empty()

    if table_df.empty:
        error_state(TR_NO_DATA, key="tr_retry_empty")
        return
    ctx["last_dates"].append(last_date)

    caption = TR_AS_OF.format(date=fmt_date(last_date))
    missing_count = len(tickers) - len(table_df)
    if missing_count > 0:
        caption += " · " + TR_MISSING.format(count=missing_count)

    _render_summary(table_df)
    st.caption(caption)

    section_title(TR_LIST_TITLE, TR_LIST_CAPTION)
    _render_results(table_df, device)
