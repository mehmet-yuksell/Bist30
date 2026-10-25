"""BIST 30 Tarama sekmesi: özet şeridi, ısı haritası ve sıralanabilir tablo / kompakt liste."""

import pandas as pd
import streamlit as st

from config import BIST30_TICKERS
from data import DataFetchError, get_multiple_price_histories
from indicators import rsi, sma
from signals import trend_label
from ui.components import (
    callout,
    change_badge,
    error_state,
    heat_grid,
    metric_html,
    section_title,
    skeleton_html,
    stat_strip,
    stock_list,
)
from ui.format import arrow, direction, fmt_date, fmt_num, fmt_pct
from ui.viewport import DESKTOP, MOBILE
from ui import theme as t
from ui_text import (
    TR_AS_OF,
    TR_COL_CHANGE,
    TR_COL_COMPANY,
    TR_COL_PRICE,
    TR_COL_RSI,
    TR_COL_TICKER,
    TR_COL_TREND,
    TR_FALLING,
    TR_HEATMAP_TITLE,
    TR_LIST_TITLE,
    TR_MISSING,
    TR_NO_DATA,
    TR_NO_RESULTS,
    TR_RISING,
    TR_SEARCH_LABEL,
    TR_SEARCH_PLACEHOLDER,
    TR_SORT_LABEL,
    TR_SORT_OPTIONS,
    TR_STRIP_FLAT,
    TR_STRIP_OF,
    TR_TOP_GAINER,
    TR_TOP_LOSER,
    TR_TREND_LABEL,
    TR_VIEW_LABEL,
    TR_VIEW_LIST,
    TR_VIEW_TABLE,
)

SORTERS = {
    "change_desc": (TR_COL_CHANGE, False),
    "change_asc": (TR_COL_CHANGE, True),
    "ticker": (TR_COL_TICKER, True),
    "rsi_desc": (TR_COL_RSI, False),
}


def _build_rows(histories: dict, tickers: tuple[str, ...]) -> tuple[pd.DataFrame, pd.Timestamp | None]:
    rows = []
    last_date = None
    for ticker in tickers:
        df = histories.get(ticker)
        if df is None or len(df) < 2:
            continue

        close = df["Close"]
        last_price = close.iloc[-1]
        prev_price = close.iloc[-2]
        daily_change = (last_price - prev_price) / prev_price * 100
        rsi_value = rsi(close, 14).iloc[-1]
        last_date = max(last_date, df.index[-1]) if last_date is not None else df.index[-1]

        rows.append(
            {
                TR_COL_TICKER: ticker,
                TR_COL_COMPANY: BIST30_TICKERS[ticker],
                TR_COL_PRICE: round(float(last_price), 2),
                TR_COL_CHANGE: round(float(daily_change), 2),
                TR_COL_RSI: round(float(rsi_value), 1) if pd.notna(rsi_value) else None,
                TR_COL_TREND: trend_label(sma(close, 50).iloc[-1], sma(close, 200).iloc[-1]),
            }
        )
    return pd.DataFrame(rows), last_date


def _render_summary(table_df: pd.DataFrame) -> None:
    changes = table_df[TR_COL_CHANGE]
    rising = int((changes.round(2) > 0).sum())
    falling = int((changes.round(2) < 0).sum())
    flat = len(changes) - rising - falling
    top = table_df.loc[changes.idxmax()]
    bottom = table_df.loc[changes.idxmin()]

    cards = [
        metric_html(TR_RISING, f"▲ {rising}", sub=TR_STRIP_OF.format(count=len(changes)), value_class="ui-up"),
        metric_html(TR_FALLING, f"▼ {falling}", sub=TR_STRIP_FLAT.format(count=flat), value_class="ui-down"),
        metric_html(TR_TOP_GAINER, top[TR_COL_TICKER], sub=change_badge(top[TR_COL_CHANGE])),
        metric_html(TR_TOP_LOSER, bottom[TR_COL_TICKER], sub=change_badge(bottom[TR_COL_CHANGE])),
    ]
    stat_strip(cards, breadth=(rising, flat, falling))


def _style_table(df: pd.DataFrame):
    def change_color(value):
        tone = direction(value)
        color = {"up": t.UP, "down": t.DOWN_TEXT}.get(tone, t.TEXT_2)
        return f"color: {color}; font-weight: 600"

    return (
        df.style
        .format({
            TR_COL_PRICE: lambda v: fmt_num(v, 2),
            TR_COL_CHANGE: lambda v: f"{arrow(v)} {fmt_pct(v)}",
            TR_COL_RSI: lambda v: fmt_num(v, 1),
        })
        .map(change_color, subset=[TR_COL_CHANGE])
    )


