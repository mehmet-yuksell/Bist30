"""Hisse Detay sekmesi: hero, mum grafiği, alım sistemi (skor kırılımı), Teknik Özet, Sinyal Karnesi."""

from datetime import timedelta

import pandas as pd
import streamlit as st

import evaluation as ev
import feed
import market
import motor_veri
import panel_veri as pv
import tarayici_motor as motor
from backtest import run_buy_and_hold, run_macd_strategy, run_rsi_strategy, run_sma_cross_strategy
from data import (
    DataFetchError,
    get_adjusted_price_history,
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
from ui import charts, kalite_ui
from ui import theme as t
from ui.components import (
    badge,
    callout,
    error_state,
    hero,
    legend,
    metric_html,
    section_title,
    score_card,
    skeleton_html,
    strategy_cards,
    subtitle,
    summary_rows,
)
from ui.controls import date_range_popover, display_name, symbol_formatter, validate_date_range
from ui.format import arrow, direction, fmt_compact, fmt_date, fmt_num, fmt_pct, fmt_price
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
    BL_CAPTION,
    BL_CAPTION_ORTA,
    BL_COL_FORWARD_ORTA,
    BL_GATES_ORTA,
    BL_HISTORY_CAPTION_ORTA,
    BL_LAST_SELL,
    BL_NO_SELL,
    BL_SELL_PRESSURE,
    BL_STATUS_NONE_ORTA,
    BL_STATUS_RECENT_ORTA,
    BL_STATUS_TODAY_ORTA,
    BL_COL_CLOSE,
    BL_COL_DATE,
    BL_COL_FORWARD,
    BL_COL_SCORE,
    BL_COL_STOP,
    BL_COL_TARGET,
    BL_GATES,
    BL_HISTORY_CAPTION,
    BL_HISTORY_EMPTY,
    BL_HISTORY_SUMMARY,
    BL_HISTORY_TITLE,
    BL_ITEM_LABELS,
    BL_SCORE_LABEL,
    BL_SIGNAL_LEVELS,
    BL_STATUS_NONE,
    BL_STATUS_NO_DATA,
    BL_STATUS_RECENT,
    BL_STATUS_TODAY,
    BL_STATUS_TODAY_PROVISIONAL,
    BL_TITLE,
    BT_CAPTION,
    BT_COST_HELP,
    BT_COST_LABEL,
    BT_ENTRY,
    BT_EQUITY_TITLE,
    BT_EXPANDER,
    BT_EXIT,
    BT_MAX_DRAWDOWN,
    BT_NEED_MORE_DATA,
    BT_NUM_TRADES,
    BT_PRICE_LEGEND,
    BT_SAMPLE_TITLE,
    BT_TAG_BENCHMARK,
    BT_TAG_BEST,
    BT_TAG_WORST,
    BT_TOTAL_RETURN,
    BT_TRADES_PICK,
    BT_TRADES_TITLE,
    BT_WIN_RATE,
    CHART_BL_SIGNAL,
    CHART_FIRSAT,
    CHART_SELL,
    CHART_SERIES_BL_FAST,
    CHART_SERIES_BL_SLOW,
    CHART_SERIES_BOLLINGER,
    CHART_SERIES_EMA20,
    CHART_SERIES_MACD,
    CHART_SERIES_SIGNAL,
    CHART_SERIES_SMA200,
    CHART_SERIES_SMA50,
    EXPLAIN_INDICATORS,
    EXPLANATIONS,
    HD_CURRENCY_LABEL,
    HD_EMPTY_BODY,
    HD_EMPTY_TITLE,
    HD_FX_ALIGN_FAILED,
    HD_NO_INDEX,
    HD_WEEKLY_INDICATORS,
    HS_GENERAL,
    HS_HIST_AXIS,
    HS_HIST_TITLE,
    HS_NO_TARGETS,
    HS_OWN,
    HS_TITLE,
    HD_INDICATOR_BLUETSMAN,
    HD_INDICATOR_OPTIONS,
    HD_INDICATORS_LABEL,
    HD_TICKER_LABEL,
    HD_VIEW_LABEL,
    HD_VIEW_WINDOWS,
    HERO_AS_OF,
    LIVE_STALE,
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
    VADE_BIRIM,
    VADE_BUGUN,
    VADE_ONCE,
    VADE_WEEK_NOTE,
)

