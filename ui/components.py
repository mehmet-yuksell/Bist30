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
    FOOTER_KVKK,
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
        f"<p><strong>{escape(DISCLAIMER)}</strong></p>"
        f"<p>{escape(FOOTER_KVKK)}</p>"
        f'<p><a href="{escape(GITHUB_URL)}" target="_blank" rel="noopener noreferrer">{escape(FOOTER_GITHUB_LABEL)} ↗</a></p>'
        f'<p class="ui-credit">{escape(FOOTER_CREDIT)}</p>'
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
    """items: (ad, renk, biçim) — biçim 'line' | 'dot' | 'tri-up' | 'tri-up accent' | 'tri-down'."""
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
# BIST 100 Tarama
# ---------------------------------------------------------------------------

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
    """Telefon için kompakt liste: sembol + şirket + skor | fiyat + değişim rozeti (+ sinyal rozeti)."""
    def side(row: dict) -> str:
        signal = row.get("signal")
        signal_html = f'<div class="ui-list-signal">{badge(signal, "accent")}</div>' if signal else ""
        return (
            f'<div class="ui-list-side"><div class="ui-list-price">{escape(row["price"])}</div>'
            f'<div style="margin-top:4px">{change_badge(row["change"])}</div>{signal_html}</div>'
        )

    html_rows = "".join(
        '<div class="ui-list-row" role="listitem">'
        f'<div class="ui-list-main"><div class="ui-list-ticker">{escape(row["ticker"])}</div>'
        f'<div class="ui-list-name">{escape(row["name"])}</div>'
        f'<div class="ui-list-meta">{escape(row["meta"])}</div></div>'
        f"{side(row)}</div>"
        for row in rows
    )
    render(f'<div class="ui-list" role="list">{html_rows}</div>')


# ---------------------------------------------------------------------------
# Bluetsman alım sistemi
# ---------------------------------------------------------------------------

def score_color(score: float) -> str:
    """Pine göstergesindeki skor rengi: 70+ yeşil, 40-69 turuncu, altı kırmızı."""
    if score >= 70:
        return t.UP
    if score >= 40:
        return t.WARN
    return t.DOWN_TEXT


def _bar(ratio: float, color: str, css: str = "ui-score-bar") -> str:
    return (
        f'<div class="{css}" aria-hidden="true">'
        f'<span style="width:{min(max(ratio, 0.0), 1.0) * 100:.0f}%;background:{color}"></span></div>'
    )


def score_card(title: str, subtitle_lines: list[str], score: float, score_label: str,
               items: list[tuple[str, float, float]], aria_label: str = "Alım sinyali",
               color: str | None = None) -> None:
    """Sinyal durumu + skor + kalem kalem puan kırılımı. items: (kalem, puan, maksimum).

    color verilmezse alım skorunun renk eşikleri kullanılır.
    """
    color = color or score_color(score)
    cells = "".join(
        '<div class="ui-check" role="listitem">'
        f'<span class="ui-check-label">{escape(label)}</span>'
        f'<span class="ui-check-points num">{points:.0f}<small>/{maximum:.0f}</small></span>'
        f'{_bar(points / maximum if maximum else 0, t.ACCENT_TEXT if points else t.BORDER_STRONG, "ui-check-bar")}</div>'
        for label, points, maximum in items
    )
    subs = "".join(f'<div class="ui-signal-sub">{escape(line)}</div>' for line in subtitle_lines if line)
    render(
        f'<section class="ui-card" aria-label="{escape(aria_label)}">'
        '<div class="ui-signal-head">'
        f'<div><div class="ui-signal-title">{escape(title)}</div>{subs}</div>'
        f'<div class="ui-score"><div class="ui-score-value num" style="color:{color}">{score:.0f}</div>'
        f'<div class="ui-score-label">{escape(score_label)}</div></div></div>'
        f"{_bar(score / 100, color)}"
        f'<div class="ui-checks" role="list">{cells}</div>'
        "</section>"
    )