def _render_filters(table_df: pd.DataFrame, device: str):
    with st.container(horizontal=True, vertical_alignment="bottom", gap="small", key="tr_filters"):
        search = st.text_input(
            TR_SEARCH_LABEL, "", placeholder=TR_SEARCH_PLACEHOLDER, key="tr_search",
            width="stretch" if device == MOBILE else 280,
        )
        view = st.segmented_control(
            TR_VIEW_LABEL, options=[TR_VIEW_LIST, TR_VIEW_TABLE],
            default=TR_VIEW_LIST if device == MOBILE else TR_VIEW_TABLE, key="tr_view",
        ) or (TR_VIEW_LIST if device == MOBILE else TR_VIEW_TABLE)
        sort_key = "change_desc"
        if view == TR_VIEW_LIST:
            sort_key = st.selectbox(
                TR_SORT_LABEL, options=list(TR_SORT_OPTIONS), format_func=TR_SORT_OPTIONS.get,
                key="tr_sort", width=200,
            )

    trend_options = sorted(table_df[TR_COL_TREND].unique())
    selected_trends = st.pills(
        TR_TREND_LABEL, trend_options, selection_mode="multi", default=trend_options, key="tr_trends",
    ) or []
    return search, view, sort_key, selected_trends


def _render_results(table_df: pd.DataFrame, device: str) -> None:
    search, view, sort_key, selected_trends = _render_filters(table_df, device)

    filtered = table_df[table_df[TR_COL_TREND].isin(selected_trends)]
    if search:
        query = search.strip()
        mask = filtered[TR_COL_TICKER].str.contains(query, case=False, regex=False) | filtered[
            TR_COL_COMPANY
        ].str.contains(query, case=False, regex=False)
        filtered = filtered[mask]

    if filtered.empty:
        callout("empty", None, TR_NO_RESULTS)
        return

    if view == TR_VIEW_LIST:
        column, ascending = SORTERS[sort_key]
        ordered = filtered.sort_values(column, ascending=ascending, na_position="last")
        stock_list([
            {
                "ticker": row[TR_COL_TICKER],
                "name": row[TR_COL_COMPANY],
                "price": fmt_num(row[TR_COL_PRICE], 2),
                "change": row[TR_COL_CHANGE],
                "rsi": fmt_num(row[TR_COL_RSI], 1),
                "trend": row[TR_COL_TREND],
            }
            for _, row in ordered.iterrows()
        ])
        return

    # Telefonda tablo seçilirse en önemli 5 sütun gösterilir (şirket adı listede/aramada kalır).
    columns = (
        [TR_COL_TICKER, TR_COL_PRICE, TR_COL_CHANGE, TR_COL_RSI, TR_COL_TREND]
        if device == MOBILE
        else list(filtered.columns)
    )
    st.dataframe(
        _style_table(filtered),
        width="stretch",
        height=min(36 * (len(filtered) + 1) + 4, 470),
        hide_index=True,
        column_order=columns,
        column_config={
            TR_COL_TICKER: st.column_config.TextColumn(TR_COL_TICKER, width="small"),
            TR_COL_PRICE: st.column_config.NumberColumn(TR_COL_PRICE),
            TR_COL_CHANGE: st.column_config.NumberColumn(TR_COL_CHANGE),
            TR_COL_RSI: st.column_config.NumberColumn(TR_COL_RSI, width="small"),
        },
    )


@st.fragment
def render(device: str, ctx: dict) -> None:
    tickers = tuple(BIST30_TICKERS.keys())

    loading = st.empty()
    loading.html(skeleton_html("list"))
    try:
        histories = get_multiple_price_histories(tickers)
    except DataFetchError as exc:
        loading.empty()
        error_state(str(exc), key="tr_retry")
        return
    loading.empty()

    table_df, last_date = _build_rows(histories, tickers)
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

    heat_items = [
        (row[TR_COL_TICKER], row[TR_COL_COMPANY], row[TR_COL_CHANGE]) for _, row in table_df.iterrows()
    ]
    if device == DESKTOP:
        heat_col, table_col = st.columns([5, 7], gap="large")
        with heat_col:
            section_title(TR_HEATMAP_TITLE)
            heat_grid(heat_items)
        with table_col:
            section_title(TR_LIST_TITLE)
            _render_results(table_df, device)
    else:
        section_title(TR_HEATMAP_TITLE)
        heat_grid(heat_items)
        section_title(TR_LIST_TITLE)
        _render_results(table_df, device)