CURRENCY_KEY = "hisse_detay_currency"
EXPANDER_ICON = ":material/help_outline:"
MIN_BACKTEST_ROWS = 210
MACD_CROSS_LOOKBACK = 5  # signals.describe_macd_cross ile aynı
SMA_CROSS_LOOKBACK = 10  # signals.describe_golden_death_cross ile aynı
SIGNAL_LOOKBACK = 10  # BIST 100 Tarama ile aynı
MIN_HISSE_SINYALI = 15  # bundan azsa hisse yerine genel istatistik
ENDEKS = "XU100"
HISTORY_ROWS = 10


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


# ---------------------------------------------------------------------------
# Bluetsman alım sistemi
# ---------------------------------------------------------------------------

def _render_signal_history(sonuc: pd.DataFrame, vade: str) -> None:
    history = motor_veri.al_gecmisi(sonuc, sutun=pv.ALIM_SUTUNU)
    col_forward = BL_COL_FORWARD if vade == pv.KISA else BL_COL_FORWARD_ORTA
    with st.expander(BL_HISTORY_TITLE, icon=":material/history:"):
        if history.empty:
            callout("empty", None, BL_HISTORY_EMPTY)
            return
        done = history["forward_return"].dropna()
        st.markdown(BL_HISTORY_SUMMARY.format(
            count=len(history), up=int((done > 0).sum()), done=len(done),
            avg=fmt_pct(done.mean()) if len(done) else "—",
        ))
        recent = history.iloc[:HISTORY_ROWS]
        forward = recent["forward_return"].to_numpy()
        # Değerler metin olarak verilir: Streamlit boş değerde Styler'ın na_rep'ini yok sayıp
        # "None" yazıyor. Renk yine sayısal değerden hesaplanır.
        table = pd.DataFrame({
            BL_COL_DATE: [fmt_date(d) for d in recent.index],
            BL_COL_SCORE: recent["score"].round().astype(int).to_numpy(),
            BL_COL_CLOSE: [fmt_num(v, 2) for v in recent["close"]],
            BL_COL_STOP: [fmt_num(v, 2) for v in recent["stop"]],
            BL_COL_TARGET: [fmt_num(v, 2) for v in recent["target"]],
            col_forward: ["—" if pd.isna(v) else f"{arrow(v)} {fmt_pct(v)}" for v in forward],
        })
        forward_colors = [
            f"color: {({'up': t.UP, 'down': t.DOWN_TEXT}).get(direction(v), t.TEXT_3)}; font-weight: 600"
            for v in forward
        ]

        st.dataframe(
            table.style.apply(lambda _: forward_colors, subset=[col_forward]),
            hide_index=True, width="stretch",
        )
        st.caption(BL_HISTORY_CAPTION if vade == pv.KISA else BL_HISTORY_CAPTION_ORTA)


def _mark(ok: bool) -> str:
    return "✓" if ok else "✗"


def _skor_kalemleri(df_tl: pd.DataFrame, vade: str) -> pd.Series:
    """Son barın alım skoru kalemleri (orta vadede haftalık bar; motor.hisse_analiz ile aynı girdi)."""
    girdi = motor_veri.motor_girdisi(df_tl)
    if vade == pv.KISA:
        return motor.alim_skor_kalemleri(girdi, motor.KISA_VADE).iloc[-1]
    return motor.alim_skor_kalemleri(motor.haftaliga_cevir(girdi), motor.ORTA_VADE).iloc[-1]


