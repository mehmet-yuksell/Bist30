"""Takip listesinin tarayıcıda (localStorage) saklanması.

Neden localStorage ve neden bu bileşen: liste kişiseldir ve sunucuda hesap/veritabanı yoktur;
Streamlit Cloud'un diski de kalıcı değildir. Tarayıcının localStorage'ı listeyi aynı tarayıcıda
kalıcı tutar. Okuma/yazma için Streamlit'in yerleşik `st.components.v2` API'siyle küçük bir JS
bileşeni kullanılır (ui/viewport.py ile aynı yöntem): ek paket gerekmez ve requirements.txt
değişmez. Sınırlama: liste başka tarayıcıya/cihaza taşınmaz; bunun için JSON indir/yükle var.

Akış: ilk çalıştırmada JS kaydı okuyup bir kez "kayit" durumu olarak gönderir (sayfa yeniden
çalışır, liste oturuma yüklenir). Liste değişince kaydet() yeni JSON'u bir sonraki çalıştırmada
bileşene verir, JS onu localStorage'a yazar.
"""

import streamlit as st

import takip

DEPO_ANAHTARI = "bist_paneli_takip_listesi"
LISTE = "takip_listesi"
_YUKLENDI = "_takip_yuklendi"
_KAYDET = "_takip_kaydet"

_JS = f"""
export default function(component) {{
    const {{ data, setStateValue }} = component;
    if (data && typeof data.kaydet === "string") {{
        try {{ window.localStorage.setItem("{DEPO_ANAHTARI}", data.kaydet); }} catch (e) {{}}
    }}
    if (data && !data.yuklendi) {{
        let deger = "";
        try {{ deger = window.localStorage.getItem("{DEPO_ANAHTARI}") || ""; }} catch (e) {{}}
        setStateValue("kayit", deger);
    }}
}}
"""

_depo = st.components.v2.component("takip_deposu", js=_JS)


def senkronize() -> list[dict]:
    """Her çalıştırmada (sekmelerden önce) çağrılır; oturumdaki takip listesini döndürür."""
    yuklendi = st.session_state.get(_YUKLENDI, False)
    kaydedilecek = st.session_state.pop(_KAYDET, None)
    with st.container(key="takip_deposu"):
        sonuc = _depo(key="takip_deposu_bilesen", data={"kaydet": kaydedilecek, "yuklendi": yuklendi},
                      on_kayit_change=lambda: None)
    if not yuklendi:
        kayit = getattr(sonuc, "kayit", None)
        if kayit is not None:
            try:
                st.session_state[LISTE] = takip.json_oku(kayit)
            except ValueError:
                st.session_state[LISTE] = []  # bozuk kayıt: boş listeyle devam (üzerine yazılır)
            st.session_state[_YUKLENDI] = True
    return st.session_state.get(LISTE, [])


def yuklendi_mi() -> bool:
    return bool(st.session_state.get(_YUKLENDI))


def kaydet(liste: list[dict]) -> None:
    """Listeyi oturuma yazar ve bir sonraki çalıştırmada tarayıcıya kaydettirir (ardından st.rerun)."""
    st.session_state[LISTE] = liste
    st.session_state[_YUKLENDI] = True
    st.session_state[_KAYDET] = takip.json_yaz(liste)
