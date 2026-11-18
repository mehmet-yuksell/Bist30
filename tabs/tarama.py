"""BIST 100 Tarama sekmesi: bugünün alım ve satış sinyalleri, kısa vade fırsatları ve iki vadeli tablo.

Sinyaller yalnızca Bluetsman Alım 1.2 ve Satım 1.2 göstergelerinden gelir (bluetsman.py, Pine
kodunun birebir karşılığı): günlük vade günlük, haftalık vade haftalık barlarla. Veri feed.batch
ile piyasa saatine göre güncel tutulur; sekme seans boyunca 15 dakikada bir kendini yeniler. Vade
seçimi sayfanın üstündedir (app.py) ve tüm sekmelerde geçerlidir.
"""

from datetime import timedelta

import pandas as pd
import streamlit as st

import feed
import market
import panel_veri as pv
from config import BIST100_TICKERS
from data import DataFetchError
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
    AL_CAPTION,
    AL_NONE,
    AL_TITLE,
    KF_CAPTION,
    KF_NONE,
    KF_TITLE,
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
    SIGNAL_ADX,
    SIGNAL_SELL_SCORE,
    SIGNAL_SELL_SCORE_VALUE,
    ST_CAPTION,
    ST_NONE,
    ST_RECENT_META,
    ST_RECENT_TITLE,
    ST_TITLE,
    TR_AS_OF,
    TR_COL_BUY,
    TR_COL_CHANGE,
    TR_COL_COMPANY,
    TR_COL_PRICE,
    TR_COL_RSI,
    TR_COL_SCORE,
    TR_COL_SELL,
    TR_COL_TICKER,
    TR_COL_VOLUME,
    TR_FALLING,
    TR_FILTER_ALL,
    TR_FILTER_LABEL,
    TR_FILTER_SIGNAL,
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
    TR_SELL_TODAY,
    TR_SIGNAL_TODAY,
    TR_SIGNAL_TODAY_SUB,
    TR_SORT_LABEL,
    TR_SORT_OPTIONS,
    TR_STRIP_FLAT,
    TR_STRIP_OF,
    TS_PROVISIONAL_BADGE,
    TS_RSI,
    TS_SIGNAL_PRICE,
    TS_SINCE,
    TS_VOLUME,
    TS_VOLUME_VALUE,
    VADE_BUGUN,
    VADE_ONCE,
    VADE_SHORT,
    VADE_WEEK_NOTE,
)

SIGNAL_LOOKBACK = 10  # tablo ve "son 10 gün/hafta" için
RECENT_BARS = 5       # kısa vade fırsatları ve son satış sinyalleri
NO_SIGNAL = "—"
VADELER = (pv.KISA, pv.ORTA)
SELL_STYLE = {"sat": (t.DOWN_TEXT, "down"), "kar_al": (t.ACCENT_TEXT, "accent")}


def _col(template: str, vade: str) -> str:
    return template.format(v=VADE_SHORT[vade])


def _when(once: int | None, vade: str) -> str:
    if once is None:
        return NO_SIGNAL
    return VADE_BUGUN[vade] if once == 0 else VADE_ONCE[vade].format(days=once)


def _vade_tarama(ticker: str, name: str, sonuc: pd.DataFrame, price: float, change: float) -> dict:
    """Bir hissenin bir vadedeki tablo hücreleri ve listelere girecek sinyalleri."""
    last = sonuc.iloc[-1]
    temel = {"ticker": ticker, "name": name, "price": price, "change": change}
    alimlar = pv.alim_sinyalleri(sonuc, SIGNAL_LOOKBACK)
    satislar = pv.satis_sinyalleri(sonuc, SIGNAL_LOOKBACK)
    out = {
        "skor": float(last["score"]),
        "alim_once": alimlar[0]["once"] if alimlar else None,
        "satis": satislar[0] if satislar else None,
        "alim_bugun": None, "satis_bugun": None, "satis_yakin": [], "firsat": None,
    }
    if alimlar and alimlar[0]["once"] == 0:
        out["alim_bugun"] = {**temel, "score": alimlar[0]["skor"], "rsi": float(last["rsi_value"]),
                             "volume_ratio": float(last["volume_ratio"]), "adx": float(last["adx_value"])}
    for s in satislar:
        if s["once"] == 0:
            out["satis_bugun"] = {**temel, **s, "rsi": float(last["rsi_value"])}
        elif s["once"] <= RECENT_BARS:
            out["satis_yakin"].append({**temel, **s})
    acik = pv.acik_alim(sonuc, RECENT_BARS + 1)
    if acik and acik["once"] >= 1:
        out["firsat"] = {**temel, **acik}
    return out


