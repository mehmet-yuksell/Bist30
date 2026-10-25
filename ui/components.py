"""HTML tabanlı arayüz bileşenleri.

Kartlar, rozetler, ızgaralar ve listeler Streamlit'in st.columns'u yerine CSS ızgarasıyla
çizilir; böylece telefonda 2x2 metrik ızgarası gibi düzenler Streamlit'in "dar ekranda her
sütun tam genişlik" davranışına takılmadan kontrol edilebilir. Tüm dinamik metinler
(özellikle kullanıcının elle girebildiği hisse sembolü) html.escape ile kaçışlanır.
"""

import base64
from html import escape

import streamlit as st

from ui import theme as t
from ui.format import arrow, direction, fmt_pct
from ui_text import (
    APP_SUBTITLE,
    APP_TITLE,
    DISCLAIMER,
    ERROR_CARD_HINT,
    ERROR_CARD_TITLE,
    FOOTER_CREDIT,
    FOOTER_GITHUB_LABEL,
    FOOTER_SOURCE,
    GITHUB_URL,
    HEADER_LAST_DATA,
    HEADER_SOURCE,
    LOADING_TEXT,
    RETRY_LABEL,
)

_ICONS = {
    "info": (
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
        f'<circle cx="12" cy="12" r="9" stroke="{t.ACCENT_TEXT}" stroke-width="2"/>'
        f'<path d="M12 11v6M12 7.5v.5" stroke="{t.ACCENT_TEXT}" stroke-width="2" stroke-linecap="round"/></svg>'
    ),
    "warn": (
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
        f'<path d="M12 3.5 2.8 19.5h18.4L12 3.5Z" stroke="{t.WARN}" stroke-width="2" stroke-linejoin="round"/>'
        f'<path d="M12 10v4.5M12 17v.5" stroke="{t.WARN}" stroke-width="2" stroke-linecap="round"/></svg>'
    ),
    "error": (
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
        f'<path d="M4 15a5 5 0 0 1 1.5-9.8A6 6 0 0 1 17 6a4.5 4.5 0 0 1 2.5 8.4" stroke="{t.TEXT_2}" stroke-width="2" stroke-linecap="round"/>'
        f'<path d="M12 12v5M12 20v.5" stroke="{t.TEXT_2}" stroke-width="2" stroke-linecap="round"/></svg>'
    ),
    "empty": (
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
        f'<circle cx="11" cy="11" r="6.5" stroke="{t.TEXT_2}" stroke-width="2"/>'
        f'<path d="m16 16 4.5 4.5" stroke="{t.TEXT_2}" stroke-width="2" stroke-linecap="round"/></svg>'
    ),
}

_LOGO = (
    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
    f'<path d="M6 3v4M6 15v6M12 2v5M12 15v7M18 5v3M18 16v4" stroke="{t.TEXT_2}" stroke-width="1.6" stroke-linecap="round"/>'
    f'<rect x="4" y="7" width="4" height="8" rx="1" fill="{t.UP}"/>'
    f'<rect x="10" y="7" width="4" height="8" rx="1" fill="{t.DOWN}"/>'
    f'<rect x="16" y="8" width="4" height="8" rx="1" fill="{t.ACCENT_TEXT}"/></svg>'
)


def _svg_img(svg: str, size: int) -> str:
    """st.html satır içi <svg> etiketlerini temizlediği için ikonlar data-URI <img> olarak verilir."""
    encoded = base64.b64encode(svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1).encode()).decode()
    return f'<img src="data:image/svg+xml;base64,{encoded}" width="{size}" height="{size}" alt="">'


def render(html_text: str) -> None:
    st.html(html_text)


# ---------------------------------------------------------------------------
# Sayfa iskeleti
# ---------------------------------------------------------------------------

