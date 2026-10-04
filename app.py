from datetime import date, timedelta

import numpy as np
import pandas as pd
import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from backtest import run_buy_and_hold, run_macd_strategy, run_rsi_strategy, run_sma_cross_strategy
from config import BIST30_TICKERS
from data import (
    DataFetchError,
    get_adjusted_price_history,
    get_multiple_price_histories,
    get_price_history,
    load_all_bist_symbols,
)
from indicators import bollinger_bands, ema, macd, rsi, sma
from signals import (
    describe_golden_death_cross,
    describe_macd_cross,
    describe_price_vs_ma,
    describe_rsi,
    trend_label,
)
from ui_text import (
    APP_TITLE,
    BACKTEST_DISCLAIMER,
    BACKTEST_INSUFFICIENT_SAMPLE,
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
COLOR_NEUTRAL = "#383835"
COLOR_YELLOW = "#c98500"
COLOR_DIV_RED = "#e66767"

HEATMAP_COLS = 6
CATEGORICAL_PALETTE = [COLOR_BLUE, COLOR_ORANGE, COLOR_AQUA, COLOR_YELLOW, COLOR_MAGENTA]


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


def build_equity_curve_figure(results: list) -> go.Figure:
    fig = go.Figure()
    for i, result in enumerate(results):
        fig.add_trace(
            go.Scatter(
                x=result.equity_curve.index,
                y=result.equity_curve.values,
                mode="lines",
                name=result.name,
                line=dict(color=CATEGORICAL_PALETTE[i % len(CATEGORICAL_PALETTE)], width=2),
            )
        )
    fig.add_hline(y=100, line_dash="dash", line_color=COLOR_MUTED)

    fig.update_yaxes(title_text="Getiri (Başlangıç = 100)", showgrid=True, gridcolor=COLOR_GRID, zeroline=False)
    fig.update_xaxes(showgrid=True, gridcolor=COLOR_GRID, zeroline=False)
    fig.update_layout(
        height=420,
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLOR_TEXT),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=10, r=10, t=30, b=10),
    )
    return fig


def build_trade_markers_figure(close, result, ticker: str) -> go.Figure:
    entry_dates = [t.entry_date for t in result.trades]
    entry_prices = [t.entry_price for t in result.trades]
    exit_dates = [t.exit_date for t in result.trades if t.is_closed]
    exit_prices = [t.exit_price for t in result.trades if t.is_closed]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=close.index, y=close.values, mode="lines", name=ticker,
            line=dict(color=COLOR_MUTED, width=1.5),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=entry_dates, y=entry_prices, mode="markers", name="Giriş",
            marker=dict(symbol="triangle-up", size=11, color=COLOR_GOOD),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=exit_dates, y=exit_prices, mode="markers", name="Çıkış",
            marker=dict(symbol="triangle-down", size=11, color=COLOR_CRITICAL),
        )
    )

    fig.update_yaxes(title_text="Fiyat (TL)", showgrid=True, gridcolor=COLOR_GRID, zeroline=False)
    fig.update_xaxes(showgrid=True, gridcolor=COLOR_GRID, zeroline=False)
    fig.update_layout(
        height=380,
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLOR_TEXT),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=10, r=10, t=30, b=10),
    )
    return fig