@st.cache_data(max_entries=3, show_spinner=False)
def _scan(data_key: str, _histories: dict) -> dict:
    """Her hisse için iki vadenin Alım 1.2 ve Satım 1.2 sonucunu hesaplar; yalnızca ekran özetlerini döndürür.

    data_key verinin çekildiği an olduğundan aynı veri için hesap bir kez yapılır
    (`_histories` önbellek anahtarına katılmaz).
    """
    rows = []
    listeler = {v: {"alim": [], "satis": [], "satis_yakin": [], "firsat": []} for v in VADELER}
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
               TR_COL_CHANGE: round(change, 2), TR_COL_RSI: None, TR_COL_VOLUME: None}
        for vade in VADELER:
            sonuc = pv.analiz(df, vade)
            if sonuc is None:
                row.update({_col(TR_COL_SCORE, vade): None, _col(TR_COL_BUY, vade): NO_SIGNAL,
                            _col(TR_COL_SELL, vade): NO_SIGNAL, f"_once_{vade}": None, f"_sat_{vade}": None})
                continue
            if vade == pv.ORTA:
                last_week = max(last_week, sonuc.index[-1]) if last_week is not None else sonuc.index[-1]
            else:
                row[TR_COL_RSI] = round(float(sonuc["rsi_value"].iloc[-1]), 1)
                row[TR_COL_VOLUME] = round(float(sonuc["volume_ratio"].iloc[-1]), 2)
            v = _vade_tarama(ticker, name, sonuc, price, change)
            satis = v["satis"]
            row[_col(TR_COL_SCORE, vade)] = round(v["skor"])
            row[_col(TR_COL_BUY, vade)] = _when(v["alim_once"], vade)
            row[_col(TR_COL_SELL, vade)] = f"{satis['ad']} · {_when(satis['once'], vade).lower()}" if satis else NO_SIGNAL
            row[f"_once_{vade}"] = v["alim_once"]
            row[f"_sat_{vade}"] = satis["once"] if satis else None
            if v["alim_bugun"]:
                listeler[vade]["alim"].append(v["alim_bugun"])
            if v["satis_bugun"]:
                listeler[vade]["satis"].append(v["satis_bugun"])
            if v["firsat"]:
                listeler[vade]["firsat"].append(v["firsat"])
            listeler[vade]["satis_yakin"] += v["satis_yakin"]
        rows.append(row)

    oncelik = [tur for tur, _ in pv.SATIS_TURLERI]
    for liste in listeler.values():
        liste["alim"].sort(key=lambda s: s["score"], reverse=True)
        liste["satis"].sort(key=lambda s: (oncelik.index(s["tur"]), -s["skor"]))
        liste["satis_yakin"].sort(key=lambda s: (s["once"], oncelik.index(s["tur"]), -s["skor"]))
        liste["firsat"].sort(key=lambda s: (s["once"], -s["skor"]))
    return {"rows": pd.DataFrame(rows), "listeler": listeler, "last_date": last_date, "last_week": last_week}


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

def _render_alim(liste: dict, vade: str, provisional: bool) -> None:
    section_title(AL_TITLE[vade], AL_CAPTION)
    if not liste["alim"]:
        callout("empty", AL_NONE[vade], None)
        return
    signal_cards([
        {
            "ticker": s["ticker"], "name": s["name"], "score": s["score"],
            "price": fmt_num(s["price"], 2), "change": s["change"],
            "badge": TS_PROVISIONAL_BADGE if provisional else None,
            "rows": [
                (TS_RSI, fmt_num(s["rsi"], 1)),
                (TS_VOLUME, TS_VOLUME_VALUE.format(ratio=fmt_num(s["volume_ratio"], 2))),
                (SIGNAL_ADX, fmt_num(s["adx"], 1)),
            ],
        }
        for s in liste["alim"]
    ])