def header_html(last_data_date: str | None = None) -> str:
    meta = f'<span><span class="ui-live-dot"></span>{escape(HEADER_SOURCE)}</span>'
    if last_data_date:
        meta += f'<span>{escape(HEADER_LAST_DATA)}: <strong class="num">{escape(last_data_date)}</strong></span>'
    return (
        '<div class="ui-header">'
        f'<div class="ui-brand"><div class="ui-logo">{_svg_img(_LOGO, 22)}</div>'
        f'<div><h1>{escape(APP_TITLE)}</h1><p>{escape(APP_SUBTITLE)}</p></div></div>'
        f'<div class="ui-header-meta">{meta}</div>'
        "</div>"
    )


def footer() -> None:
    render(
        '<footer class="ui-footer">'
        f"<p><strong>{escape(FOOTER_SOURCE)}</strong></p>"
        f"<p>{escape(DISCLAIMER)}</p>"
        f'<p><a href="{escape(GITHUB_URL)}" target="_blank" rel="noopener noreferrer">{escape(FOOTER_GITHUB_LABEL)} ↗</a>'
        f" · {escape(FOOTER_CREDIT)}</p>"
        "</footer>"
    )


def section_title(title: str, caption: str | None = None) -> None:
    body = f"<h3>{escape(title)}</h3>"
    if caption:
        body += f"<p>{escape(caption)}</p>"
    render(f'<div class="ui-section-title">{body}</div>')


def subtitle(text: str, caption: str | None = None) -> None:
    body = f'<p class="ui-subtitle">{escape(text)}</p>'
    if caption:
        body += f'<p class="ui-caption">{escape(caption)}</p>'
    render(f"<div>{body}</div>")


# ---------------------------------------------------------------------------
# Durumlar: bilgi, uyarı, hata, boş, yükleniyor
# ---------------------------------------------------------------------------

def callout(kind: str, title: str | None, body: str | list[str] | None = None) -> None:
    """kind: 'info' | 'warn' | 'error' | 'empty'."""
    parts = []
    if title:
        parts.append(f'<p class="ui-callout-title">{escape(title)}</p>')
    if isinstance(body, list):
        items = "".join(f"<li>{escape(item)}</li>" for item in body)
        parts.append(f'<div class="ui-callout-body"><ul>{items}</ul></div>')
    elif body:
        parts.append(f'<p class="ui-callout-body">{escape(body)}</p>')
    render(
        f'<div class="ui-callout {escape(kind)}" role="{"alert" if kind == "warn" else "status"}">'
        f'<div class="ui-callout-icon">{_svg_img(_ICONS.get(kind, _ICONS["info"]), 18)}</div>'
        f'<div>{"".join(parts)}</div></div>'
    )


def error_state(message: str, key: str) -> None:
    """Veri alınamadığında sakin bir kart + 'Tekrar dene' düğmesi.

    st.cache_data hataları önbelleğe almadığı için düğmeye basılınca yapılan yeniden
    çalıştırma veriyi gerçekten yeniden ister.
    """
    callout("error", ERROR_CARD_TITLE, f"{message} {ERROR_CARD_HINT}")
    st.button(RETRY_LABEL, key=key, icon=":material/refresh:")


def skeleton_html(variant: str = "detail") -> str:
    def block(height: int, width: str = "100%") -> str:
        return f'<div class="ui-skel" style="height:{height}px;width:{width}"></div>'

    if variant == "detail":
        inner = (
            block(132)
            + block(36, "70%")
            + block(360)
        )
    elif variant == "list":
        inner = block(64) + block(220) + block(56) + block(56) + block(56)
    else:
        inner = block(140) + block(320)
    return (
        f'<div class="ui-skeleton" aria-busy="true" aria-live="polite">'
        f'<span class="ui-skel-label">{escape(LOADING_TEXT)}</span>{inner}</div>'
    )


# ---------------------------------------------------------------------------
# Rozet ve metrikler
# ---------------------------------------------------------------------------

def badge(text: str, tone: str = "neutral", large: bool = False) -> str:
    size = " lg" if large else ""
    return f'<span class="ui-badge {escape(tone)}{size}">{escape(text)}</span>'


def change_badge(pct: float, large: bool = False, extra: str | None = None) -> str:
    """Renk + ▲/▼ + işaretli yüzde: '▲ %+1,23'."""
    label = f"{arrow(pct)} {fmt_pct(pct)}"
    if extra:
        label += f" ({extra})"
    return badge(label, direction(pct), large)


