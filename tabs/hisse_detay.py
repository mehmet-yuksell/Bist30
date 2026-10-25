"""Hisse Detay sekmesi: hero blok, mum grafiği + göstergeler, Teknik Özet, Sinyal Karnesi."""

import pandas as pd
import streamlit as st

from backtest import run_buy_and_hold, run_macd_strategy, run_rsi_strategy, run_sma_cross_strategy
from data import (
    DataFetchError,
    get_adjusted_price_history,
    get_price_history,
    get_usdtry_rate,
    load_all_bist_symbols,
)
from indicators import bollinger_bands, ema, macd, rsi, sma
from signals import (
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    _last_crossover,
    describe_golden_death_cross,
    describe_macd_cross,
    describe_price_vs_ma,
    describe_rsi,
)
from ui import charts
from ui import theme as t
from ui.components import (
    badge,
    callout,
    error_state,
    hero,
    legend,
    metric_html,
    section_title,
    skeleton_html,
    strategy_cards,
    subtitle,
    summary_rows,
)
from ui.controls import date_range_popover, display_name, symbol_formatter, validate_date_range
from ui.format import fmt_compact, fmt_date, fmt_num, fmt_pct, fmt_price
from ui.viewport import MOBILE
from ui_text import (
    BACKTEST_DISCLAIMER,
    BACKTEST_INSUFFICIENT_SAMPLE,
    BADGE_DEATH_CROSS,
    BADGE_GOLDEN_CROSS,
    BADGE_INSUFFICIENT,
    BADGE_MACD_ABOVE,
    BADGE_MACD_BELOW,
    BADGE_MACD_CROSS_DOWN,
    BADGE_MACD_CROSS_UP,
    BADGE_PRICE_ABOVE_BOTH,
    BADGE_PRICE_BELOW_BOTH,
    BADGE_PRICE_MIXED,
    BADGE_RSI_NEUTRAL,
    BADGE_RSI_OVERBOUGHT,
    BADGE_RSI_OVERSOLD,
    BADGE_SMA_ABOVE,
    BADGE_SMA_BELOW,
    BT_CAPTION,
    BT_COST_HELP,
    BT_COST_LABEL,
    BT_ENTRY,
    BT_EQUITY_TITLE,
    BT_EXIT,
    BT_MAX_DRAWDOWN,
    BT_NEED_MORE_DATA,
    BT_NUM_TRADES,
    BT_PRICE_LEGEND,
    BT_SAMPLE_TITLE,
    BT_TAG_BENCHMARK,
    BT_TAG_BEST,
    BT_TAG_WORST,
    BT_TITLE,
    BT_TOTAL_RETURN,
    BT_TRADES_PICK,
    BT_TRADES_TITLE,
    BT_WIN_RATE,
    CHART_SERIES_BOLLINGER,
    CHART_SERIES_EMA20,
    CHART_SERIES_MACD,
    CHART_SERIES_SIGNAL,
    CHART_SERIES_SMA200,
    CHART_SERIES_SMA50,
    EXPANDER_LABEL,
    EXPLANATIONS,
    HD_CURRENCY_LABEL,
    HD_EMPTY_BODY,
    HD_EMPTY_TITLE,
    HD_FX_ALIGN_FAILED,
    HD_INDICATOR_OPTIONS,
    HD_INDICATORS_LABEL,
    HD_TICKER_LABEL,
    HD_VIEW_LABEL,
    HD_VIEW_WINDOWS,
    HERO_AS_OF,
    METRIC_52W_HIGH,
    METRIC_52W_LOW,
    METRIC_PERIOD_HIGH,
    METRIC_PERIOD_LOW,
    METRIC_RSI,
    METRIC_VOLUME,
    SUMMARY_CAPTION,
    SUMMARY_ROW_CROSS,
    SUMMARY_ROW_MACD,
    SUMMARY_ROW_PRICE_MA,
    SUMMARY_ROW_RSI,
    SUMMARY_TITLE,
    SYMBOL_HELP,
    SYMBOL_PLACEHOLDER,
)