def _render_satis(liste: dict, vade: str, provisional: bool) -> None:
    section_title(ST_TITLE[vade], ST_CAPTION)
    if liste["satis"]:
        kartlar = []
        for s in liste["satis"]:
            color, tone = SELL_STYLE[s["tur"]]
            kartlar.append({
                "ticker": s["ticker"], "name": s["name"], "score": s["skor"], "color": color,
                "price": fmt_num(s["price"], 2), "change": s["change"],
                "badge": f"{s['ad']} · {TS_PROVISIONAL_BADGE}" if provisional else s["ad"], "badge_tone": tone,
                "rows": [(SIGNAL_SELL_SCORE, SIGNAL_SELL_SCORE_VALUE.format(score=fmt_num(s["skor"], 0))),
                         (TS_RSI, fmt_num(s["rsi"], 1))],
            })
        signal_cards(kartlar)
    else:
        callout("empty", ST_NONE[vade], None)
    if liste["satis_yakin"]:
        st.caption(ST_RECENT_TITLE[vade])
        tagged_list([
            {"ticker": s["ticker"], "name": s["name"], "change": s["change"],
             "tags": [(s["ad"], SELL_STYLE[s["tur"]][1])],
             "meta": ST_RECENT_META.format(when=VADE_ONCE[vade].format(days=s["once"]),
                                           score=fmt_num(s["skor"], 0), price=fmt_num(s["fiyat"], 2))}
            for s in liste["satis_yakin"]
        ])


def _render_firsat(liste: dict, vade: str) -> None:
    section_title(KF_TITLE, KF_CAPTION[vade])
    if not liste["firsat"]:
        callout("empty", None, KF_NONE[vade])
        return
    recent_signal_list([
        {"ticker": s["ticker"], "name": s["name"], "when": VADE_ONCE[vade].format(days=s["once"]),
         "price_label": f"{TS_SIGNAL_PRICE} {fmt_num(s['fiyat'], 2)} · skor {s['skor']:.0f}",
         "change": s["degisim"], "since_label": TS_SINCE}
        for s in liste["firsat"]
    ])


# ---------------------------------------------------------------------------
# Özet ve liste
# ---------------------------------------------------------------------------

def _render_summary(table_df: pd.DataFrame, vade: str, provisional: bool) -> None:
    changes = table_df[TR_COL_CHANGE]
    rising = int((changes.round(2) > 0).sum())
    falling = int((changes.round(2) < 0).sum())
    flat = len(changes) - rising - falling
    buy_count = int((table_df[f"_once_{vade}"] == 0).sum())
    sell_count = int((table_df[f"_sat_{vade}"] == 0).sum())
    sub = TR_SIGNAL_TODAY_SUB if provisional else None

    cards = [
        metric_html(TR_RISING, f"▲ {rising}", sub=TR_STRIP_OF.format(count=len(changes)), value_class="ui-up"),
        metric_html(TR_FALLING, f"▼ {falling}", sub=TR_STRIP_FLAT.format(count=flat), value_class="ui-down"),
        metric_html(TR_SIGNAL_TODAY[vade], str(buy_count), sub=sub, value_class="ui-accent" if buy_count else ""),
        metric_html(TR_SELL_TODAY[vade], str(sell_count), sub=sub, value_class="ui-down" if sell_count else ""),
    ]
    stat_strip(cards, breadth=(rising, flat, falling))


def _style_table(df: pd.DataFrame):
    def change_color(value):
        tone = direction(value)
        color = {"up": t.UP, "down": t.DOWN_TEXT}.get(tone, t.TEXT_2)
        return f"color: {color}; font-weight: 600"

    def signal_color(color: str):
        return lambda value: f"color: {t.TEXT_3}" if value == NO_SIGNAL else f"color: {color}; font-weight: 600"

    def sell_color(value):
        kar_al = isinstance(value, str) and value.startswith("KAR AL")
        return signal_color(t.ACCENT_TEXT if kar_al else t.DOWN_TEXT)(value)

    return (
        df.style
        .format({
            TR_COL_PRICE: lambda v: fmt_num(v, 2),
            TR_COL_CHANGE: lambda v: f"{arrow(v)} {fmt_pct(v)}",
            TR_COL_RSI: lambda v: fmt_num(v, 1),
            TR_COL_VOLUME: lambda v: fmt_num(v, 2),
        })
        .map(change_color, subset=[TR_COL_CHANGE])
        .map(signal_color(t.ACCENT_TEXT), subset=[_col(TR_COL_BUY, v) for v in VADELER])
        .map(sell_color, subset=[_col(TR_COL_SELL, v) for v in VADELER])
    )