def _kapilar(df_tl: pd.DataFrame, sonuc: pd.DataFrame, kalemler: pd.Series, vade: str, score: float) -> str:
    """Alım sinyali için gereken koşulların bugünkü durumu (✓/✗)."""
    ayar = pv.VADE_AYARI[vade]
    ortak = {"cross": _mark(kalemler["kesisim"] > 0), "price": _mark(kalemler["fiyat_ema"] > 0),
             "min_score": ayar.min_skor, "score": _mark(score >= ayar.min_skor)}
    if vade == pv.KISA:
        girdi = motor_veri.motor_girdisi(df_tl)
        weekly_up = bool(motor.haftalik_trend_gunluge(girdi, ayar.trend_ema).iloc[-1])
        return BL_GATES.format(weekly=_mark(weekly_up), **ortak)
    last = sonuc.iloc[-1]
    trend = bool(sonuc["Close"].iloc[-1] > motor.ema(sonuc["Close"], ayar.trend_ema).iloc[-1])
    return BL_GATES_ORTA.format(trend=_mark(trend), f1=_mark(bool(last.get("F_piyasa", True))),
                                f5=_mark(bool(last.get("F_uzun_trend", True))), f8=_mark(bool(last.get("F_tavan", True))),
                                **ortak)


def _satis_satiri(sonuc: pd.DataFrame, vade: str) -> str:
    ayar = pv.VADE_AYARI[vade]
    baski = BL_SELL_PRESSURE.format(skor=fmt_num(sonuc["Satis_skor"].iloc[-1], 0),
                                    kar=ayar.kar_al_min, sat=ayar.sat_min)
    son = pv.son_satis(sonuc, SIGNAL_LOOKBACK)
    if son:
        once = VADE_BUGUN[vade] if son["once"] == 0 else VADE_ONCE[vade].format(days=son["once"])
        return f"{baski} · {BL_LAST_SELL.format(ad=son['ad'], once=once.lower())}"
    return f"{baski} · {BL_NO_SELL.format(n=SIGNAL_LOOKBACK)}"


def _render_alim_sistemi(df_tl: pd.DataFrame, sonuc: pd.DataFrame | None, vade: str, hafta_yarim: bool,
                         device: str) -> None:
    section_title(BL_TITLE, BL_CAPTION if vade == pv.KISA else BL_CAPTION_ORTA)
    if sonuc is None:
        callout("info", None, BL_STATUS_NO_DATA)
        return

    last = sonuc.iloc[-1]
    score = float(last["Alim_skor"])
    signal = motor_veri.son_al(sonuc, SIGNAL_LOOKBACK, sutun=pv.ALIM_SUTUNU)
    gun_kesin_degil = market.provisional(market.now(), df_tl.index[-1].date())
    if signal and signal["once"] == 0:
        if vade == pv.ORTA and hafta_yarim:
            title = BL_STATUS_TODAY_ORTA.format(score=round(signal["skor"]))
        else:
            template = BL_STATUS_TODAY_PROVISIONAL if gun_kesin_degil else BL_STATUS_TODAY
            title = template.format(score=round(signal["skor"]))
    elif signal:
        template = BL_STATUS_RECENT if vade == pv.KISA else BL_STATUS_RECENT_ORTA
        title = template.format(days=signal["once"], date=fmt_date(signal["tarih"]), score=round(signal["skor"]))
    else:
        title = (BL_STATUS_NONE if vade == pv.KISA else BL_STATUS_NONE_ORTA).format(days=SIGNAL_LOOKBACK)

    kalemler = _skor_kalemleri(df_tl, vade)
    levels = BL_SIGNAL_LEVELS.format(stop=fmt_num(signal["stop"], 2), target=fmt_num(signal["hedef"], 2)) if signal else ""
    kq = (kalite_ui.ozet(signal["skor"], vade, True if vade == pv.ORTA else None) if signal
          else {"label": "", "stats": None})
    kalite_satiri = " · ".join(x for x in (kq["label"], kq["stats"]) if x)
    score_card(
        title=title,
        subtitle_lines=[_kapilar(df_tl, sonuc, kalemler, vade, score), _satis_satiri(sonuc, vade), levels, kalite_satiri],
        score=score,
        score_label=BL_SCORE_LABEL,
        items=[(BL_ITEM_LABELS[k], float(kalemler[k]), m) for k, m in motor.ALIM_KALEMLERI.items()],
    )
    _render_signal_history(sonuc, vade)
    _render_hisse_istatistigi(sonuc, vade, device)