CURRENCY_KEY = "hisse_detay_currency"
EXPANDER_ICON = ":material/help_outline:"
MIN_BACKTEST_ROWS = 210
MACD_CROSS_LOOKBACK = 5  # signals.describe_macd_cross ile aynı
SMA_CROSS_LOOKBACK = 10  # signals.describe_golden_death_cross ile aynı


# ---------------------------------------------------------------------------
# Veri hazırlığı
# ---------------------------------------------------------------------------

def _convert_to_usd(df: pd.DataFrame, start_date, end_date) -> tuple[pd.DataFrame, str]:
    """OHLC'yi göstergeler hesaplanmadan ÖNCE USD'ye çevirir (gerçek dolar bazlı göstergeler)."""
    try:
        fx_rate = get_usdtry_rate(start_date, end_date)
    except DataFetchError as exc:
        callout("warn", None, str(exc))
        return df, "TL"

    fx_aligned = fx_rate.reindex(df.index).ffill()
    valid_mask = fx_aligned.notna()
    converted = df.loc[valid_mask]
    fx_aligned = fx_aligned.loc[valid_mask]
    if converted.empty:
        callout("warn", None, HD_FX_ALIGN_FAILED)
        return df, "TL"

    converted = converted.copy()
    converted[["Open", "High", "Low", "Close"]] = converted[["Open", "High", "Low", "Close"]].div(
        fx_aligned, axis=0
    )
    return converted, "USD"


def _window_mask(index: pd.DatetimeIndex, view: str | None) -> pd.Series:
    days = HD_VIEW_WINDOWS.get(view) if view else None
    if not days:
        return pd.Series(True, index=index)
    return pd.Series(index >= index[-1] - pd.Timedelta(days=days), index=index)


# ---------------------------------------------------------------------------
# Hero ve Teknik Özet
# ---------------------------------------------------------------------------

def _render_hero(ticker: str, name: str, df: pd.DataFrame, rsi_series: pd.Series, currency: str) -> None:
    close = df["Close"]
    last_price = close.iloc[-1]
    prev_price = close.iloc[-2] if len(close) > 1 else last_price
    change_abs = last_price - prev_price
    change_pct = change_abs / prev_price * 100 if prev_price else 0.0

    cutoff = df.index[-1] - pd.Timedelta(days=365)
    has_full_year = df.index[0] <= cutoff
    window = df.loc[df.index >= cutoff] if has_full_year else df
    high_label, low_label = (METRIC_52W_HIGH, METRIC_52W_LOW) if has_full_year else (METRIC_PERIOD_HIGH, METRIC_PERIOD_LOW)

    last_rsi = rsi_series.iloc[-1]
    rsi_text, rsi_tone = _rsi_badge(last_rsi)

    sign = "+" if change_abs > 0 else ("−" if change_abs < 0 else "")
    metrics = [
        metric_html(high_label, fmt_price(window["High"].max(), currency)),
        metric_html(low_label, fmt_price(window["Low"].min(), currency)),
        metric_html(METRIC_VOLUME, fmt_compact(df["Volume"].iloc[-1])),
        metric_html(METRIC_RSI, fmt_num(last_rsi, 1), sub=badge(rsi_text, rsi_tone)),
    ]
    hero(
        ticker=ticker,
        name=name,
        price=fmt_price(last_price, currency),
        change_pct=change_pct,
        change_abs=f"{sign}{fmt_num(abs(change_abs))}",
        as_of=HERO_AS_OF.format(date=fmt_date(df.index[-1])),
        metrics=metrics,
    )


def _rsi_badge(value: float) -> tuple[str, str]:
    if pd.isna(value):
        return BADGE_INSUFFICIENT, "neutral"
    if value >= RSI_OVERBOUGHT:
        return BADGE_RSI_OVERBOUGHT, "warn"
    if value <= RSI_OVERSOLD:
        return BADGE_RSI_OVERSOLD, "warn"
    return BADGE_RSI_NEUTRAL, "neutral"


