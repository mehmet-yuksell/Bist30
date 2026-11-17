"""Takip Listem sekmesi: hisse ekleme/düzenleme, karar özeti, iki vadeli tablo, JSON yedek.

Liste tarayıcıda saklanır (ui/takip_deposu.py). Fiyat verisi BIST 100 taramasıyla aynı toplu
indirmeden gelir: BIST 100 dışı takip hisseleri app.py'de toplu indirmenin kod listesine eklenir.
"""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

import feed
import market
import panel_veri as pv
import takip
from data import DataFetchError, load_all_bist_symbols
from ui import kalite_ui, takip_deposu
from ui.components import callout, error_state, section_title, skeleton_html, tagged_list
from ui.controls import symbol_formatter
from ui.format import fmt_num, fmt_pct
from ui.viewport import MOBILE
from ui_text import (
    SYMBOL_PLACEHOLDER,
    TK_ADD_BUTTON,
    TK_ADD_CODE,
    TK_ADD_HELP,
    TK_ADD_NOTE,
    TK_ADD_PRICE,
    TK_ADD_QTY,
    TK_ADD_TITLE,
    TK_ADDED,
    TK_BACKUP_TITLE,
    TK_BAD_CODE,
    TK_CAPTION,
    TK_COL_CHANGE,
    TK_COL_CODE,
    TK_COL_GRADE,
    TK_COL_NOTE,
    TK_COL_PL_PCT,
    TK_COL_PL_TL,
    TK_COL_PRESSURE,
    TK_COL_PRICE,
    TK_COL_SCORE,
    TK_COL_SIGNAL,
    TK_COL_STOP,
    TK_COL_TARGET,
    TK_DOWNLOAD,
    TK_EDIT_DELETE,
    TK_EDIT_SAVE,
    TK_EDIT_SAVED,
    TK_EDIT_TITLE,
    TK_EMPTY,
    TK_HELD,
    TK_LEVEL_NOTE,
    TK_LOADING,
    TK_NO_DATA,
    TK_NOT_FOUND,
    TK_SIGNAL_BUY,
    TK_SUMMARY_CAPTION,
    TK_SUMMARY_NONE,
    TK_SUMMARY_TITLE,
    TK_TABLE_TITLE,
    TK_TITLE,
    TK_UPLOAD,
    TK_UPLOAD_APPLY,
    TK_UPLOAD_BAD,
    TK_UPLOAD_OK,
    TK_VADE_SHORT,
    VADE_BUGUN,
    VADE_ONCE,
)

ENDEKS = "XU100"
BOS = "—"


@st.cache_data(max_entries=8, show_spinner=False)
def _satirlar(data_key: str, liste_json: str, _histories: dict) -> list[dict]:
    """Takip hisselerinin satırları; aynı veri ve aynı liste için bir kez hesaplanır."""
    endeks = pv.endeks_girdisi(_histories.get(ENDEKS))
    return [takip.satir(k, _histories.get(k["kod"]), endeks) for k in takip.json_oku(liste_json)]


def _not_bul(skor: float, vade: str) -> str | None:
    return kalite_ui.ozet(skor, vade, True if vade == pv.ORTA else None)["grade"]


def _son_sinyal(v: dict | None, vade: str) -> str:
    if not v:
        return BOS
    al, sat = v["al"], v["sat"]
    if not al and not sat:
        return BOS
    if al and (not sat or al["once"] <= sat["once"]):
        ad, once = TK_SIGNAL_BUY, al["once"]
    else:
        ad, once = sat["ad"], sat["once"]
    zaman = VADE_BUGUN[vade] if once == 0 else VADE_ONCE[vade].format(days=once)
    return f"{ad} · {zaman.lower()}"


# ---------------------------------------------------------------------------
# Ekleme, düzenleme, yedek
# ---------------------------------------------------------------------------

