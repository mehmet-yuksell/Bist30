"""Karşılaştırma sekmesi: 2-5 hissenin normalize getirisi, dönem sıralaması ve korelasyonu."""

import pandas as pd
import streamlit as st

from data import DataFetchError, get_price_history, load_all_bist_symbols
from ui import charts
from ui import theme as t
from ui.components import callout, error_state, legend, rank_list, section_title, skeleton_html
from ui.controls import date_range_popover, symbol_formatter, validate_date_range
from ui.format import fmt_date
from ui.viewport import DESKTOP
from ui_text import (
    EXPANDER_LABEL,
    EXPLANATIONS,
    KR_CORR_NOT_ENOUGH,
    KR_CORR_TITLE,
    KR_LIMIT_HINT,
    KR_NEED_TWO,
    KR_NEED_TWO_TITLE,
    KR_NOT_ENOUGH,
    KR_PERIOD,
    KR_RANK_TITLE,
    KR_RETURN_TITLE,
    KR_TICKERS_LABEL,
    SYMBOL_HELP,
    SYMBOL_PLACEHOLDER,
)

EXPANDER_ICON = ":material/help_outline:"
MAX_SELECTIONS = 5


def _render_correlation(histories: dict, tickers: list[str], device: str) -> None:
    section_title(KR_CORR_TITLE)
    returns_df = pd.DataFrame({ticker: histories[ticker]["Close"].pct_change() for ticker in tickers}).dropna()
    if len(returns_df) < 2:
        callout("info", None, KR_CORR_NOT_ENOUGH)
    else:
        fig = charts.build_correlation_heatmap_figure(returns_df.corr(), device)
        charts.show_chart(fig, device, key="kr_corr")


def _render_explanations() -> None:
    with st.expander(f"{EXPANDER_LABEL} (Normalize Getiri)", icon=EXPANDER_ICON):
        st.write(EXPLANATIONS["normalized_return"])
    with st.expander(f"{EXPANDER_LABEL} (Korelasyon)", icon=EXPANDER_ICON):
        st.write(EXPLANATIONS["correlation"])


@st.fragment
def render(device: str, ctx: dict) -> None:
    all_stocks = load_all_bist_symbols()
    all_symbols = sorted(all_stocks.keys())
    default_selection = [ticker for ticker in ("AKBNK", "GARAN", "THYAO") if ticker in all_stocks]

    with st.container(horizontal=True, vertical_alignment="bottom", gap="small", key="kr_controls", wrap=True):
        selected_raw = st.multiselect(
            KR_TICKERS_LABEL,
            options=all_symbols,
            default=default_selection,
            format_func=symbol_formatter(all_stocks),
            max_selections=MAX_SELECTIONS,
            placeholder=SYMBOL_PLACEHOLDER,
            key="kr_tickers",
            width="stretch",
        )
        date_range = date_range_popover("karsilastirma_tarih", default_days=365)
    selected = list(dict.fromkeys(ticker.strip().upper() for ticker in selected_raw if ticker.strip()))
    st.caption(f"{KR_LIMIT_HINT.format(count=len(selected))} {SYMBOL_HELP.format(count=len(all_symbols))}")

    if len(selected) < 2:
        callout("empty", KR_NEED_TWO_TITLE, KR_NEED_TWO)
        return

    dates = validate_date_range(date_range)
    if dates is None:
        return
    start_date, end_date = dates

    loading = st.empty()
    loading.html(skeleton_html("compare"))
    histories, failures = {}, []
    for ticker in selected:
        try:
            histories[ticker] = get_price_history(ticker, start_date, end_date)
        except DataFetchError as exc:
            failures.append(str(exc))
    loading.empty()

    valid_tickers = [ticker for ticker in selected if ticker in histories]
    if len(valid_tickers) < 2:
        error_state(" ".join(failures) or KR_NOT_ENOUGH, key="kr_retry")
        return
    if failures:
        callout("warn", None, failures)
    ctx["last_dates"].append(max(histories[ticker].index[-1] for ticker in valid_tickers))

    # Renk, hissenin seçim sırasını izler (sıralamaya göre değişmez).
    colors = {ticker: t.SERIES[i % len(t.SERIES)] for i, ticker in enumerate(valid_tickers)}
    period_returns = {
        ticker: (histories[ticker]["Close"].iloc[-1] / histories[ticker]["Close"].iloc[0] - 1) * 100
        for ticker in valid_tickers
    }
    ranking = sorted(valid_tickers, key=lambda ticker: period_returns[ticker], reverse=True)

    def render_rank() -> None:
        section_title(KR_RANK_TITLE)
        rank_list([(ticker, colors[ticker], period_returns[ticker]) for ticker in ranking])
        st.caption(KR_PERIOD.format(start=fmt_date(start_date), end=fmt_date(end_date)))

    def render_returns() -> None:
        section_title(KR_RETURN_TITLE)
        legend([(ticker, colors[ticker], "line") for ticker in valid_tickers])
        fig = charts.build_normalized_return_figure(histories, valid_tickers, device)
        charts.show_chart(fig, device, key="kr_returns")

    if device == DESKTOP:
        rank_col, chart_col = st.columns([4, 8], gap="large")
        with rank_col:
            render_rank()
        with chart_col:
            render_returns()
        corr_col, explain_col = st.columns([7, 5], gap="large")
        with corr_col:
            _render_correlation(histories, valid_tickers, device)
        with explain_col:
            section_title(EXPANDER_LABEL)
            _render_explanations()
    else:
        render_rank()
        render_returns()
        _render_correlation(histories, valid_tickers, device)
        _render_explanations()
