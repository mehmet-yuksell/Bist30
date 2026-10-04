from datetime import date, timedelta

import numpy as np
import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from config import BIST30_TICKERS
from data import DataFetchError, get_price_history
from indicators import bollinger_bands, ema, macd, rsi, sma
from signals import (
    describe_golden_death_cross,
    describe_macd_cross,
    describe_price_vs_ma,
    describe_rsi,
)
from ui_text import (
    APP_TITLE,
    DISCLAIMER,
    EXPANDER_LABEL,
    EXPLANATIONS,
    TAB_HISSE_DETAY,
    TAB_KARSILASTIRMA,
    TAB_TARAMA,
)

COLOR_GOOD = "#0ca30c"
COLOR_CRITICAL = "#d03b3b"
COLOR_BLUE = "#3987e5"
COLOR_ORANGE = "#d95926"
COLOR_AQUA = "#199e70"
COLOR_MAGENTA = "#d55181"
COLOR_MUTED = "#898781"
COLOR_GRID = "#2c2c2a"
COLOR_TEXT = "#FAFAFA"


def build_detail_figure(df, sma50, sma200, ema20, bollinger, rsi_series, macd_df, ticker):
    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.45, 0.15, 0.17, 0.23],
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name=ticker,
            increasing_line_color=COLOR_GOOD,
            increasing_fillcolor=COLOR_GOOD,
            decreasing_line_color=COLOR_CRITICAL,
            decreasing_fillcolor=COLOR_CRITICAL,
        ),
        row=1,
        col=1,
    )

    if sma50 is not None:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=sma50, mode="lines", name="SMA (50)",
                line=dict(color=COLOR_BLUE, width=2),
            ),
            row=1, col=1,
        )
    if sma200 is not None:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=sma200, mode="lines", name="SMA (200)",
                line=dict(color=COLOR_ORANGE, width=2),
            ),
            row=1, col=1,
        )
    if ema20 is not None:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=ema20, mode="lines", name="EMA (20)",
                line=dict(color=COLOR_AQUA, width=2),
            ),
            row=1, col=1,
        )
    if bollinger is not None:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=bollinger["upper"], mode="lines", name="Bollinger Üst",
                line=dict(color=COLOR_MAGENTA, width=1),
            ),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df.index, y=bollinger["lower"], mode="lines", name="Bollinger Alt",
                line=dict(color=COLOR_MAGENTA, width=1),
                fill="tonexty", fillcolor="rgba(213,81,129,0.12)",
            ),
            row=1, col=1,
        )

    volume_colors = np.where(df["Close"] >= df["Open"], COLOR_GOOD, COLOR_CRITICAL)
    fig.add_trace(
        go.Bar(x=df.index, y=df["Volume"], name="Hacim", marker_color=volume_colors, opacity=0.7),
        row=2, col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=df.index, y=rsi_series, mode="lines", name="RSI",
            line=dict(color=COLOR_BLUE, width=2),
        ),
        row=3, col=1,
    )
    fig.add_hline(y=70, row=3, col=1, line_dash="dash", line_color=COLOR_MUTED)
    fig.add_hline(y=30, row=3, col=1, line_dash="dash", line_color=COLOR_MUTED)

    histogram_colors = np.where(macd_df["histogram"] >= 0, COLOR_GOOD, COLOR_CRITICAL)
    fig.add_trace(
        go.Bar(
            x=df.index, y=macd_df["histogram"], name="Histogram",
            marker_color=histogram_colors, opacity=0.6,
        ),
        row=4, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index, y=macd_df["macd"], mode="lines", name="MACD",
            line=dict(color=COLOR_BLUE, width=2),
        ),
        row=4, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index, y=macd_df["signal"], mode="lines", name="Sinyal",
            line=dict(color=COLOR_ORANGE, width=2),
        ),
        row=4, col=1,
    )

    fig.update_yaxes(title_text="Fiyat (TL)", row=1, col=1)
    fig.update_yaxes(title_text="Hacim", row=2, col=1)
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)
    fig.update_yaxes(title_text="MACD", row=4, col=1)
    fig.update_xaxes(rangeslider_visible=False, row=1, col=1)

    fig.update_xaxes(showgrid=True, gridcolor=COLOR_GRID, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor=COLOR_GRID, zeroline=False)

    fig.update_layout(
        height=850,
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLOR_TEXT),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=10, r=10, t=30, b=10),
    )

    return fig