def _cross_badge(diff: pd.Series, lookback: int, labels: tuple[str, str, str, str]) -> tuple[str, str]:
    """labels: (yukarı kesişim, aşağı kesişim, üzerinde, altında)."""
    diff = diff.dropna()
    if len(diff) < 2:
        return BADGE_INSUFFICIENT, "neutral"
    cross = _last_crossover(diff, lookback)
    if cross == "up":
        return labels[0], "up"
    if cross == "down":
        return labels[1], "down"
    return (labels[2], "up") if diff.iloc[-1] > 0 else (labels[3], "down")


def _price_ma_badge(price: float, sma50: float, sma200: float) -> tuple[str, str]:
    if pd.isna(sma50) or pd.isna(sma200):
        return BADGE_INSUFFICIENT, "neutral"
    if price >= sma50 and price >= sma200:
        return BADGE_PRICE_ABOVE_BOTH, "up"
    if price < sma50 and price < sma200:
        return BADGE_PRICE_BELOW_BOTH, "down"
    return BADGE_PRICE_MIXED, "neutral"


def _render_teknik_ozet(close, sma50_series, sma200_series, rsi_series, macd_df) -> None:
    section_title(SUMMARY_TITLE, SUMMARY_CAPTION)

    last_price = close.iloc[-1]
    last_sma50 = sma50_series.iloc[-1]
    last_sma200 = sma200_series.iloc[-1]
    last_rsi = rsi_series.iloc[-1]

    macd_badge = _cross_badge(
        macd_df["macd"] - macd_df["signal"], MACD_CROSS_LOOKBACK,
        (BADGE_MACD_CROSS_UP, BADGE_MACD_CROSS_DOWN, BADGE_MACD_ABOVE, BADGE_MACD_BELOW),
    )
    sma_badge = _cross_badge(
        sma50_series - sma200_series, SMA_CROSS_LOOKBACK,
        (BADGE_GOLDEN_CROSS, BADGE_DEATH_CROSS, BADGE_SMA_ABOVE, BADGE_SMA_BELOW),
    )
    summary_rows([
        (SUMMARY_ROW_RSI, *_rsi_badge(last_rsi), describe_rsi(last_rsi)),
        (SUMMARY_ROW_MACD, *macd_badge, describe_macd_cross(macd_df)),
        (SUMMARY_ROW_PRICE_MA, *_price_ma_badge(last_price, last_sma50, last_sma200),
         describe_price_vs_ma(last_price, last_sma50, last_sma200)),
        (SUMMARY_ROW_CROSS, *sma_badge, describe_golden_death_cross(sma50_series, sma200_series)),
    ])

    with st.expander(f"{EXPANDER_LABEL} (Altın/Ölüm Kesişimi)", icon=EXPANDER_ICON):
        st.write(EXPLANATIONS["golden_death_cross"])


# ---------------------------------------------------------------------------
# Sinyal Karnesi
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def _run_backtests(ticker: str, start_date, end_date, cost_pct: float):
    """Düzeltilmiş fiyatla dört stratejiyi çalıştırır; aynı girdiler için önbellekten döner."""
    adj_df = get_adjusted_price_history(ticker, start_date, end_date)
    if len(adj_df) < MIN_BACKTEST_ROWS:
        return adj_df, None
    return adj_df, {
        "rsi": run_rsi_strategy(adj_df, cost_pct),
        "macd": run_macd_strategy(adj_df, cost_pct),
        "sma": run_sma_cross_strategy(adj_df, cost_pct),
        "buy_hold": run_buy_and_hold(adj_df, cost_pct),
    }