def _render_hisse_istatistigi(sonuc: pd.DataFrame, vade: str, device: str) -> None:
    """Bu hissenin alım sinyallerinin sonucu ve hedefe ulaşma süresi histogramı.

    Değerlendirme raporla aynı kurallardır (ertesi bar açılışı giriş, stop/hedef/zaman aşımı);
    hissede 15'ten az tamamlanmış sinyal varsa BIST 100 genelinin istatistiği gösterilir.
    """
    timeout, ilk_bar = (20, motor_veri.MIN_BARS) if vade == pv.KISA else (12, 52)
    trades = ev.islemler(sonuc, sonuc[pv.ALIM_SUTUNU], sonuc["Stop"], sonuc["Hedef"],
                         ev.Kurallar(timeout=timeout), ilk_bar=ilk_bar)
    kendi = pv.islem_istatistigi(trades)
    subtitle(HS_TITLE)
    if kendi["sinyal"] >= MIN_HISSE_SINYALI:
        st.caption(HS_OWN.format(n=kendi["sinyal"], hit=fmt_num(kendi["hedef_pct"], 0),
                                 stop=fmt_num(kendi["stop_pct"], 0), r=fmt_num(kendi["beklenen_r"], 2)))
        sayilar = pd.Series(kendi["hedef_gunleri"]).value_counts().to_dict()
    else:
        genel = kalite_ui.kalibrasyon().get("genel", {}).get(vade, {})
        if not genel.get("sinyal"):
            return
        st.caption(HS_GENERAL.format(n=kendi["sinyal"], m=genel["sinyal"], hit=fmt_num(genel["hedef_pct"], 0),
                                     stop=fmt_num(genel["stop_pct"], 0), r=fmt_num(genel["beklenen_r"], 2)))
        sayilar = {int(k): v for k, v in genel.get("hedef_gunleri", {}).items()}
    if not sayilar:
        callout("empty", None, HS_NO_TARGETS)
        return
    st.caption(HS_HIST_TITLE[vade])
    charts.show_chart(charts.build_histogram_figure({int(k): int(v) for k, v in sayilar.items()},
                                                    HS_HIST_AXIS.format(birim=VADE_BIRIM[vade]), device),
                      device, key="hd_hist")


def _render_explanations(currency: str) -> None:
    """Tüm gösterge açıklamaları tek açılır kutuda (eskiden her gösterge için ayrı kutu vardı)."""
    with st.expander(EXPLAIN_INDICATORS, icon=EXPANDER_ICON):
        st.markdown(f"**Bluetsman alım sistemi** — {EXPLANATIONS['bluetsman']}")
        st.markdown(f"**Ortalamalar** — {EXPLANATIONS['sma_ema']}")
        st.markdown(f"**Bollinger Bantları** — {EXPLANATIONS['bollinger']}")
        st.markdown(f"**RSI** — {EXPLANATIONS['rsi']}")
        st.markdown(f"**MACD** — {EXPLANATIONS['macd']}")
        st.markdown(f"**Altın / ölüm kesişimi** — {EXPLANATIONS['golden_death_cross']}")
        if currency == "USD":
            st.markdown(f"**Dolar bazlı görünüm** — {EXPLANATIONS['usd_view']}")


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
    # Gelişmiş bölüm, varsayılan kapalı. Streamlit iç içe açılır kutuya izin vermediği için
    # içindeki açıklama düz metin olarak gösterilir.
    with st.expander(BT_EXPANDER, icon=":material/science:"):
        _render_sinyal_karnesi_body(ticker, start_date, end_date, device)