def render_teknik_ozet(close, sma50_series, sma200_series, rsi_series, macd_df):
    st.subheader("Teknik Özet")

    last_price = close.iloc[-1]
    last_sma50 = sma50_series.iloc[-1]
    last_sma200 = sma200_series.iloc[-1]
    last_rsi = rsi_series.iloc[-1]

    with st.container(border=True):
        st.markdown(f"- {describe_rsi(last_rsi)}")
        st.markdown(f"- {describe_macd_cross(macd_df)}")
        st.markdown(f"- {describe_price_vs_ma(last_price, last_sma50, last_sma200)}")
        st.markdown(f"- {describe_golden_death_cross(sma50_series, sma200_series)}")

    with st.expander(f"{EXPANDER_LABEL} (Altın/Ölüm Kesişimi)"):
        st.write(EXPLANATIONS["golden_death_cross"])


def render_hisse_detay_tab() -> None:
    col_ticker, col_dates = st.columns([1, 2])

    with col_ticker:
        ticker = st.selectbox(
            "Hisse",
            options=list(BIST30_TICKERS.keys()),
            format_func=lambda t: f"{t} — {BIST30_TICKERS[t]}",
        )

    with col_dates:
        today = date.today()
        default_start = today - timedelta(days=3 * 365)
        date_range = st.date_input(
            "Tarih aralığı",
            value=(default_start, today),
            min_value=date(2005, 1, 1),
            max_value=today,
        )

    if not isinstance(date_range, tuple) or len(date_range) != 2:
        st.info("Lütfen bir başlangıç ve bitiş tarihi seçin.")
        return

    start_date, end_date = date_range
    if start_date >= end_date:
        st.warning("Başlangıç tarihi, bitiş tarihinden önce olmalıdır.")
        return

    try:
        df = get_price_history(ticker, start_date, end_date)
    except DataFetchError as exc:
        st.error(str(exc))
        return

    close = df["Close"]

    st.markdown("**Göstergeler**")
    opt_cols = st.columns(4)
    with opt_cols[0]:
        show_sma50 = st.checkbox("SMA (50)", value=True)
    with opt_cols[1]:
        show_sma200 = st.checkbox("SMA (200)", value=True)
    with opt_cols[2]:
        show_ema20 = st.checkbox("EMA (20)", value=False)
    with opt_cols[3]:
        show_bollinger = st.checkbox("Bollinger Bantları", value=False)

    with st.expander(EXPANDER_LABEL):
        st.write(EXPLANATIONS["sma_ema"])
        st.write(EXPLANATIONS["bollinger"])

    sma50_series = sma(close, 50)
    sma200_series = sma(close, 200)
    ema20_series = ema(close, 20) if show_ema20 else None
    bollinger_df = bollinger_bands(close, 20) if show_bollinger else None

    rsi_series = rsi(close, 14)
    macd_df = macd(close)

    fig = build_detail_figure(
        df=df,
        sma50=sma50_series if show_sma50 else None,
        sma200=sma200_series if show_sma200 else None,
        ema20=ema20_series,
        bollinger=bollinger_df,
        rsi_series=rsi_series,
        macd_df=macd_df,
        ticker=ticker,
    )
    st.plotly_chart(fig, width="stretch")

    with st.expander(f"{EXPANDER_LABEL} (RSI)"):
        st.write(EXPLANATIONS["rsi"])
    with st.expander(f"{EXPANDER_LABEL} (MACD)"):
        st.write(EXPLANATIONS["macd"])

    render_teknik_ozet(close, sma50_series, sma200_series, rsi_series, macd_df)


def render_tarama_tab() -> None:
    st.info("Bu sekme bir sonraki aşamada eklenecek.")


def render_karsilastirma_tab() -> None:
    st.info("Bu sekme bir sonraki aşamada eklenecek.")


st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title(APP_TITLE)

tab1, tab2, tab3 = st.tabs([TAB_HISSE_DETAY, TAB_TARAMA, TAB_KARSILASTIRMA])

with tab1:
    render_hisse_detay_tab()

with tab2:
    render_tarama_tab()

with tab3:
    render_karsilastirma_tab()

st.divider()
st.caption(DISCLAIMER)