def _strategy_card_data(results: dict) -> list[dict]:
    ranked = sorted(results, key=lambda k: results[k].total_return_pct)
    worst, best = ranked[0], ranked[-1]
    cards = []
    for key, result in results.items():
        if key == best:
            tag, tag_text = "best", BT_TAG_BEST
        elif key == worst:
            tag, tag_text = "worst", BT_TAG_WORST
        elif key == "buy_hold":
            tag, tag_text = "benchmark", BT_TAG_BENCHMARK
        else:
            tag, tag_text = None, ""
        cards.append({
            "name": result.name,
            "total": result.total_return_pct,
            "total_label": BT_TOTAL_RETURN,
            "tag": tag,
            "tag_text": tag_text,
            "rows": [
                (BT_MAX_DRAWDOWN, fmt_pct(result.max_drawdown_pct)),
                (BT_NUM_TRADES, str(result.num_trades) if result.num_trades is not None else "—"),
                (BT_WIN_RATE, fmt_pct(result.win_rate_pct, 1, signed=False) if result.win_rate_pct is not None else "—"),
            ],
        })
    return cards


def _render_sinyal_karnesi(ticker: str, start_date, end_date, device: str) -> None:
    section_title(BT_TITLE, BT_CAPTION)

    cost_pct = st.number_input(
        BT_COST_LABEL, min_value=0.0, max_value=5.0, value=0.1, step=0.05,
        help=BT_COST_HELP, key="bt_cost", width=260 if device != MOBILE else "stretch",
    )

    try:
        adj_df, results = _run_backtests(ticker, start_date, end_date, cost_pct)
    except DataFetchError as exc:
        error_state(str(exc), key="bt_retry")
        return

    if results is None:
        callout("info", None, BT_NEED_MORE_DATA)
        return

    strategy_cards(_strategy_card_data(results))

    insufficient = [
        BACKTEST_INSUFFICIENT_SAMPLE.format(name=results[key].name, count=results[key].num_trades)
        for key in ("rsi", "macd", "sma")
        if results[key].num_trades is not None and results[key].num_trades < 10
    ]
    if insufficient:
        callout("warn", BT_SAMPLE_TITLE, insufficient)

    subtitle(BT_EQUITY_TITLE)
    legend([
        (result.name, charts.STRATEGY_COLORS[key], "line") for key, result in results.items()
    ])
    charts.show_chart(charts.build_equity_curve_figure(results, device), device, key="bt_equity")

    subtitle(BT_TRADES_TITLE)
    strategy_choice = st.pills(
        BT_TRADES_PICK,
        options=["rsi", "macd", "sma"],
        format_func=lambda k: results[k].name,
        default="rsi",
        required=True,
        key="bt_strategy",
    ) or "rsi"
    legend([
        (BT_PRICE_LEGEND, t.MUTED_LINE, "line"),
        (BT_ENTRY, t.UP, "tri-up"),
        (BT_EXIT, t.DOWN, "tri-down"),
    ])
    charts.show_chart(
        charts.build_trade_markers_figure(adj_df["Close"], results[strategy_choice], device),
        device, key="bt_trades",
    )

    with st.expander(f"{EXPANDER_LABEL} (Sinyal Karnesi)", icon=EXPANDER_ICON):
        st.write(EXPLANATIONS["backtest"])

    st.caption(BACKTEST_DISCLAIMER)


# ---------------------------------------------------------------------------
# Sekme
# ---------------------------------------------------------------------------