def _ekleme_formu(liste: list[dict]) -> None:
    tum = load_all_bist_symbols()
    with st.expander(TK_ADD_TITLE, icon=":material/add:", expanded=not liste):
        with st.form("tk_ekle", clear_on_submit=True, border=False):
            kod = st.selectbox(TK_ADD_CODE, options=sorted(tum), index=None, accept_new_options=True,
                               format_func=symbol_formatter(tum), placeholder=SYMBOL_PLACEHOLDER, key="tk_kod")
            with st.container(horizontal=True, gap="small"):
                alis = st.number_input(TK_ADD_PRICE, min_value=0.0, value=None, step=0.01, format="%.2f", key="tk_alis")
                adet = st.number_input(TK_ADD_QTY, min_value=0, value=None, step=1, key="tk_adet")
            not_ = st.text_input(TK_ADD_NOTE, key="tk_not", max_chars=200)
            st.caption(TK_ADD_HELP)
            gonder = st.form_submit_button(TK_ADD_BUTTON, icon=":material/star:")
        if not gonder:
            return
        temiz = takip.kod_temizle(kod)
        if temiz is None:
            st.warning(TK_BAD_CODE)
            return
        if temiz not in tum:
            # Bilinen ~630 hisse dışındaysa Yahoo'da verisi var mı, bir kez kontrol edilir
            try:
                feed.single(temiz, date.today() - timedelta(days=40), date.today())
            except DataFetchError:
                st.warning(TK_NOT_FOUND.format(kod=temiz))
                return
        takip_deposu.kaydet(takip.ekle(liste, takip.yeni_kayit(temiz, alis, adet, not_)))
        st.toast(TK_ADDED.format(kod=temiz))
        st.rerun()  # tüm sayfa: toplu indirme yeni kodu da içersin, tarayıcıya kaydedilsin


def _duzenleme(liste: list[dict]) -> None:
    with st.expander(TK_EDIT_TITLE, icon=":material/edit:"):
        tablo = pd.DataFrame([{TK_COL_CODE: k["kod"], TK_ADD_PRICE: k["alis"], TK_ADD_QTY: k["adet"],
                               TK_COL_NOTE: k["not"], TK_EDIT_DELETE: False} for k in liste])
        duzenli = st.data_editor(
            tablo, hide_index=True, width="stretch", key="tk_editor", num_rows="fixed",
            column_config={
                TK_COL_CODE: st.column_config.TextColumn(TK_COL_CODE, disabled=True),
                TK_ADD_PRICE: st.column_config.NumberColumn(TK_ADD_PRICE, min_value=0.0, format="%.2f"),
                TK_ADD_QTY: st.column_config.NumberColumn(TK_ADD_QTY, min_value=0, step=1),
                TK_EDIT_DELETE: st.column_config.CheckboxColumn(TK_EDIT_DELETE),
            },
        )
        if st.button(TK_EDIT_SAVE, icon=":material/save:", key="tk_kaydet"):
            yeni = [takip.yeni_kayit(r[TK_COL_CODE], r[TK_ADD_PRICE], r[TK_ADD_QTY], r[TK_COL_NOTE] or "")
                    for _, r in duzenli.iterrows() if not r[TK_EDIT_DELETE]]
            takip_deposu.kaydet(yeni)
            st.toast(TK_EDIT_SAVED)
            st.rerun()


def _yedek(liste: list[dict]) -> None:
    with st.expander(TK_BACKUP_TITLE, icon=":material/download:"):
        st.download_button(TK_DOWNLOAD, data=takip.json_yaz(liste), file_name="takip_listem.json",
                           mime="application/json", icon=":material/download:", key="tk_indir")
        dosya = st.file_uploader(TK_UPLOAD, type=["json"], key="tk_yukle")
        if dosya is not None and st.button(TK_UPLOAD_APPLY, key="tk_yukle_uygula"):
            try:
                yeni = takip.json_oku(dosya.getvalue())
            except ValueError as exc:
                st.warning(TK_UPLOAD_BAD.format(hata=exc))
                return
            takip_deposu.kaydet(yeni)
            st.toast(TK_UPLOAD_OK.format(n=len(yeni)))
            st.rerun()


# ---------------------------------------------------------------------------
# Karar özeti ve tablo
# ---------------------------------------------------------------------------

def _karar_ozeti(satirlar: list[dict]) -> None:
    section_title(TK_SUMMARY_TITLE, TK_SUMMARY_CAPTION)
    gruplar = takip.karar_ozeti(satirlar, _not_bul)
    dolu = {g: v for g, v in gruplar.items() if v}
    if not dolu:
        callout("empty", None, TK_SUMMARY_NONE)
        return
    for grup, maddeler in dolu.items():
        if grup == "al":
            kalite_ui.alim_uyarisi()
        tur = "warn" if grup in ("sat", "dikkat") else "info"
        callout(tur, takip.GRUPLAR[grup], [f"{kod}: {neden}" for kod, neden in maddeler])


