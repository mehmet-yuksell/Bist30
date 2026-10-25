"""Tasarım sistemi: CSS değişkenleri, Streamlit varsayılanlarının sadeleştirilmesi ve
mobil öncelikli (mobile-first) düzen kuralları.

Kırılım noktaları ui/viewport.py ile aynıdır: < 768px telefon, 768-1023px tablet,
>= 1024px masaüstü.
"""

import streamlit as st

from ui import theme as t

_CSS = f"""
:root {{
    --bg: {t.BG};
    --surface-1: {t.SURFACE_1};
    --surface-2: {t.SURFACE_2};
    --border: {t.BORDER};
    --border-strong: {t.BORDER_STRONG};
    --text-1: {t.TEXT_1};
    --text-2: {t.TEXT_2};
    --text-3: {t.TEXT_3};
    --up: {t.UP};
    --down: {t.DOWN};
    --down-text: {t.DOWN_TEXT};
    --up-bg: rgba(22, 199, 132, 0.14);
    --down-bg: rgba(234, 57, 67, 0.16);
    --warn: {t.WARN};
    --warn-bg: rgba(240, 180, 41, 0.10);
    --warn-border: rgba(240, 180, 41, 0.45);
    --accent: {t.ACCENT};
    --accent-text: {t.ACCENT_TEXT};
    --accent-bg: rgba(47, 111, 235, 0.14);
    --neutral-bg: rgba(163, 170, 184, 0.12);

    --space-1: {t.SPACE['1']}px;
    --space-2: {t.SPACE['2']}px;
    --space-3: {t.SPACE['3']}px;
    --space-4: {t.SPACE['4']}px;
    --space-5: {t.SPACE['5']}px;
    --space-6: {t.SPACE['6']}px;

    --radius-sm: {t.RADIUS['sm']}px;
    --radius-md: {t.RADIUS['md']}px;
    --radius-pill: {t.RADIUS['pill']}px;
    --shadow-1: 0 1px 2px rgba(0, 0, 0, 0.35);

    --font: {t.FONT_FAMILY};
    --fs-xs: 12px;
    --fs-sm: 13px;
    --fs-base: 15px;
    --fs-md: 16px;
    --fs-lg: clamp(17px, 1.6vw, 19px);
    --fs-xl: clamp(19px, 2.4vw, 23px);
    --fs-hero: clamp(30px, 6vw, 42px);
    --touch: 44px;
}}

/* ---------- Temel ---------- */
html, body, .stApp {{
    background: var(--bg);
    color: var(--text-1);
    font-family: var(--font);
    -webkit-text-size-adjust: 100%;
}}
.stApp p, .stApp li {{ font-size: var(--fs-md); line-height: 1.55; }}
.stApp .ui-callout-body {{ font-size: var(--fs-base); }}
.stApp .ui-caption {{ font-size: var(--fs-sm); }}
.stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stCaptionContainer"] p {{ font-size: var(--fs-sm) !important; color: var(--text-3); line-height: 1.45; }}
.num, .ui-num, [data-testid="stDataFrame"], [data-testid="stMetricValue"] {{
    font-variant-numeric: tabular-nums;
    font-feature-settings: "tnum" 1;
}}
:focus-visible {{
    outline: 2px solid var(--accent-text) !important;
    outline-offset: 2px !important;
}}

/* ---------- Streamlit şablon görünümünü sadeleştir ---------- */
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
#MainMenu,
footer {{
    display: none !important;
}}
.st-key-viewport_probe {{ display: none !important; }}
[data-testid="stMainBlockContainer"], .block-container {{
    max-width: 1280px;
    padding: var(--space-5) var(--space-6) var(--space-6) !important;
}}
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] {{ gap: var(--space-4); }}

/* ---------- Başlık alanı ---------- */
.ui-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-3);
    flex-wrap: wrap;
}}
.ui-brand {{ display: flex; align-items: center; gap: var(--space-3); min-width: 0; }}
.ui-logo {{
    flex: none;
    width: 40px; height: 40px;
    border-radius: 10px;
    background: var(--accent-bg);
    border: 1px solid rgba(110, 168, 254, 0.35);
    display: grid; place-items: center;
}}
.ui-brand h1 {{
    margin: 0; padding: 0;
    font-size: var(--fs-xl);
    font-weight: 700;
    letter-spacing: -0.01em;
    line-height: 1.2;
    color: var(--text-1);
}}
.ui-brand p {{ margin: 2px 0 0; font-size: var(--fs-sm) !important; color: var(--text-2); line-height: 1.35; }}
.ui-header-meta {{
    display: flex; flex-direction: column; align-items: flex-end; gap: 2px;
    font-size: var(--fs-xs); color: var(--text-3);
}}
.ui-header-meta strong {{ color: var(--text-2); font-weight: 600; }}
.ui-live-dot {{
    display: inline-block; width: 7px; height: 7px; border-radius: 50%;
    background: var(--up); margin-right: 6px; vertical-align: 1px;
}}

/* ---------- Sekmeler (Streamlit 1.65: react-aria yapısı) ---------- */
[data-testid="stTabs"] [role="tablist"] {{
    position: sticky; top: 0; z-index: 20;
    background: var(--bg);
    gap: var(--space-1);
    border-bottom: 1px solid var(--border);
    overflow-x: auto;
    scrollbar-width: none;
}}
[data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar {{ display: none; }}
[data-testid="stTab"] {{
    min-height: var(--touch);
    padding: 0 var(--space-4);
    white-space: nowrap;
    flex: none;
    display: flex; align-items: center;
}}
[data-testid="stTab"] p {{
    font-size: var(--fs-base) !important;
    font-weight: 600;
    color: var(--text-2);
}}
[data-testid="stTab"]:hover p, [data-testid="stTab"][aria-selected="true"] p {{ color: var(--text-1); }}
[data-testid="stTab"] .react-aria-SelectionIndicator {{ background: var(--accent-text); height: 3px; }}
[data-testid="stTabPanel"] {{ padding-top: var(--space-4); }}

/* ---------- Form öğeleri ve dokunma hedefleri ---------- */
[data-testid="stWidgetLabel"] p {{ font-size: var(--fs-sm) !important; color: var(--text-2); font-weight: 500; }}
[data-testid="stSelectbox"] [role="group"],
[data-testid="stMultiSelect"] [role="group"]:not([aria-label]),
[data-testid="stTextInputRootElement"],
[data-testid="stDateInputField"],
[data-testid="stNumberInputContainer"] {{
    min-height: var(--touch);
    border-radius: 10px !important;
}}
[data-testid="stMultiSelect"] [data-tag] > span[title] {{
    max-width: 12em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}}
.stButton button, [data-testid="stPopoverButton"] {{
    min-height: var(--touch);
    border-radius: 10px;
}}
[data-testid="stButtonGroup"] button {{ min-height: 38px; padding: 0 var(--space-3); }}
[data-testid="stButtonGroup"] button[data-variant="pills"] {{ border-radius: var(--radius-pill) !important; }}
[data-testid="stButtonGroup"] button p {{ font-size: var(--fs-sm) !important; font-weight: 500; }}
[data-testid="stNumberInput"] button {{ min-width: 40px; }}

/* ---------- Açılır kutular ("Bu ne anlama gelir?") ---------- */
[data-testid="stExpander"] details {{
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    background: var(--surface-1);
}}
[data-testid="stExpander"] summary {{ min-height: var(--touch); padding: 0 var(--space-4); }}
[data-testid="stExpander"] summary p {{ font-size: var(--fs-sm) !important; color: var(--text-2); font-weight: 500; }}
[data-testid="stExpander"] summary:hover p {{ color: var(--text-1); }}
[data-testid="stExpanderDetails"] p {{ color: var(--text-2); font-size: var(--fs-base) !important; }}

/* ---------- Popover ---------- */
[data-testid="stPopoverBody"] {{
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-md);
    background: var(--surface-1);
    max-width: min(360px, calc(100vw - 24px));
}}

/* ---------- Veri tabloları ve grafikler ---------- */
[data-testid="stDataFrame"] {{ border: 1px solid var(--border); border-radius: var(--radius-md); overflow: hidden; }}
[data-testid="stPlotlyChart"] {{ min-width: 0; }}

/* ---------- Kartlar ---------- */
.ui-card {{
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: var(--space-4);
    box-shadow: var(--shadow-1);
    min-width: 0;
}}
.ui-section-title {{ margin: var(--space-2) 0 0; }}
.ui-section-title h3 {{
    margin: 0; padding: 0;
    font-size: var(--fs-lg); font-weight: 650; color: var(--text-1); letter-spacing: -0.005em;
}}
.ui-section-title p {{ margin: 4px 0 0; font-size: var(--fs-sm) !important; color: var(--text-3); line-height: 1.45; }}
.ui-subtitle {{ font-size: var(--fs-base); font-weight: 600; color: var(--text-1); margin: 0; }}
.ui-caption {{ font-size: var(--fs-sm); color: var(--text-3); margin: 0; line-height: 1.45; }}

/* Hero */
.ui-hero {{ display: grid; gap: var(--space-4); }}
.ui-hero-top {{ display: flex; justify-content: space-between; align-items: flex-start; gap: var(--space-3); flex-wrap: wrap; }}
.ui-hero-id {{ min-width: 0; }}
.ui-hero-ticker {{ font-size: var(--fs-lg); font-weight: 700; color: var(--text-1); letter-spacing: 0.01em; }}
.ui-hero-name {{
    font-size: var(--fs-sm); color: var(--text-2); margin-top: 2px;
    overflow-wrap: anywhere;
}}
.ui-hero-price-wrap {{ text-align: right; }}
.ui-hero-price {{ font-size: var(--fs-hero); font-weight: 700; line-height: 1.05; letter-spacing: -0.02em; color: var(--text-1); }}
.ui-hero-change {{ margin-top: var(--space-2); display: flex; gap: var(--space-2); justify-content: flex-end; align-items: center; flex-wrap: wrap; }}
.ui-hero-asof {{ font-size: var(--fs-xs); color: var(--text-3); margin-top: 6px; }}

/* Rozetler */
.ui-badge {{
    display: inline-flex; align-items: center; gap: 4px;
    padding: 3px 10px;
    border-radius: var(--radius-pill);
    font-size: var(--fs-sm); font-weight: 600; line-height: 1.4;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
}}
.ui-badge.up {{ color: var(--up); background: var(--up-bg); }}
.ui-badge.down {{ color: var(--down-text); background: var(--down-bg); }}
.ui-badge.flat, .ui-badge.neutral {{ color: var(--text-2); background: var(--neutral-bg); }}
.ui-badge.warn {{ color: var(--warn); background: var(--warn-bg); }}
.ui-badge.accent {{ color: var(--accent-text); background: var(--accent-bg); }}
.ui-badge.lg {{ font-size: var(--fs-md); padding: 4px 12px; }}
.ui-up {{ color: var(--up); }}
.ui-down {{ color: var(--down-text); }}
.ui-flat {{ color: var(--text-2); }}

/* Metrik ızgarası: telefonda 2x2, geniş ekranda 4'lü */
.ui-metrics {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-2); }}
.ui-metric {{
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: var(--space-3);
    min-width: 0;
}}
.ui-metric-label {{ font-size: var(--fs-xs); color: var(--text-3); font-weight: 500; }}
.ui-metric-value {{ font-size: var(--fs-md); font-weight: 650; color: var(--text-1); margin-top: 4px; font-variant-numeric: tabular-nums; }}
.ui-metric-sub {{ font-size: var(--fs-xs); color: var(--text-2); margin-top: 4px; }}
.ui-metric-sub .ui-badge {{ font-size: 11px; padding: 1px 8px; }}

/* Teknik özet satırları */
.ui-rows {{ display: grid; }}
.ui-row {{
    display: grid;
    grid-template-columns: minmax(120px, 180px) minmax(0, 1fr) auto;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-3) 0;
    border-top: 1px solid var(--border);
}}
.ui-row:first-child {{ border-top: 0; padding-top: 0; }}
.ui-row:last-child {{ padding-bottom: 0; }}
.ui-row-label {{ font-size: var(--fs-base); font-weight: 600; color: var(--text-1); }}
.ui-row-detail {{ font-size: var(--fs-sm); color: var(--text-2); line-height: 1.45; }}
.ui-row-badge {{ justify-self: end; }}

/* Bilgi kutuları */
.ui-callout {{
    display: flex; gap: var(--space-3); align-items: flex-start;
    border-radius: var(--radius-md);
    padding: var(--space-3) var(--space-4);
    border: 1px solid var(--border);
    background: var(--surface-1);
}}
.ui-callout-icon {{ flex: none; width: 22px; height: 22px; display: grid; place-items: center; margin-top: 1px; }}
.ui-callout-title {{ font-weight: 650; font-size: var(--fs-base); color: var(--text-1); margin: 0; }}
.ui-callout-body {{ font-size: var(--fs-sm); color: var(--text-2); margin: 2px 0 0; line-height: 1.5; }}
.ui-callout-body ul {{ margin: 4px 0 0; padding-left: 18px; }}
.ui-callout-body li {{ font-size: var(--fs-sm) !important; margin: 2px 0; }}
.ui-callout.info {{ border-color: rgba(110, 168, 254, 0.35); background: var(--accent-bg); }}
.ui-callout.warn {{ border-color: var(--warn-border); background: var(--warn-bg); }}
.ui-callout.error {{ border-color: var(--border-strong); background: var(--surface-1); }}
.ui-callout.empty {{ border-style: dashed; border-color: var(--border-strong); background: transparent; padding: var(--space-5) var(--space-4); }}

/* Grafik lejantı (grafiğin üstünde, satır kırarak) */
.ui-legend {{ display: flex; flex-wrap: wrap; gap: 6px 14px; align-items: center; margin: 0; }}
.ui-legend-item {{ display: inline-flex; align-items: center; gap: 6px; font-size: var(--fs-xs); color: var(--text-2); white-space: nowrap; }}
.ui-swatch {{ display: inline-block; width: 14px; height: 3px; border-radius: 2px; }}
.ui-swatch.dot {{ width: 9px; height: 9px; border-radius: 50%; }}
.ui-swatch.tri-up {{ width: 0; height: 0; border-left: 5px solid transparent; border-right: 5px solid transparent; border-bottom: 9px solid var(--up); border-radius: 0; background: none !important; }}
.ui-swatch.tri-down {{ width: 0; height: 0; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 9px solid var(--down); border-radius: 0; background: none !important; }}

/* Strateji kartları (Sinyal Karnesi) */
.ui-cards {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-3); }}
.ui-strategy {{ display: flex; flex-direction: column; gap: var(--space-2); padding: var(--space-3); }}
.ui-strategy.best {{ border-color: rgba(22, 199, 132, 0.55); }}
.ui-strategy.worst {{ border-color: rgba(240, 97, 106, 0.55); }}
.ui-strategy-name {{ font-size: var(--fs-sm); font-weight: 650; color: var(--text-1); line-height: 1.3; }}
.ui-strategy-return {{ font-size: var(--fs-xl); font-weight: 700; font-variant-numeric: tabular-nums; line-height: 1.15; }}
.ui-strategy-tag {{ min-height: 22px; }}
.ui-strategy-tag .ui-badge {{ font-size: 11px; padding: 2px 8px; }}
.ui-kv {{ display: flex; justify-content: space-between; gap: var(--space-2); font-size: var(--fs-xs); color: var(--text-3); border-top: 1px solid var(--border); padding-top: 6px; }}
.ui-kv b {{ color: var(--text-1); font-weight: 600; font-variant-numeric: tabular-nums; }}

/* Tarama özet şeridi */
.ui-strip {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-2); }}
.ui-strip .ui-metric-value {{ font-size: var(--fs-lg); }}
.ui-breadth {{ display: flex; height: 6px; border-radius: 3px; overflow: hidden; background: var(--neutral-bg); margin-top: var(--space-2); }}
.ui-breadth span {{ display: block; height: 100%; }}

/* Isı haritası (HTML ızgarası): telefonda 5, geniş ekranda 6 sütun */
.ui-heat {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 4px; }}
.ui-heat-cell {{
    border-radius: var(--radius-sm);
    padding: 10px 4px;
    text-align: center;
    color: #FFFFFF;
    min-width: 0;
}}
.ui-heat-cell b {{ display: block; font-size: var(--fs-sm); font-weight: 700; letter-spacing: 0.01em; }}
.ui-heat-cell span {{ display: block; font-size: var(--fs-xs); font-weight: 500; margin-top: 2px; font-variant-numeric: tabular-nums; opacity: 0.95; }}

/* Kompakt hisse listesi */
.ui-list {{
    max-height: 520px;
    overflow-y: auto;
    overscroll-behavior: contain;
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    background: var(--surface-1);
}}
.ui-list-row {{
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: var(--space-3);
    align-items: center;
    padding: 10px var(--space-4);
    border-top: 1px solid var(--border);
    min-height: 56px;
}}
.ui-list-row:first-child {{ border-top: 0; }}
.ui-list-main {{ min-width: 0; }}
.ui-list-ticker {{ font-size: var(--fs-base); font-weight: 650; color: var(--text-1); }}
.ui-list-name {{ font-size: var(--fs-xs); color: var(--text-3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.ui-list-side {{ text-align: right; }}
.ui-list-price {{ font-size: var(--fs-base); font-weight: 600; color: var(--text-1); font-variant-numeric: tabular-nums; }}
.ui-list-meta {{ font-size: var(--fs-xs); color: var(--text-3); margin-top: 2px; white-space: nowrap; }}

/* Karşılaştırma sıralaması */
.ui-rank-row {{
    display: grid;
    grid-template-columns: 22px 10px minmax(56px, auto) minmax(0, 1fr) auto;
    gap: var(--space-2) var(--space-3);
    align-items: center;
    padding: 8px 0;
    border-top: 1px solid var(--border);
}}
.ui-rank-row:first-child {{ border-top: 0; padding-top: 0; }}
.ui-rank-row:last-child {{ padding-bottom: 0; }}
.ui-rank-no {{ font-size: var(--fs-sm); color: var(--text-3); font-variant-numeric: tabular-nums; }}
.ui-rank-ticker {{ font-weight: 650; font-size: var(--fs-base); color: var(--text-1); }}
.ui-rank-bar {{ height: 6px; border-radius: 3px; background: var(--neutral-bg); overflow: hidden; }}
.ui-rank-bar span {{ display: block; height: 100%; border-radius: 3px; }}

/* İskelet (yüklenme) */
.ui-skeleton {{ display: grid; gap: var(--space-3); }}
.ui-skel {{
    border-radius: var(--radius-sm);
    background: linear-gradient(90deg, var(--surface-1) 0%, var(--surface-2) 50%, var(--surface-1) 100%);
    background-size: 200% 100%;
    animation: ui-shimmer 1.4s ease-in-out infinite;
}}
.ui-skel-label {{ font-size: var(--fs-sm); color: var(--text-3); }}
@keyframes ui-shimmer {{ 0% {{ background-position: 200% 0; }} 100% {{ background-position: -200% 0; }} }}
@media (prefers-reduced-motion: reduce) {{ .ui-skel {{ animation: none; }} }}

/* Alt bilgi */
.ui-footer {{
    border-top: 1px solid var(--border);
    margin-top: var(--space-5);
    padding-top: var(--space-4);
    display: grid; gap: 6px;
    font-size: var(--fs-xs); color: var(--text-3); line-height: 1.5;
}}
.ui-footer p {{ font-size: var(--fs-xs) !important; margin: 0; color: var(--text-3); }}
.ui-footer strong {{ color: var(--text-2); font-weight: 600; }}
.ui-footer a {{ color: var(--accent-text); text-decoration: none; display: inline-flex; align-items: center; min-height: 32px; }}
.ui-footer a:hover {{ text-decoration: underline; }}

/* ---------- Tablet ve üstü ---------- */
@media (min-width: 768px) {{
    .ui-cards {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    .ui-heat {{ grid-template-columns: repeat(6, minmax(0, 1fr)); }}
    .ui-strip {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
}}

/* ---------- Masaüstü ---------- */
@media (min-width: 1024px) {{
    .ui-metrics {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
    .ui-cards {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
    [data-testid="stButtonGroup"] button {{ min-height: 34px; }}
    .stButton button, [data-testid="stPopoverButton"] {{ min-height: 40px; }}
    [data-testid="stSelectbox"] [role="group"],
    [data-testid="stTextInputRootElement"],
    [data-testid="stDateInputField"],
    [data-testid="stNumberInputContainer"] {{ min-height: 40px; }}
}}

/* ---------- Dokunmatik ekranlar (telefon + tablet): en az 44px hedefler ---------- */
@media (max-width: 1023.98px) {{
    [data-testid="stButtonGroup"] button {{ min-height: var(--touch); }}
    [data-testid="stSelectbox"] input,
    [data-testid="stTextInputField"],
    [data-testid="stNumberInputField"] {{ min-height: 42px; }}
    [data-testid="stNumberInput"] button {{ min-height: var(--touch); min-width: var(--touch); }}
    [data-testid="stTooltipHoverTarget"] button {{ min-width: 32px; min-height: 32px; }}
    [data-testid="stMultiSelect"] button {{ min-width: 32px; min-height: 32px; }}
}}

/* ---------- Telefon ---------- */
@media (max-width: 767.98px) {{
    [data-testid="stMainBlockContainer"], .block-container {{
        padding: var(--space-3) 14px var(--space-5) !important;
    }}
    [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] {{ gap: var(--space-3); }}
    /* st.columns ile yan yana duran her şey alt alta */
    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]) {{ flex-wrap: wrap; gap: var(--space-3); }}
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{ min-width: 100% !important; flex: 1 1 100% !important; }}
    [data-testid="stTab"] {{ padding: 0 10px; }}
    [data-testid="stTab"] p {{ font-size: 14px !important; }}
    [data-testid="stTab"] span[role="img"] {{ display: none !important; }}
    /* Karşılaştırmada çoklu seçim tam genişlik alır, tarih düğmesi alta iner */
    .st-key-kr_controls > :has([data-testid="stMultiSelect"]) {{ min-width: 100%; flex: 1 1 100%; }}
    [data-testid="stMultiSelect"] [data-tag] > span[title] {{ max-width: 8.5em; }}
    .ui-header-meta {{ align-items: flex-start; flex-direction: row; flex-wrap: wrap; gap: 4px 10px; }}
    .ui-logo {{ width: 36px; height: 36px; }}
    .ui-card {{ padding: var(--space-3); }}
    .ui-row {{ grid-template-columns: minmax(0, 1fr) auto; gap: 4px var(--space-2); }}
    .ui-row-detail {{ grid-column: 1 / -1; grid-row: 2; }}
    .ui-hero-price-wrap {{ text-align: left; }}
    .ui-hero-change {{ justify-content: flex-start; }}
    .ui-hero-top {{ flex-direction: column; gap: var(--space-2); }}
    .ui-list {{ max-height: 460px; }}
}}
@media (max-width: 359.98px) {{
    .ui-cards {{ grid-template-columns: minmax(0, 1fr); }}
    .ui-heat {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
}}
"""


def inject_styles() -> None:
    """Tasarım sistemini sayfaya ekler (her çalıştırmada bir kez çağrılır)."""
    st.html(f"<style>{_CSS}</style>")