def render_sinyal_karnesi(ticker: str, start_date, end_date) -> None:
    st.subheader("Sinyal Karnesi")
    st.caption(
        "Seçtiğiniz hissede üç basit teknik sinyalin geçmiş performansı. "
        "Sinyal gün sonunda oluşur, işlem ertesi günün açılışında gerçekleşir."
    )

    cost_pct = st.number_input(
        "İşlem maliyeti (%, her yönde)",
        min_value=0.0, max_value=5.0, value=0.1, step=0.05,
        help="Alış ve satışta ayrı ayrı uygulanan varsayımsal komisyon/maliyet.",
    )

    try:
        adj_df = get_adjusted_price_history(ticker, start_date, end_date)
    except DataFetchError as exc:
        st.error(str(exc))
        return

    if len(adj_df) < 210:
        st.info(
            "Sinyal Karnesi için en az ~210 günlük veri gerekir (200 günlük ortalama "
            "hesaplanabilsin diye). Lütfen tarih aralığını genişletin."
        )
        return

    results = {
        "rsi": run_rsi_strategy(adj_df, cost_pct),
        "macd": run_macd_strategy(adj_df, cost_pct),
        "sma": run_sma_cross_strategy(adj_df, cost_pct),
        "buy_hold": run_buy_and_hold(adj_df, cost_pct),
    }

    summary_rows = []
    for result in results.values():
        summary_rows.append(
            {
                "Strateji": result.name,
                "Toplam Getiri (%)": round(result.total_return_pct, 2),
                "Maks. Düşüş (%)": round(result.max_drawdown_pct, 2),
                "İşlem Sayısı": float(result.num_trades) if result.num_trades is not None else np.nan,
                "Kazanç Oranı (%)": (
                    round(result.win_rate_pct, 1) if result.win_rate_pct is not None else np.nan
                ),
            }
        )
    summary_df = pd.DataFrame(summary_rows)

    st.dataframe(
        summary_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Toplam Getiri (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Maks. Düşüş (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "İşlem Sayısı": st.column_config.NumberColumn(format="%.0f"),
            "Kazanç Oranı (%)": st.column_config.NumberColumn(format="%.1f%%"),
        },
    )

    for key in ("rsi", "macd", "sma"):
        result = results[key]
        if result.num_trades is not None and result.num_trades < 10:
            st.warning(
                BACKTEST_INSUFFICIENT_SAMPLE.format(name=result.name, count=result.num_trades)
            )

    st.markdown("**Getiri Eğrileri Karşılaştırması**")
    equity_fig = build_equity_curve_figure(list(results.values()))
    st.plotly_chart(equity_fig, width="stretch")

    st.markdown("**İşlem Noktaları**")
    strategy_choice = st.selectbox(
        "Hangi stratejinin işlem noktalarını görmek istersiniz?",
        options=["rsi", "macd", "sma"],
        format_func=lambda k: results[k].name,
    )
    trade_fig = build_trade_markers_figure(adj_df["Close"], results[strategy_choice], ticker)
    st.plotly_chart(trade_fig, width="stretch")

    with st.expander(f"{EXPANDER_LABEL} (Sinyal Karnesi)"):
        st.write(EXPLANATIONS["backtest"])

    st.caption(BACKTEST_DISCLAIMER)


def render_hisse_detay_tab() -> None:
    all_stocks = load_all_bist_symbols()
    all_symbols = sorted(all_stocks.keys())
    default_ticker = "THYAO" if "THYAO" in all_stocks else all_symbols[0]

    col_ticker, col_dates = st.columns([1, 2])

    with col_ticker:
        ticker_raw = st.selectbox(
            "Hisse (sembol veya şirket adıyla arayın)",
            options=all_symbols,
            index=all_symbols.index(default_ticker),
            format_func=lambda t: f"{t} — {all_stocks[t]}" if t in all_stocks else f"{t} (listede yok)",
            accept_new_options=True,
            placeholder="Örn. THYAO veya Türk Hava Yolları",
        )
        st.caption("Listede bulamadığınız bir hisse varsa sembolünü yazıp Enter'a basabilirsiniz.")

    if not ticker_raw:
        st.info("Lütfen bir hisse seçin veya sembol girin.")
        return

    ticker = ticker_raw.strip().upper()

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

    render_sinyal_karnesi(ticker, start_date, end_date)


def build_heatmap_figure(tickers: list[str], changes: list[float]):
    n = len(tickers)
    n_rows = (n + HEATMAP_COLS - 1) // HEATMAP_COLS

    z = [[None] * HEATMAP_COLS for _ in range(n_rows)]
    text = [[""] * HEATMAP_COLS for _ in range(n_rows)]

    for idx, (ticker, chg) in enumerate(zip(tickers, changes)):
        r, c = divmod(idx, HEATMAP_COLS)
        z[r][c] = chg
        text[r][c] = f"{ticker}<br>{chg:+.2f}%"

    max_abs = max(2.0, max(abs(c) for c in changes))

    fig = go.Figure(
        go.Heatmap(
            z=z,
            text=text,
            texttemplate="%{text}",
            textfont={"size": 12, "color": "#FFFFFF"},
            colorscale=[[0, COLOR_CRITICAL], [0.5, COLOR_NEUTRAL], [1, COLOR_GOOD]],
            zmid=0,
            zmin=-max_abs,
            zmax=max_abs,
            xgap=4,
            ygap=4,
            showscale=True,
            colorbar=dict(title="%", tickfont=dict(color=COLOR_TEXT)),
            hoverinfo="skip",
        )
    )
    fig.update_yaxes(
        autorange="reversed", showticklabels=False, showgrid=False,
        zeroline=False, showline=False, ticks="",
    )
    fig.update_xaxes(
        showticklabels=False, showgrid=False, zeroline=False,
        showline=False, ticks="",
    )
    fig.update_layout(
        height=110 * n_rows,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLOR_TEXT),
    )
    return fig