@st.fragment
def render(device: str, ctx: dict) -> None:
    all_stocks = load_all_bist_symbols()
    all_symbols = sorted(all_stocks.keys())
    default_ticker = "THYAO" if "THYAO" in all_stocks else all_symbols[0]

    with st.container(horizontal=True, vertical_alignment="bottom", gap="small", key="hd_controls"):
        ticker_raw = st.selectbox(
            HD_TICKER_LABEL,
            options=all_symbols,
            index=all_symbols.index(default_ticker),
            format_func=symbol_formatter(all_stocks),
            accept_new_options=True,
            placeholder=SYMBOL_PLACEHOLDER,
            key="hd_ticker",
            width="stretch",
        )
        date_range = date_range_popover("hd_dates", default_days=3 * 365)
    st.caption(SYMBOL_HELP)

    if not ticker_raw or not ticker_raw.strip():
        callout("empty", HD_EMPTY_TITLE, HD_EMPTY_BODY)
        return
    ticker = ticker_raw.strip().upper()

    dates = validate_date_range(date_range)
    if dates is None:
        return
    start_date, end_date = dates

    loading = st.empty()
    loading.html(skeleton_html("detail"))
    try:
        df = get_price_history(ticker, start_date, end_date)
    except DataFetchError as exc:
        loading.empty()
        error_state(str(exc), key="hd_retry")
        return
    loading.empty()
    ctx["last_dates"].append(df.index[-1])

    # Para birimi anahtarı grafik araç çubuğunda durur; hero ondan önce çizildiği için
    # seçili değer oturum durumundan okunur (anahtara tıklamak sayfayı yeniden çalıştırır).
    currency = st.session_state.get(CURRENCY_KEY) or "TL"
    currency_label = "TL"
    if currency == "USD":
        df, currency_label = _convert_to_usd(df, start_date, end_date)

    close = df["Close"]
    sma50_series = sma(close, 50)
    sma200_series = sma(close, 200)
    rsi_series = rsi(close, 14)
    macd_df = macd(close)

    _render_hero(ticker, display_name(ticker, all_stocks), df, rsi_series, currency_label)

    with st.container(horizontal=True, gap="medium", key="hd_toolbar"):
        view = st.segmented_control(
            HD_VIEW_LABEL, options=list(HD_VIEW_WINDOWS),
            default="3A" if device == MOBILE else "1Y", key="hd_view",
        )
        st.segmented_control(HD_CURRENCY_LABEL, options=["TL", "USD"], default="TL", key=CURRENCY_KEY)
        indicators = st.pills(
            HD_INDICATORS_LABEL, options=HD_INDICATOR_OPTIONS, selection_mode="multi",
            default=["SMA 50", "SMA 200"], key="hd_indicators",
        ) or []

    if currency == "USD":
        with st.expander(f"{EXPANDER_LABEL} (Dolar Bazlı Görünüm)", icon=EXPANDER_ICON):
            st.write(EXPLANATIONS["usd_view"])

    mask = _window_mask(df.index, view)
    overlays = {
        "sma50": sma50_series[mask] if "SMA 50" in indicators else None,
        "sma200": sma200_series[mask] if "SMA 200" in indicators else None,
        "ema20": ema(close, 20)[mask] if "EMA 20" in indicators else None,
        "bollinger": bollinger_bands(close, 20)[mask] if "Bollinger" in indicators else None,
    }
    legend_items = [
        (name, charts.OVERLAY_COLORS[key], "line")
        for key, name in (
            ("sma50", CHART_SERIES_SMA50), ("sma200", CHART_SERIES_SMA200),
            ("ema20", CHART_SERIES_EMA20), ("bollinger", CHART_SERIES_BOLLINGER),
        )
        if overlays[key] is not None
    ]
    legend_items += [
        (CHART_SERIES_MACD, charts.OVERLAY_COLORS["macd"], "line"),
        (CHART_SERIES_SIGNAL, charts.OVERLAY_COLORS["signal"], "line"),
    ]
    legend(legend_items)

    fig = charts.build_detail_figure(
        df=df[mask], overlays=overlays, rsi_series=rsi_series[mask], macd_df=macd_df[mask],
        currency_label=currency_label, device=device,
    )
    charts.show_chart(fig, device, key="hd_chart")

    explain_cols = st.columns(3)
    with explain_cols[0]:
        with st.expander(f"{EXPANDER_LABEL} (Ortalamalar, Bollinger)", icon=EXPANDER_ICON):
            st.write(EXPLANATIONS["sma_ema"])
            st.write(EXPLANATIONS["bollinger"])
    with explain_cols[1]:
        with st.expander(f"{EXPANDER_LABEL} (RSI)", icon=EXPANDER_ICON):
            st.write(EXPLANATIONS["rsi"])
    with explain_cols[2]:
        with st.expander(f"{EXPANDER_LABEL} (MACD)", icon=EXPANDER_ICON):
            st.write(EXPLANATIONS["macd"])

    _render_teknik_ozet(close, sma50_series, sma200_series, rsi_series, macd_df)

    _render_sinyal_karnesi(ticker, start_date, end_date, device)