def _tablo(satirlar: list[dict]) -> pd.DataFrame:
    kayitlar = []
    for s in satirlar:
        r = {TK_COL_CODE: s["kod"], TK_HELD: "✓" if takip.elimde(s) else ""}
        if not s.get("veri"):
            r[TK_COL_PRICE] = TK_NO_DATA
            kayitlar.append(r)
            continue
        r[TK_COL_PRICE] = fmt_num(s["fiyat"], 2)
        r[TK_COL_CHANGE] = fmt_pct(s["degisim"])
        r[TK_COL_PL_PCT] = fmt_pct(s["kz_pct"]) if s.get("kz_pct") is not None else BOS
        r[TK_COL_PL_TL] = fmt_num(s["kz_tl"], 0) if s.get("kz_tl") is not None else BOS
        for vade in (pv.KISA, pv.ORTA):
            v, etiket = s.get(vade), TK_VADE_SHORT[vade]
            r[TK_COL_SCORE.format(v=etiket)] = fmt_num(v["skor"], 0) if v else BOS
            r[TK_COL_GRADE.format(v=etiket)] = (_not_bul(v["skor"], vade) or BOS) if v and v["skor"] >= 60 else BOS
            r[TK_COL_PRESSURE.format(v=etiket)] = fmt_num(v["satis_baskisi"], 0) if v else BOS
            r[TK_COL_SIGNAL.format(v=etiket)] = _son_sinyal(v, vade)
            r[TK_COL_STOP.format(v=etiket)] = fmt_num(v["stop"], 2) if v else BOS
            r[TK_COL_TARGET.format(v=etiket)] = fmt_num(v["hedef"], 2) if v else BOS
        r[TK_COL_NOTE] = s.get("not", "")
        kayitlar.append(r)
    return pd.DataFrame(kayitlar)


def _mobil_liste(satirlar: list[dict]) -> None:
    satir_listesi = []
    for s in satirlar:
        if not s.get("veri"):
            satir_listesi.append({"ticker": s["kod"], "name": TK_NO_DATA, "tags": []})
            continue
        parcalar = []
        for vade in (pv.KISA, pv.ORTA):
            v = s.get(vade)
            if v:
                parcalar.append(f"{TK_VADE_SHORT[vade]}: skor {fmt_num(v['skor'], 0)}, baskı "
                                f"{fmt_num(v['satis_baskisi'], 0)}, {_son_sinyal(v, vade)}")
        kz = f"K/Z {fmt_pct(s['kz_pct'])}" if s.get("kz_pct") is not None else ""
        satir_listesi.append({
            "ticker": s["kod"], "name": " · ".join(x for x in (fmt_num(s["fiyat"], 2), kz, s.get("not", "")) if x),
            "tags": [(TK_HELD, "accent")] if takip.elimde(s) else [],
            "meta": " | ".join(parcalar), "change": s["degisim"],
        })
    tagged_list(satir_listesi)


@st.fragment(run_every=timedelta(minutes=market.REFRESH_MINUTES))
def render(device: str, ctx: dict) -> None:
    section_title(TK_TITLE, TK_CAPTION)
    if not takip_deposu.yuklendi_mi():
        callout("info", None, TK_LOADING)
    liste = st.session_state.get(takip_deposu.LISTE, [])
    _ekleme_formu(liste)
    if not liste:
        callout("empty", None, TK_EMPTY)
        _yedek(liste)
        return

    loading = st.empty()
    loading.html(skeleton_html("list"))
    try:
        data = feed.batch(ctx["tickers"])  # Tarama ile aynı toplu indirme (aynı önbellek anahtarı)
    except DataFetchError as exc:
        loading.empty()
        error_state(str(exc), key="tk_retry")
        return
    satirlar = _satirlar(data.fetched_at.isoformat(), takip.json_yaz(liste), data.data)
    loading.empty()

    _karar_ozeti(satirlar)
    section_title(TK_TABLE_TITLE)
    if device == MOBILE:
        _mobil_liste(satirlar)
    else:
        st.dataframe(_tablo(satirlar), hide_index=True, width="stretch")
    st.caption(TK_LEVEL_NOTE)
    _duzenleme(liste)
    _yedek(liste)