def _render_sinyal_karnesi_body(ticker: str, start_date, end_date, device: str) -> None:
    st.caption(BT_CAPTION)

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

    st.caption(EXPLANATIONS["backtest"])
    st.caption(BACKTEST_DISCLAIMER)


# ---------------------------------------------------------------------------
# Sekme
# ---------------------------------------------------------------------------

# Seans boyunca 15 dakikada bir yalnızca bu sekme yeniden çalışır (seçimler korunur).
@st.fragment(run_every=timedelta(minutes=market.REFRESH_MINUTES))
def render(device: str, ctx: dict) -> None:
    vade = ctx.get("vade", pv.KISA)
    all_stocks = load_all_bist_symbols()
    all_symbols = sorted(all_stocks.keys())
    default_ticker = "THYAO" if "THYAO" in all_stocks else all_symbols[0]

    with st.container(horizontal=True, vertical_alignment="bottom", gap="small", key="hd_controls"):
        ticker_raw = st.selectbox(
            HD_TICKER_LABEL,
            options=all_symbols,
            index=all_symbols.index(default_ticker),
            format_func=symbol_formatter(all_stocks),
            placeholder=SYMBOL_PLACEHOLDER,
            key="hd_ticker",
            width="stretch",
        )
        date_range = date_range_popover("hd_dates", default_days=3 * 365)
    st.caption(SYMBOL_HELP.format(count=len(all_symbols)))

    if not ticker_raw or not ticker_raw.strip():
        callout("empty", HD_EMPTY_TITLE, HD_EMPTY_BODY.format(count=len(all_symbols)))
        return
    ticker = ticker_raw.strip().upper()

    dates = validate_date_range(date_range)
    if dates is None:
        return
    start_date, end_date = dates

    loading = st.empty()
    loading.html(skeleton_html("detail"))
    try:
        data = feed.single(ticker, start_date, end_date)
    except DataFetchError as exc:
        loading.empty()
        error_state(str(exc), key="hd_retry")
        return
    loading.empty()
    df = data.data
    ctx["last_dates"].append(df.index[-1])
    if data.stale:
        callout("warn", None, LIVE_STALE.format(minutes=data.age_minutes()))

    # Alım sistemi her zaman TL ve temettü düzeltmeli fiyatla hesaplanır (motor_veri). Orta vadenin
    # piyasa filtresi XU100 ister; endeks alınamazsa orta vade sinyalleri gösterilemez.
    df_tl = df
    endeks = None
    try:
        endeks = pv.endeks_girdisi(feed.single(ENDEKS, start_date, end_date).data)
    except DataFetchError:
        if vade == pv.ORTA:
            callout("warn", None, HD_NO_INDEX)
    sonuc = pv.analiz(df_tl, vade, endeks) if (vade == pv.KISA or endeks is not None) else None
    fs = pv.firsat_analizi(df_tl, endeks) if vade == pv.KISA else None
    hafta_yarim = vade == pv.ORTA and sonuc is not None and not pv.hafta_tamamlandi(df_tl.index[-1], sonuc.index[-1])

    # Para birimi anahtarı grafik araç çubuğunda durur; hero ondan önce çizildiği için
    # seçili değer oturum durumundan okunur (anahtara tıklamak sayfayı yeniden çalıştırır).
    currency = st.session_state.get(CURRENCY_KEY) or "TL"
    currency_label = "TL"
    if currency == "USD":
        df, currency_label = _convert_to_usd(df, start_date, end_date)

    # Hero ve Teknik Özet günlük; grafik orta vadede haftalık mumlardır.
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
            default=[HD_INDICATOR_BLUETSMAN], key="hd_indicators",
        ) or []

    grafik = df if vade == pv.KISA else motor.haftaliga_cevir(df[["Open", "High", "Low", "Close", "Volume"]])
    if vade == pv.ORTA:
        callout("info", None, HD_WEEKLY_INDICATORS + (" " + VADE_WEEK_NOTE if hafta_yarim else ""))
    g_close = grafik["Close"]
    ayar = pv.VADE_AYARI[vade]
    mask = _window_mask(grafik.index, view)
    show_bluetsman = HD_INDICATOR_BLUETSMAN in indicators
    overlays = {
        "sma50": sma(g_close, 50)[mask] if "SMA 50" in indicators else None,
        "sma200": sma(g_close, 200)[mask] if "SMA 200" in indicators else None,
        "ema20": ema(g_close, 20)[mask] if "EMA 20" in indicators else None,
        "bollinger": bollinger_bands(g_close, 20)[mask] if "Bollinger" in indicators else None,
        # Dolar görünümünde EMA'lar dolar fiyatından çizilir; sinyal günleri TL hesabından gelir.
        "bl_fast": ema(g_close, ayar.hizli_ema)[mask] if show_bluetsman else None,
        "bl_slow": ema(g_close, ayar.yavas_ema)[mask] if show_bluetsman else None,
    }
    signal_scores = sell_points = firsat_points = None
    if show_bluetsman and sonuc is not None:
        visible = sonuc.reindex(grafik.index)[mask]
        signal_scores = visible.loc[visible[pv.ALIM_SUTUNU].eq(True), "Alim_skor"]
        satis = pd.Series(None, index=visible.index, dtype=object)
        for sutun, ad in reversed(pv.SATIS_TURLERI):  # öncelikli tür en son yazılır (SAT > KAR AL > ÇIK)
            satis[visible[sutun].eq(True)] = ad
        sell_points = satis.dropna()
    if show_bluetsman and fs is not None:
        gorunen = fs.reindex(grafik.index)[mask]
        firsat_points = gorunen.index[gorunen["FIRSAT"].eq(True)]
    legend_items = [
        (name, charts.OVERLAY_COLORS[key], "line")
        for key, name in (
            ("bl_fast", CHART_SERIES_BL_FAST if vade == pv.KISA else f"EMA {ayar.hizli_ema}"),
            ("bl_slow", CHART_SERIES_BL_SLOW if vade == pv.KISA else f"EMA {ayar.yavas_ema}"),
            ("sma50", CHART_SERIES_SMA50), ("sma200", CHART_SERIES_SMA200),
            ("ema20", CHART_SERIES_EMA20), ("bollinger", CHART_SERIES_BOLLINGER),
        )
        if overlays[key] is not None
    ]
    if show_bluetsman:
        legend_items.append((CHART_BL_SIGNAL, charts.OVERLAY_COLORS["bl_signal"], "tri-up accent"))
        legend_items.append((CHART_SELL, t.DOWN, "tri-down"))
        if vade == pv.KISA:
            legend_items.append((CHART_FIRSAT, t.WARN, "dot"))
    legend_items += [
        (CHART_SERIES_MACD, charts.OVERLAY_COLORS["macd"], "line"),
        (CHART_SERIES_SIGNAL, charts.OVERLAY_COLORS["signal"], "line"),
    ]
    legend(legend_items)

    fig = charts.build_detail_figure(
        df=grafik[mask], overlays=overlays, rsi_series=rsi(g_close, 14)[mask], macd_df=macd(g_close)[mask],
        currency_label=currency_label, device=device, signal_scores=signal_scores,
        sell_points=sell_points, firsat_points=firsat_points,
    )
    charts.show_chart(fig, device, key="hd_chart")
    _render_explanations(currency_label)

    _render_alim_sistemi(df_tl, sonuc, vade, hafta_yarim, device)

    _render_teknik_ozet(close, sma50_series, sma200_series, rsi_series, macd_df)

    _render_sinyal_karnesi(ticker, start_date, end_date, device)
