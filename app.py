import streamlit as st

from ui_text import APP_TITLE, DISCLAIMER

st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title(APP_TITLE)
st.write("Merhaba! Proje iskeleti hazır. Sekmeler sonraki aşamalarda eklenecek.")

st.divider()
st.caption(DISCLAIMER)
