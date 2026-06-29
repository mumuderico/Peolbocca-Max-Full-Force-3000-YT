import streamlit as st
from ui.tab_script_writer import render_script_writer
from ui.tab_downloader import render_downloader
from ui.tab_transcript import render_transcript
from ui.tab_caption_remover import render_caption_remover
from ui.tab_video_search import render_video_search
from ui.tab_config import render_config
from ui.i18n import t
from ui.tab_channel_ranking import render_channel_ranking

st.set_page_config(page_title="Peolbocca Max Full Force 3000 YT", layout="wide", page_icon="🎬")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Background */
.stApp {
    background: #0d0d14;
}

/* Hide Streamlit chrome */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }

/* Headings */
h1 {
    background: linear-gradient(135deg, #a78bfa 0%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.4rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.5px;
    padding-bottom: 4px;
}

h2 {
    color: #e2e8f0 !important;
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.2px;
}

h3 {
    color: #cbd5e1 !important;
    font-weight: 600 !important;
}

p, label, .stMarkdown {
    color: #94a3b8;
}

/* Tabs */
[data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 14px !important;
    padding: 5px !important;
    gap: 4px !important;
    border: 1px solid rgba(255,255,255,0.07);
}

[data-baseweb="tab"] {
    border-radius: 10px !important;
    color: #64748b !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    padding: 8px 22px !important;
    transition: all 0.2s ease !important;
}

[data-baseweb="tab"]:hover {
    color: #e2e8f0 !important;
    background: rgba(255,255,255,0.06) !important;
}

[aria-selected="true"][data-baseweb="tab"] {
    background: linear-gradient(135deg, #7c3aed, #0ea5e9) !important;
    color: white !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 15px rgba(124,58,237,0.35) !important;
}

[data-baseweb="tab-highlight"] {
    display: none !important;
}

[data-baseweb="tab-border"] {
    display: none !important;
}

/* Primary button */
[data-testid="stBaseButton-primary"] > button,
button[kind="primary"],
.stButton > button[data-testid*="primary"] {
    background: linear-gradient(135deg, #7c3aed, #0ea5e9) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 0.55rem 1.8rem !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 15px rgba(124,58,237,0.3) !important;
}

/* All buttons */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    transition: all 0.2s ease !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    background: rgba(255,255,255,0.06) !important;
    color: #cbd5e1 !important;
}

.stButton > button:hover {
    background: rgba(255,255,255,0.1) !important;
    border-color: rgba(124,58,237,0.5) !important;
    color: #e2e8f0 !important;
    transform: translateY(-1px) !important;
}

/* Download button */
[data-testid="stDownloadButton"] > button {
    background: rgba(16,185,129,0.15) !important;
    border: 1px solid rgba(16,185,129,0.3) !important;
    color: #34d399 !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
}

[data-testid="stDownloadButton"] > button:hover {
    background: rgba(16,185,129,0.25) !important;
}

/* Text inputs */
.stTextInput input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-size: 0.95rem !important;
    padding: 0.6rem 0.9rem !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}

.stTextInput input:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.18) !important;
    outline: none !important;
}

/* Text area */
.stTextArea textarea {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-size: 0.93rem !important;
    line-height: 1.6 !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}

.stTextArea textarea:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.18) !important;
    outline: none !important;
}

/* Selectbox */
[data-baseweb="select"] > div:first-child {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}

[data-baseweb="select"] svg {
    fill: #64748b !important;
}

/* Dropdown menu */
[data-baseweb="popover"] {
    background: #1e1e2e !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
}

[data-baseweb="menu"] {
    background: #1e1e2e !important;
}

[data-baseweb="option"] {
    color: #cbd5e1 !important;
}

[data-baseweb="option"]:hover {
    background: rgba(124,58,237,0.15) !important;
}

/* Expanders */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    overflow: hidden;
    margin-bottom: 8px;
}

[data-testid="stExpander"] summary {
    color: #cbd5e1 !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    padding: 0.7rem 1rem !important;
}

[data-testid="stExpander"] summary:hover {
    background: rgba(255,255,255,0.04) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: rgba(124,58,237,0.06) !important;
    border: 2px dashed rgba(124,58,237,0.35) !important;
    border-radius: 12px !important;
    transition: all 0.2s ease !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: rgba(124,58,237,0.6) !important;
    background: rgba(124,58,237,0.1) !important;
}

[data-testid="stFileUploaderDropzone"] {
    background: transparent !important;
    border: none !important;
}

/* Divider */
hr {
    border-color: rgba(255,255,255,0.07) !important;
    margin: 1.5rem 0 !important;
}

/* Alert boxes */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-size: 0.88rem !important;
}

/* Spinner */
[data-testid="stSpinner"] {
    color: #7c3aed !important;
}

/* Audio player */
audio {
    border-radius: 10px;
    width: 100%;
    margin-top: 8px;
}

/* Column separator feel */
[data-testid="column"]:last-child {
    border-left: 1px solid rgba(255,255,255,0.06);
    padding-left: 1.5rem !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); }
::-webkit-scrollbar-thumb { background: #4c1d95; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #7c3aed; }
</style>
""", unsafe_allow_html=True)

LANGUAGES = {
    "🇺🇸 English": "English",
    "🇧🇷 Portuguese": "Portuguese",
}

title_col, lang_col, btn_col = st.columns([6, 2, 1])
with title_col:
    st.title(f"🎬 {t('app_title')}")
with lang_col:
    st.markdown("<div style='padding-top:1.4rem'>", unsafe_allow_html=True)
    selected_lang_label = st.selectbox(
        "Language",
        list(LANGUAGES.keys()),
        label_visibility="collapsed",
        key="app_language_label",
    )
    st.session_state["app_language"] = LANGUAGES[selected_lang_label]
    st.markdown("</div>", unsafe_allow_html=True)
with btn_col:
    st.markdown("<div style='padding-top:1.6rem'>", unsafe_allow_html=True)
    if st.button("🔄 Rerun", help="Refresh the app"):
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    f"✍️  {t('tab_script_writer')}",
    f"⬇️  {t('tab_downloader')}",
    f"📝  {t('tab_transcript')}",
    f"🎞️  {t('tab_caption_remover')}",
    f"🔎  {t('tab_video_search')}",
    f"🏆  {t('tab_channel_rankings')}",
    f"⚙️  {t('tab_config')}",
])

with tab1:
    render_script_writer()

with tab2:
    render_downloader()

with tab3:
    render_transcript()

with tab4:
    render_caption_remover()

with tab5:
    render_video_search()

with tab6:
    render_channel_ranking()

with tab7:
    render_config()