def _render_filters(device: str, vade: str) -> tuple[bool, str, str]:
    mobile = device == MOBILE
    signal_option = TR_FILTER_SIGNAL[vade].format(days=SIGNAL_LOOKBACK)
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


def _mobile_signal(row: pd.Series, vade: str) -> str | None:
    parcalar = []
    if row[_col(TR_COL_BUY, vade)] != NO_SIGNAL:
        parcalar.append(f"Alım · {row[_col(TR_COL_BUY, vade)].lower()}")
    if row[_col(TR_COL_SELL, vade)] != NO_SIGNAL:
        parcalar.append(row[_col(TR_COL_SELL, vade)])
    return " | ".join(parcalar) or None


def _render_results(table_df: pd.DataFrame, device: str, vade: str) -> None:
    only_signals, search, sort_key = _render_filters(device, vade)

    filtered = table_df
    if only_signals:
        filtered = filtered[filtered[f"_once_{vade}"].notna() | filtered[f"_sat_{vade}"].notna()]
        if filtered.empty:
            callout("empty", None, TR_NO_SIGNALS[vade].format(days=SIGNAL_LOOKBACK))
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
        "score_desc": (_col(TR_COL_SCORE, vade), False),
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
                "meta": TR_LIST_META_VADE.format(k=skor(row[_col(TR_COL_SCORE, pv.KISA)]),
                                                 o=skor(row[_col(TR_COL_SCORE, pv.ORTA)]),
                                                 rsi=fmt_num(row[TR_COL_RSI], 1)),
                "signal": _mobile_signal(row, vade),
            }
            for _, row in ordered.iterrows()
        ])
        return

    columns = [TR_COL_TICKER, TR_COL_COMPANY, TR_COL_PRICE, TR_COL_CHANGE]
    for v in VADELER:
        columns += [_col(TR_COL_SCORE, v), _col(TR_COL_BUY, v), _col(TR_COL_SELL, v)]
    columns += [TR_COL_RSI, TR_COL_VOLUME]
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
            **{_col(TR_COL_SCORE, v): st.column_config.ProgressColumn(_col(TR_COL_SCORE, v), **progress)
               for v in VADELER},
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
    # Kod listesi app.py'den: BIST 100 + takip listesindeki BIST 100 dışı hisseler
    tickers = ctx.get("tickers") or tuple(BIST100_TICKERS.keys())

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
    gun_kesin_degil = market.provisional(now, last_date.date())
    hafta_yarim = scan["last_week"] is not None and not pv.hafta_tamamlandi(last_date, scan["last_week"])
    provisional = gun_kesin_degil if vade == pv.KISA else (gun_kesin_degil or hafta_yarim)

    _render_status(data, last_date, is_open)
    if vade == pv.ORTA and hafta_yarim:
        st.caption(VADE_WEEK_NOTE)
    elif gun_kesin_degil:
        st.caption(LIVE_SESSION_NOTE if is_open else LIVE_SETTLING_NOTE)

    liste = scan["listeler"][vade]
    _render_alim(liste, vade, provisional)
    _render_satis(liste, vade, provisional)
    _render_firsat(liste, vade)

    caption = TR_AS_OF.format(date=fmt_date(last_date))
    missing_count = len(BIST100_TICKERS) - len(table_df)
    if missing_count > 0:
        caption += " · " + TR_MISSING.format(count=missing_count)

    _render_summary(table_df, vade, provisional)
    st.caption(caption)

    section_title(TR_LIST_TITLE, TR_LIST_CAPTION)
    _render_results(table_df, device, vade)
