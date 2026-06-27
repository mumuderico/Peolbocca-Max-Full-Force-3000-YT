import streamlit as st
from ui.tab_script_writer import render_script_writer
from ui.tab_downloader import render_downloader

st.set_page_config(page_title="Content Creator Tool", layout="wide")
st.title("Content Creator Tool")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Script Writer", "Downloader", "Transcript", "Caption Remover"]
)

with tab1:
    render_script_writer()

with tab2:
    render_downloader()

with tab3:
    st.info("Transcript — coming soon")

with tab4:
    st.info("Caption Remover — coming soon")