def render_tarama_tab() -> None:
    tickers = tuple(BIST30_TICKERS.keys())

    try:
        histories = get_multiple_price_histories(tickers)
    except DataFetchError as exc:
        st.error(str(exc))
        return

    rows = []
    for ticker in tickers:
        df = histories.get(ticker)
        if df is None or len(df) < 2:
            continue

        close = df["Close"]
        last_price = close.iloc[-1]
        prev_price = close.iloc[-2]
        daily_change = (last_price - prev_price) / prev_price * 100
        rsi_value = rsi(close, 14).iloc[-1]
        sma50_value = sma(close, 50).iloc[-1]
        sma200_value = sma(close, 200).iloc[-1]

        rows.append(
            {
                "Hisse": ticker,
                "Şirket": BIST30_TICKERS[ticker],
                "Son Fiyat": round(float(last_price), 2),
                "Günlük Değişim (%)": round(float(daily_change), 2),
                "RSI": round(float(rsi_value), 1) if pd.notna(rsi_value) else None,
                "Trend": trend_label(sma50_value, sma200_value),
            }
        )

    if not rows:
        st.warning("Hiçbir hisse için veri alınamadı.")
        return

    table_df = pd.DataFrame(rows)

    missing_count = len(tickers) - len(rows)
    if missing_count > 0:
        st.caption(f"{missing_count} hisse için veri alınamadı ve tablodan çıkarıldı.")

    st.markdown("**Günlük Değişim Isı Haritası**")
    heatmap_fig = build_heatmap_figure(
        table_df["Hisse"].tolist(), table_df["Günlük Değişim (%)"].tolist()
    )
    st.plotly_chart(heatmap_fig, width="stretch")

    st.markdown("**Filtrele**")
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        trend_options = sorted(table_df["Trend"].unique())
        selected_trends = st.multiselect(
            "Trend durumu", trend_options, default=trend_options
        )
    with filter_col2:
        search = st.text_input("Hisse kodu veya şirket adı ara", "")

    filtered_df = table_df[table_df["Trend"].isin(selected_trends)]
    if search:
        mask = filtered_df["Hisse"].str.contains(
            search, case=False
        ) | filtered_df["Şirket"].str.contains(search, case=False)
        filtered_df = filtered_df[mask]

    st.dataframe(
        filtered_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Son Fiyat": st.column_config.NumberColumn("Son Fiyat", format="%.2f"),
            "Günlük Değişim (%)": st.column_config.NumberColumn(
                "Günlük Değişim (%)", format="%.2f%%"
            ),
            "RSI": st.column_config.NumberColumn("RSI", format="%.1f"),
        },
    )


def build_normalized_return_figure(histories: dict, tickers: list[str]):
    fig = go.Figure()
    for i, ticker in enumerate(tickers):
        close = histories[ticker]["Close"]
        normalized = close / close.iloc[0] * 100
        fig.add_trace(
            go.Scatter(
                x=normalized.index, y=normalized, mode="lines", name=ticker,
                line=dict(color=CATEGORICAL_PALETTE[i % len(CATEGORICAL_PALETTE)], width=2),
            )
        )
    fig.add_hline(y=100, line_dash="dash", line_color=COLOR_MUTED)

    fig.update_yaxes(title_text="Normalize Edilmiş Getiri (Başlangıç = 100)", showgrid=True, gridcolor=COLOR_GRID, zeroline=False)
    fig.update_xaxes(showgrid=True, gridcolor=COLOR_GRID, zeroline=False)
    fig.update_layout(
        height=500,
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLOR_TEXT),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=10, r=10, t=30, b=10),
    )
    return fig


