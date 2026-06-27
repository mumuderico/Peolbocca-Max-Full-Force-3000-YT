import streamlit as st

st.set_page_config(page_title="Content Creator Tool", layout="wide")
st.title("Content Creator Tool")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Script Writer", "Downloader", "Transcript", "Caption Remover"]
)

with tab1:
    st.info("Script Writer — coming soon")

with tab2:
    st.info("Downloader — coming soon")

with tab3:
    st.info("Transcript — coming soon")

with tab4:
    st.info("Caption Remover — coming soon")