def metric_html(label: str, value: str, sub: str | None = None, value_class: str = "") -> str:
    sub_html = f'<div class="ui-metric-sub">{sub}</div>' if sub else ""
    return (
        '<div class="ui-metric">'
        f'<div class="ui-metric-label">{escape(label)}</div>'
        f'<div class="ui-metric-value {value_class}">{escape(value)}</div>{sub_html}</div>'
    )


def hero(ticker: str, name: str, price: str, change_pct: float, change_abs: str,
         as_of: str, metrics: list[str]) -> None:
    render(
        '<section class="ui-card ui-hero" aria-label="Hisse özeti">'
        '<div class="ui-hero-top">'
        f'<div class="ui-hero-id"><div class="ui-hero-ticker">{escape(ticker)}</div>'
        f'<div class="ui-hero-name">{escape(name)}</div></div>'
        '<div class="ui-hero-price-wrap">'
        f'<div class="ui-hero-price num">{escape(price)}</div>'
        f'<div class="ui-hero-change">{change_badge(change_pct, large=True, extra=change_abs)}</div>'
        f'<div class="ui-hero-asof">{escape(as_of)}</div>'
        "</div></div>"
        f'<div class="ui-metrics">{"".join(metrics)}</div>'
        "</section>"
    )


def summary_rows(rows: list[tuple[str, str, str, str]]) -> None:
    """rows: (etiket, rozet metni, ton, açıklama cümlesi)."""
    items = "".join(
        '<div class="ui-row">'
        f'<div class="ui-row-label">{escape(label)}</div>'
        f'<div class="ui-row-detail">{escape(detail)}</div>'
        f'<div class="ui-row-badge">{badge(text, tone)}</div>'
        "</div>"
        for label, text, tone, detail in rows
    )
    render(f'<div class="ui-card"><div class="ui-rows">{items}</div></div>')


def legend(items: list[tuple[str, str, str]]) -> None:
    """items: (ad, renk, biçim) — biçim 'line' | 'dot' | 'tri-up' | 'tri-down'."""
    if not items:
        return
    html_items = "".join(
        f'<span class="ui-legend-item"><span class="ui-swatch {escape(kind)}" '
        f'style="background:{escape(color)}"></span>{escape(name)}</span>'
        for name, color, kind in items
    )
    render(f'<div class="ui-legend" aria-label="Grafik lejantı">{html_items}</div>')


# ---------------------------------------------------------------------------
# Sinyal Karnesi
# ---------------------------------------------------------------------------

def strategy_cards(cards: list[dict]) -> None:
    """Her kart: name, total, drawdown, trades, win_rate, tag ('best'|'worst'|'benchmark'|None), tag_text."""
    html_cards = []
    for card in cards:
        tag = card.get("tag")
        tag_html = ""
        if tag == "best":
            tag_html = badge(card["tag_text"], "up")
        elif tag == "worst":
            tag_html = badge(card["tag_text"], "down")
        elif tag == "benchmark":
            tag_html = badge(card["tag_text"], "neutral")
        total = card["total"]
        kv = "".join(
            f'<div class="ui-kv"><span>{escape(label)}</span><b>{escape(value)}</b></div>'
            for label, value in card["rows"]
        )
        html_cards.append(
            f'<article class="ui-card ui-strategy {escape(tag or "")}">'
            f'<div class="ui-strategy-tag">{tag_html}</div>'
            f'<div class="ui-strategy-name">{escape(card["name"])}</div>'
            f'<div class="ui-strategy-return ui-{direction(total)}">{escape(arrow(total))} {escape(fmt_pct(total))}</div>'
            f'<div class="ui-metric-label">{escape(card["total_label"])}</div>'
            f"{kv}</article>"
        )
    render(f'<div class="ui-cards">{"".join(html_cards)}</div>')


# ---------------------------------------------------------------------------
# BIST 30 Tarama
# ---------------------------------------------------------------------------