def status_bar(items: list[tuple[str, str, str | None]]) -> None:
    """Güncellik satırı. items: (etiket, değer, ton: 'up' | 'down' | None — değerin önüne nokta)."""
    parts = "".join(
        f'<span class="ui-status-item">{escape(label)}: '
        + (f'<span class="ui-status-dot {escape(tone)}"></span>' if tone else "")
        + f"<strong>{escape(value)}</strong></span>"
        for label, value, tone in items
    )
    render(f'<div class="ui-status" role="status">{parts}</div>')


def signal_cards(cards: list[dict]) -> None:
    """Bugünün sinyal kartları.

    Her kart: ticker, name, score, price, change (%), badge (str | None), rows [(etiket, değer)],
    isteğe bağlı color (skor rengi; verilmezse alım skoru renk eşikleri) ve badge_tone.
    """
    html_cards = []
    for card in cards:
        color = card.get("color") or score_color(card["score"])
        badge_html = badge(card["badge"], card.get("badge_tone", "warn")) if card.get("badge") else ""
        kv = "".join(
            f'<div class="ui-kv"><span>{escape(label)}</span><b>{escape(value)}</b></div>'
            for label, value in card["rows"]
        )
        html_cards.append(
            '<article class="ui-card ui-signal-card" role="listitem">'
            '<div class="ui-signal-card-top">'
            f'<div class="ui-signal-card-id"><div class="ui-list-ticker">{escape(card["ticker"])} {badge_html}</div>'
            f'<div class="ui-list-name">{escape(card["name"])}</div></div>'
            f'<div class="ui-signal-card-score num" style="color:{color}">{card["score"]:.0f}</div></div>'
            f'<div class="ui-signal-card-price"><span class="num">{escape(card["price"])}</span>'
            f"{change_badge(card['change'])}</div>"
            f"{_bar(card['score'] / 100, color)}{kv}</article>"
        )
    render(f'<div class="ui-signal-cards" role="list">{"".join(html_cards)}</div>')


def tagged_list(rows: list[dict]) -> None:
    """Etiketli kompakt liste. Her satır: ticker, name, tags [(metin, ton)], meta, isteğe bağlı change (%)."""
    def side(row: dict) -> str:
        return f'<div class="ui-list-side">{change_badge(row["change"])}</div>' if row.get("change") is not None else ""

    html_rows = "".join(
        '<div class="ui-list-row" role="listitem">'
        f'<div class="ui-list-main"><div class="ui-list-ticker">{escape(row["ticker"])} '
        + " ".join(badge(text, tone) for text, tone in row.get("tags", []))
        + f'</div><div class="ui-list-name">{escape(row["name"])}</div>'
        f'<div class="ui-list-meta ui-wrap">{escape(row.get("meta", ""))}</div></div>'
        f"{side(row)}</div>"
        for row in rows
    )
    render(f'<div class="ui-list ui-list-auto" role="list">{html_rows}</div>')


def recent_signal_list(rows: list[dict]) -> None:
    """Son günlerin alım sinyalleri. Her satır: ticker, name, when, price_label, change (%), since_label."""
    html_rows = "".join(
        '<div class="ui-list-row" role="listitem">'
        f'<div class="ui-list-main"><div class="ui-list-ticker">{escape(row["ticker"])} '
        f'{badge(row["when"], "accent")}</div>'
        f'<div class="ui-list-name">{escape(row["name"])}</div>'
        f'<div class="ui-list-meta">{escape(row["price_label"])}</div></div>'
        f'<div class="ui-list-side">{change_badge(row["change"])}'
        f'<div class="ui-list-meta">{escape(row["since_label"])}</div></div>'
        "</div>"
        for row in rows
    )
    render(f'<div class="ui-list ui-list-auto" role="list">{html_rows}</div>')


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

