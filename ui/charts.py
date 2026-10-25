"""Plotly grafik oluşturucuları — tüm grafikler aynı temel düzeni paylaşır.

Mobil kararlar:
- Lejant Plotly'nin içinde değil, grafiğin ÜSTÜNDE HTML olarak çizilir (ui.components.legend);
  böylece dar ekranda satır kırar ve grafiğin üzerine taşmaz.
- Telefonda eksenler sabit (fixedrange) ve dragmode kapalıdır: grafik üzerinde parmakla
  kaydırma sayfayı kaydırır, grafiği yakınlaştırmaz. Dokununca değer etiketi yine görünür.
- `separators=",."` ile eksen ve etiketlerdeki sayılar Türkçe biçimdedir (1.234,56).
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from ui import theme as t
from ui.format import fmt_num
from ui.viewport import DESKTOP, MOBILE, TABLET
from ui_text import (
    BT_ENTRY,
    BT_EXIT,
    CHART_PANEL_MACD,
    CHART_PANEL_RSI,
    CHART_PANEL_VOLUME,
    CHART_PRICE_AXIS,
    CHART_SERIES_BOLLINGER,
    CHART_SERIES_EMA20,
    CHART_SERIES_HISTOGRAM,
    CHART_SERIES_MACD,
    CHART_SERIES_SIGNAL,
    CHART_SERIES_SMA200,
    CHART_SERIES_SMA50,
)

DETAIL_HEIGHT = {MOBILE: 620, TABLET: 700, DESKTOP: 760}
LINE_HEIGHT = {MOBILE: 300, TABLET: 360, DESKTOP: 420}
TRADES_HEIGHT = {MOBILE: 280, TABLET: 340, DESKTOP: 380}

DAY_MS = 86_400_000
WEEKEND_BREAK = [dict(bounds=["sat", "mon"])]

# Strateji/seri renkleri sabit sıradadır (renk varlığı takip eder, sıralamayı değil).
STRATEGY_COLORS = {
    "rsi": t.SERIES[0],
    "macd": t.SERIES[1],
    "sma": t.SERIES[2],
    "buy_hold": t.TEXT_2,
}
OVERLAY_COLORS = {
    "sma50": t.SERIES[0],
    "sma200": t.SERIES[1],
    "ema20": t.SERIES[2],
    "bollinger": t.BOLLINGER,
    # MACD paneli ayrı olsa da aynı lejantta durduğu için fiyat ortalamalarıyla renk paylaşmaz
    "macd": t.MACD_LINE,
    "signal": t.SERIES[3],
}


def plotly_config(device: str) -> dict:
    if device != DESKTOP:
        return {"displayModeBar": False, "scrollZoom": False, "displaylogo": False, "responsive": True}
    return {
        "displayModeBar": "hover",
        "displaylogo": False,
        "scrollZoom": False,
        "responsive": True,
        "modeBarButtonsToRemove": [
            "select2d", "lasso2d", "autoScale2d", "zoomIn2d", "zoomOut2d", "toggleSpikelines",
        ],
    }


def show_chart(fig: go.Figure, device: str, key: str | None = None) -> None:
    st.plotly_chart(fig, width="stretch", theme=None, config=plotly_config(device), key=key)


def _base_layout(fig: go.Figure, device: str, height: int, hovermode: str = "x unified") -> None:
    mobile = device == MOBILE
    touch = device != DESKTOP  # telefon ve tablette parmakla kaydırma sayfayı kaydırmalı
    fig.update_layout(
        height=height,
        margin=dict(l=4, r=4, t=8, b=4),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=t.FONT_FAMILY, size=11 if mobile else 12, color=t.TEXT_2),
        separators=",.",
        showlegend=False,
        hovermode=hovermode,
        dragmode=False if touch else "zoom",
        hoverlabel=dict(
            bgcolor=t.SURFACE_2,
            bordercolor=t.BORDER_STRONG,
            font=dict(family=t.FONT_FAMILY, size=11 if mobile else 12, color=t.TEXT_1),
            namelength=-1,
        ),
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor=t.BORDER,
        tickfont=dict(size=10 if mobile else 11, color=t.TEXT_3),
        fixedrange=touch,
        automargin=True,
        showspikes=not touch,
        spikecolor=t.BORDER_STRONG,
        spikethickness=1,
        spikedash="dot",
        spikemode="across",
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=t.GRID,
        zeroline=False,
        side="right",
        tickfont=dict(size=10 if mobile else 11, color=t.TEXT_3),
        fixedrange=touch,
        automargin=True,
        nticks=5 if mobile else 7,
    )


def _date_axes(fig: go.Figure) -> None:
    fig.update_xaxes(
        rangebreaks=WEEKEND_BREAK,
        hoverformat="%d.%m.%Y",
        tickformatstops=[
            dict(dtickrange=[None, "M1"], value="%d.%m"),
            dict(dtickrange=["M1", "M12"], value="%m.%Y"),
            dict(dtickrange=["M12", None], value="%Y"),
        ],
    )


def _panel_label(fig: go.Figure, row: int, text: str) -> None:
    axis = "" if row == 1 else str(row)
    fig.add_annotation(
        xref=f"x{axis} domain", yref=f"y{axis} domain", x=0, y=1,
        xanchor="left", yanchor="top", showarrow=False,
        text=text, font=dict(size=10, color=t.TEXT_3),
        bgcolor="rgba(11,14,20,0.6)", borderpad=2,
    )


def _ohlc_hover_text(df: pd.DataFrame) -> list[str]:
    return [
        f"A {fmt_num(o)} · Y {fmt_num(h)} · D {fmt_num(lo)} · K {fmt_num(c)}"
        for o, h, lo, c in zip(df["Open"], df["High"], df["Low"], df["Close"])
    ]


def _line(x, y, name: str, color: str, width: float = 1.6, fmt: str = ",.2f", **kwargs) -> go.Scatter:
    return go.Scatter(
        x=x, y=y, mode="lines", name=name,
        line=dict(color=color, width=width),
        hovertemplate=f"{name}: %{{y:{fmt}}}<extra></extra>",
        **kwargs,
    )


def build_detail_figure(df: pd.DataFrame, overlays: dict, rsi_series: pd.Series,
                        macd_df: pd.DataFrame, currency_label: str, device: str) -> go.Figure:
    """Mum + hacim + RSI + MACD. `df` ve seriler, gösterilecek pencereye zaten kırpılmış olmalı.

    overlays: {"sma50": Series|None, "sma200": ..., "ema20": ..., "bollinger": DataFrame|None}
    """
    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True,
        vertical_spacing=0.035,
        row_heights=[0.55, 0.12, 0.15, 0.18],
    )
    x = df.index

    bollinger = overlays.get("bollinger")
    if bollinger is not None:
        fig.add_trace(_line(x, bollinger["upper"], f"{CHART_SERIES_BOLLINGER} üst", OVERLAY_COLORS["bollinger"], 1), row=1, col=1)
        fig.add_trace(
            _line(x, bollinger["lower"], f"{CHART_SERIES_BOLLINGER} alt", OVERLAY_COLORS["bollinger"], 1,
                  fill="tonexty", fillcolor="rgba(144,133,233,0.08)"),
            row=1, col=1,
        )

    fig.add_trace(
        go.Candlestick(
            x=x, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
            name="Fiyat",
            increasing=dict(line=dict(color=t.UP, width=1), fillcolor=t.UP),
            decreasing=dict(line=dict(color=t.DOWN, width=1), fillcolor=t.DOWN),
            whiskerwidth=0,
            text=_ohlc_hover_text(df),
            hoverinfo="text",
        ),
        row=1, col=1,
    )

    for key, name in (("sma50", CHART_SERIES_SMA50), ("sma200", CHART_SERIES_SMA200), ("ema20", CHART_SERIES_EMA20)):
        series = overlays.get(key)
        if series is not None:
            fig.add_trace(_line(x, series, name, OVERLAY_COLORS[key]), row=1, col=1)

    volume_colors = np.where(df["Close"] >= df["Open"], t.UP, t.DOWN)
    fig.add_trace(
        go.Bar(x=x, y=df["Volume"], name=CHART_PANEL_VOLUME, marker_color=volume_colors,
               marker_line_width=0, opacity=0.55, hovertemplate=f"{CHART_PANEL_VOLUME}: %{{y:,.0f}}<extra></extra>"),
        row=2, col=1,
    )

    fig.add_hrect(y0=30, y1=70, fillcolor="rgba(110,168,254,0.05)", line_width=0, row=3, col=1)
    for level in (30, 70):
        fig.add_hline(y=level, line=dict(color="rgba(163,170,184,0.35)", width=1, dash="dash"), row=3, col=1)
    fig.add_trace(_line(x, rsi_series, "RSI", t.SERIES[0], fmt=".1f"), row=3, col=1)

    histogram_colors = np.where(macd_df["histogram"] >= 0, t.UP, t.DOWN)
    fig.add_trace(
        go.Bar(x=x, y=macd_df["histogram"], name=CHART_SERIES_HISTOGRAM, marker_color=histogram_colors,
               marker_line_width=0, opacity=0.5, hovertemplate=f"{CHART_SERIES_HISTOGRAM}: %{{y:,.2f}}<extra></extra>"),
        row=4, col=1,
    )
    fig.add_trace(_line(x, macd_df["macd"], CHART_SERIES_MACD, OVERLAY_COLORS["macd"], 1.4), row=4, col=1)
    fig.add_trace(_line(x, macd_df["signal"], CHART_SERIES_SIGNAL, OVERLAY_COLORS["signal"], 1.4), row=4, col=1)

    _base_layout(fig, device, DETAIL_HEIGHT[device])
    _date_axes(fig)
    fig.update_layout(bargap=0.15)
    fig.update_xaxes(rangeslider_visible=False)
    fig.update_xaxes(showticklabels=False, showline=False, row=1, col=1)
    fig.update_xaxes(showticklabels=False, showline=False, row=2, col=1)
    fig.update_xaxes(showticklabels=False, showline=False, row=3, col=1)
    fig.update_yaxes(tickformat=",.0f" if df["Close"].max() >= 100 else ",.2f", row=1, col=1)
    fig.update_yaxes(tickformat="~s", nticks=3, row=2, col=1)
    fig.update_yaxes(range=[0, 100], tickvals=[30, 70], row=3, col=1)
    fig.update_yaxes(nticks=4, row=4, col=1)

    _panel_label(fig, 1, CHART_PRICE_AXIS.format(currency=currency_label))
    _panel_label(fig, 2, CHART_PANEL_VOLUME)
    _panel_label(fig, 3, CHART_PANEL_RSI)
    _panel_label(fig, 4, CHART_PANEL_MACD)
    return fig


def build_equity_curve_figure(results: dict, device: str) -> go.Figure:
    fig = go.Figure()
    for key, result in results.items():
        is_benchmark = key == "buy_hold"
        fig.add_trace(
            _line(
                result.equity_curve.index, result.equity_curve.values, result.name,
                STRATEGY_COLORS[key], 1.4 if is_benchmark else 1.8, fmt=",.1f",
            )
        )
        if is_benchmark:
            fig.data[-1].line.dash = "dot"
    fig.add_hline(y=100, line=dict(color="rgba(163,170,184,0.35)", width=1, dash="dash"))
    _base_layout(fig, device, LINE_HEIGHT[device])
    _date_axes(fig)
    return fig


def build_trade_markers_figure(close: pd.Series, result, device: str) -> go.Figure:
    closed = [trade for trade in result.trades if trade.is_closed]
    marker_size = 9 if device == MOBILE else 11

    fig = go.Figure()
    fig.add_trace(_line(close.index, close.values, "Fiyat", t.MUTED_LINE, 1.3))
    fig.add_trace(
        go.Scatter(
            x=[trade.entry_date for trade in result.trades],
            y=[trade.entry_price for trade in result.trades],
            mode="markers", name=BT_ENTRY,
            marker=dict(symbol="triangle-up", size=marker_size, color=t.UP, line=dict(color=t.BG, width=1)),
            hovertemplate=f"{BT_ENTRY}: %{{y:,.2f}}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[trade.exit_date for trade in closed],
            y=[trade.exit_price for trade in closed],
            mode="markers", name=BT_EXIT,
            marker=dict(symbol="triangle-down", size=marker_size, color=t.DOWN, line=dict(color=t.BG, width=1)),
            hovertemplate=f"{BT_EXIT}: %{{y:,.2f}}<extra></extra>",
        )
    )
    _base_layout(fig, device, TRADES_HEIGHT[device])
    _date_axes(fig)
    return fig


def build_normalized_return_figure(histories: dict, tickers: list[str], device: str) -> go.Figure:
    fig = go.Figure()
    for i, ticker in enumerate(tickers):
        close = histories[ticker]["Close"]
        normalized = close / close.iloc[0] * 100
        fig.add_trace(_line(normalized.index, normalized, ticker, t.SERIES[i % len(t.SERIES)], 1.8, fmt=",.1f"))
    fig.add_hline(y=100, line=dict(color="rgba(163,170,184,0.35)", width=1, dash="dash"))
    _base_layout(fig, device, LINE_HEIGHT[device] + (20 if device != MOBILE else 0))
    _date_axes(fig)
    return fig


def build_correlation_heatmap_figure(corr_df: pd.DataFrame, device: str) -> go.Figure:
    tickers = corr_df.columns.tolist()
    z = corr_df.values
    text = [[fmt_num(value, 2) for value in row] for row in z]
    mobile = device == MOBILE

    fig = go.Figure(
        go.Heatmap(
            z=z, x=tickers, y=tickers,
            text=text, texttemplate="%{text}",
            textfont=dict(size=13 if mobile else 14, color="#FFFFFF", family=t.FONT_FAMILY),
            colorscale=[[0, t.DIV_NEG], [0.5, t.HEAT_NEUTRAL], [1, t.DIV_POS]],
            zmid=0, zmin=-1, zmax=1,
            xgap=3, ygap=3,
            showscale=not mobile,
            colorbar=dict(title=dict(text="r"), tickfont=dict(color=t.TEXT_3, size=11), thickness=10, outlinewidth=0),
            hovertemplate="%{y} · %{x}: %{text}<extra></extra>",
        )
    )
    _base_layout(fig, device, (64 if mobile else 84) * len(tickers) + 40, hovermode="closest")
    fig.update_yaxes(autorange="reversed", showgrid=False, side="left", nticks=None, ticks="",
                     tickfont=dict(size=11 if mobile else 12, color=t.TEXT_2))
    fig.update_xaxes(showgrid=False, showline=False, side="bottom", showspikes=False, ticks="",
                     tickfont=dict(size=11 if mobile else 12, color=t.TEXT_2))
    return fig