def _mix(hex_a: str, hex_b: str, ratio: float) -> str:
    a = [int(hex_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(hex_b[i:i + 2], 16) for i in (1, 3, 5)]
    mixed = [round(x + (y - x) * ratio) for x, y in zip(a, b)]
    return "#" + "".join(f"{v:02X}" for v in mixed)


def heat_color(pct: float, max_abs: float) -> str:
    """Yön içeren ıraksak skala: kırmızı <- nötr gri -> yeşil (uçlar beyaz yazıyla okunur)."""
    ratio = min(abs(pct) / max_abs, 1.0) ** 0.75 if max_abs else 0.0
    return _mix(t.HEAT_NEUTRAL, t.HEAT_UP if pct >= 0 else t.HEAT_DOWN, ratio)


def heat_grid(items: list[tuple[str, str, float]]) -> None:
    """items: (sembol, şirket adı, günlük % değişim)."""
    max_abs = max([2.0] + [abs(pct) for _, _, pct in items])
    cells = "".join(
        f'<div class="ui-heat-cell" style="background:{heat_color(pct, max_abs)}" '
        f'role="listitem" title="{escape(name)}: {escape(fmt_pct(pct))}">'
        f"<b>{escape(ticker)}</b><span>{escape(arrow(pct))} {escape(fmt_pct(pct))}</span></div>"
        for ticker, name, pct in items
    )
    render(f'<div class="ui-heat" role="list" aria-label="Günlük değişim ısı haritası">{cells}</div>')


def stat_strip(cards: list[str], breadth: tuple[int, int, int] | None = None) -> None:
    breadth_html = ""
    if breadth:
        up, flat, down = breadth
        total = max(up + flat + down, 1)
        breadth_html = (
            '<div class="ui-breadth" aria-hidden="true">'
            f'<span style="width:{up / total * 100:.1f}%;background:{t.UP}"></span>'
            f'<span style="width:{flat / total * 100:.1f}%;background:{t.BORDER_STRONG}"></span>'
            f'<span style="width:{down / total * 100:.1f}%;background:{t.DOWN}"></span></div>'
        )
    render(f'<div><div class="ui-strip">{"".join(cards)}</div>{breadth_html}</div>')


def stock_list(rows: list[dict]) -> None:
    """Telefon için kompakt liste: sembol + şirket | fiyat + değişim rozeti, RSI ve trend."""
    html_rows = "".join(
        '<div class="ui-list-row" role="listitem">'
        f'<div class="ui-list-main"><div class="ui-list-ticker">{escape(row["ticker"])}</div>'
        f'<div class="ui-list-name">{escape(row["name"])}</div>'
        f'<div class="ui-list-meta">RSI {escape(row["rsi"])} · {escape(row["trend"])}</div></div>'
        f'<div class="ui-list-side"><div class="ui-list-price">{escape(row["price"])}</div>'
        f'<div style="margin-top:4px">{change_badge(row["change"])}</div></div>'
        "</div>"
        for row in rows
    )
    render(f'<div class="ui-list" role="list">{html_rows}</div>')


# ---------------------------------------------------------------------------
# Karşılaştırma
# ---------------------------------------------------------------------------

def rank_list(rows: list[tuple[str, str, float]]) -> None:
    """rows: (sembol, seri rengi, dönem getirisi %) — getiriye göre sıralı gelmeli."""
    max_abs = max([1.0] + [abs(pct) for _, _, pct in rows])
    items = "".join(
        '<div class="ui-rank-row">'
        f'<span class="ui-rank-no">{i}.</span>'
        f'<span class="ui-swatch dot" style="background:{escape(color)}"></span>'
        f'<span class="ui-rank-ticker">{escape(ticker)}</span>'
        f'<span class="ui-rank-bar"><span style="width:{abs(pct) / max_abs * 100:.1f}%;'
        f'background:{t.UP if pct >= 0 else t.DOWN}"></span></span>'
        f"{change_badge(pct)}</div>"
        for i, (ticker, color, pct) in enumerate(rows, start=1)
    )
    render(f'<div class="ui-card">{items}</div>')