def build_correlation_heatmap_figure(corr_df: pd.DataFrame):
    tickers = corr_df.columns.tolist()
    z = corr_df.values
    text = [[f"{value:.2f}" for value in row] for row in z]

    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=tickers,
            y=tickers,
            text=text,
            texttemplate="%{text}",
            textfont={"size": 12, "color": "#FFFFFF"},
            colorscale=[[0, COLOR_DIV_RED], [0.5, COLOR_NEUTRAL], [1, COLOR_BLUE]],
            zmid=0,
            zmin=-1,
            zmax=1,
            xgap=4,
            ygap=4,
            showscale=True,
            colorbar=dict(title="r", tickfont=dict(color=COLOR_TEXT)),
        )
    )
    fig.update_yaxes(autorange="reversed", tickfont=dict(color=COLOR_TEXT), showgrid=False)
    fig.update_xaxes(tickfont=dict(color=COLOR_TEXT), showgrid=False)
    fig.update_layout(
        height=max(300, 90 * len(tickers)),
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLOR_TEXT),
    )
    return fig


def render_karsilastirma_tab() -> None:
    all_stocks = load_all_bist_symbols()
    all_symbols = sorted(all_stocks.keys())
    default_selection = [t for t in ("AKBNK", "GARAN", "THYAO") if t in all_stocks]

    col_tickers, col_dates = st.columns([2, 1])
    with col_tickers:
        selected_raw = st.multiselect(
            "Hisseler (2-5 adet, sembol veya şirket adıyla arayın)",
            options=all_symbols,
            default=default_selection,
            format_func=lambda t: f"{t} — {all_stocks[t]}" if t in all_stocks else f"{t} (listede yok)",
            max_selections=5,
            accept_new_options=True,
            placeholder="Örn. THYAO veya Türk Hava Yolları",
        )
        st.caption("Listede bulamadığınız bir hisse varsa sembolünü yazıp Enter'a basabilirsiniz.")
        selected = list(dict.fromkeys(t.strip().upper() for t in selected_raw if t.strip()))
    with col_dates:
        today = date.today()
        default_start = today - timedelta(days=365)
        date_range = st.date_input(
            "Tarih aralığı",
            value=(default_start, today),
            min_value=date(2005, 1, 1),
            max_value=today,
            key="karsilastirma_tarih",
        )

    if len(selected) < 2:
        st.info("Karşılaştırmak için en az 2 hisse seçin.")
        return

    if not isinstance(date_range, tuple) or len(date_range) != 2:
        st.info("Lütfen bir başlangıç ve bitiş tarihi seçin.")
        return

    start_date, end_date = date_range
    if start_date >= end_date:
        st.warning("Başlangıç tarihi, bitiş tarihinden önce olmalıdır.")
        return

    histories = {}
    for ticker in selected:
        try:
            histories[ticker] = get_price_history(ticker, start_date, end_date)
        except DataFetchError as exc:
            st.error(str(exc))

    valid_tickers = [t for t in selected if t in histories]
    if len(valid_tickers) < 2:
        st.warning("Karşılaştırma için yeterli veri alınamadı.")
        return

    st.markdown("**Normalize Edilmiş Getiri (Başlangıç = 100)**")
    return_fig = build_normalized_return_figure(histories, valid_tickers)
    st.plotly_chart(return_fig, width="stretch")

    with st.expander(f"{EXPANDER_LABEL} (Normalize Getiri)"):
        st.write(EXPLANATIONS["normalized_return"])

    st.markdown("**Korelasyon Isı Haritası**")

    returns_df = pd.DataFrame(
        {t: histories[t]["Close"].pct_change() for t in valid_tickers}
    ).dropna()

    if len(returns_df) < 2:
        st.info("Korelasyon hesaplamak için yeterli ortak veri yok.")
    else:
        corr_df = returns_df.corr()
        corr_fig = build_correlation_heatmap_figure(corr_df)
        st.plotly_chart(corr_fig, width="stretch")

    with st.expander(f"{EXPANDER_LABEL} (Korelasyon)"):
        st.write(EXPLANATIONS["correlation"])


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
