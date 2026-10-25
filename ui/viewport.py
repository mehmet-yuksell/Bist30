"""Ekran genişliği sınıfını (mobile / tablet / desktop) Python tarafına bildirir.

Streamlit, tarayıcının ekran genişliğini Python'a vermez; ancak grafik yükseklikleri,
varsayılan grafik dönemi ve tablo/liste seçimi gibi kararlar Python'da verilir. Bu yüzden
Streamlit'in yerleşik `st.components.v2` API'siyle (ek paket gerekmeden) küçük, görünmez
bir bileşen `window.innerWidth`'i ölçer ve kırılım noktası değiştiğinde bildirir.

İlk yüklemede (bileşen henüz ölçmeden) User-Agent başlığından bir tahmin yapılır; böylece
telefonda ilk çizim de mobil düzende olur ve çoğu zaman ek bir yeniden çalıştırma gerekmez.
Görsel düzenin (sütunların alt alta inmesi, boşluklar, yazı boyutları) asıl kaynağı yine
CSS medya sorgularıdır; bu değer yalnızca Python'un vermesi gereken kararlar içindir.
"""

import streamlit as st

MOBILE = "mobile"
TABLET = "tablet"
DESKTOP = "desktop"

MOBILE_MAX = 768  # < 768px -> mobile
TABLET_MAX = 1024  # 768-1023px -> tablet

_JS = f"""
export default function(component) {{
    const {{ data, setStateValue }} = component;
    const classify = () => {{
        const w = window.innerWidth;
        return w < {MOBILE_MAX} ? "{MOBILE}" : (w < {TABLET_MAX} ? "{TABLET}" : "{DESKTOP}");
    }};
    let last = data;
    const report = () => {{
        const current = classify();
        if (current !== last) {{
            last = current;
            setStateValue("device", current);
        }}
    }};
    report();
    let timer;
    const onResize = () => {{
        clearTimeout(timer);
        timer = setTimeout(report, 200);
    }};
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
}}
"""

_probe = st.components.v2.component("viewport_probe", js=_JS)


def _guess_from_user_agent() -> str:
    try:
        user_agent = st.context.headers.get("User-Agent", "") or ""
    except Exception:
        return DESKTOP
    if "iPad" in user_agent or ("Android" in user_agent and "Mobile" not in user_agent):
        return TABLET
    if "Mobi" in user_agent or "iPhone" in user_agent:
        return MOBILE
    return DESKTOP


def detect_device() -> str:
    """Geçerli ekran sınıfını döndürür: 'mobile', 'tablet' veya 'desktop'."""
    previous = st.session_state.get("_device") or _guess_from_user_agent()

    with st.container(key="viewport_probe"):
        result = _probe(key="viewport", data=previous, on_device_change=lambda: None)

    device = getattr(result, "device", None) or previous
    if device not in (MOBILE, TABLET, DESKTOP):
        device = DESKTOP
    st.session_state["_device"] = device
    return device
