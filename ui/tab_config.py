import time
import streamlit as st
import streamlit.components.v1 as components
import config
from modules.user_store import save_profile
from ui.user_cfg import get_key
from ui.i18n import t


def _link(label: str, url: str) -> str:
    return f'<a href="{url}" target="_blank" style="font-size:0.78rem;color:#7c3aed;">{label} ↗</a>'


def render_config():
    st.header(t("cfg_header"))

    active = st.session_state.get("active_profile")

    # ── API key inputs ────────────────────────────────────────────
    st.subheader(t("cfg_script_writer"))
    st.markdown(_link(t("cfg_groq_link"), "https://console.groq.com/keys"), unsafe_allow_html=True)
    groq_key = st.text_input(t("cfg_groq_key"), value=get_key("GROQ_API_KEY"), type="password", key="cfg_groq")

    st.divider()

    st.subheader(t("cfg_voiceover"))
    tts_provider = st.selectbox(
        t("cfg_tts_provider"),
        ["edge-tts", "elevenlabs"],
        index=0 if get_key("TTS_PROVIDER") == "edge-tts" else 1,
        key="cfg_tts",
    )
    st.markdown(_link(t("cfg_elevenlabs_link"), "https://elevenlabs.io/app/settings/api-keys"), unsafe_allow_html=True)
    elevenlabs_key = st.text_input(
        t("cfg_elevenlabs_key"),
        value=get_key("ELEVENLABS_API_KEY"),
        type="password",
        key="cfg_elevenlabs",
        help="Only needed when TTS Provider is set to elevenlabs",
    )

    st.divider()

    st.subheader(t("cfg_youtube"))
    st.markdown(_link(t("cfg_youtube_link"), "https://console.cloud.google.com/apis/library/youtube.googleapis.com"), unsafe_allow_html=True)
    youtube_key = st.text_input(t("cfg_youtube_key"), value=get_key("YOUTUBE_API_KEY"), type="password", key="cfg_youtube")

    st.divider()

    st.subheader(t("cfg_transcript"))
    st.markdown(_link(t("cfg_transcript_link"), "https://transcriptapi.com"), unsafe_allow_html=True)
    transcript_key = st.text_input(t("cfg_transcript_key"), value=get_key("TRANSCRIPTAPI_KEY"), type="password", key="cfg_transcript")

    st.divider()

    st.subheader(t("cfg_caption_remover"))
    caption_provider = st.selectbox(
        t("cfg_caption_provider"),
        ["local", "replicate"],
        index=0 if get_key("CAPTION_REMOVER_PROVIDER") == "local" else 1,
        key="cfg_caption_provider",
        help="local = NVIDIA GPU on this machine · replicate = cloud",
    )
    st.markdown(_link(t("cfg_replicate_link"), "https://replicate.com/account/api-tokens"), unsafe_allow_html=True)
    replicate_key = st.text_input(
        t("cfg_replicate_key"),
        value=get_key("REPLICATE_API_KEY"),
        type="password",
        key="cfg_replicate",
        help="Only needed when Caption Remover Provider is set to replicate",
    )

    st.divider()

    save_col, msg_col = st.columns([2, 3])
    with save_col:
        save_clicked = st.button(t("cfg_save_btn"), type="primary")
    with msg_col:
        msg_placeholder = st.empty()

    if save_clicked:
        keys = {
            "LLM_PROVIDER": "groq",
            "GROQ_API_KEY": groq_key,
            "TTS_PROVIDER": tts_provider,
            "ELEVENLABS_API_KEY": elevenlabs_key,
            "YOUTUBE_API_KEY": youtube_key,
            "TRANSCRIPTAPI_KEY": transcript_key,
            "CAPTION_REMOVER_PROVIDER": caption_provider,
            "REPLICATE_API_KEY": replicate_key,
            "SCRIPT_PRESET": st.session_state.get("gen_style_preset", "Default"),
        }
        save_profile(active, keys)
        st.session_state["user_keys"] = keys
        msg_placeholder.markdown(
            "<span style='color:#22c55e;font-weight:600;font-size:0.9rem;padding-top:0.55rem;display:block'>✓ Config saved</span>",
            unsafe_allow_html=True,
        )
        time.sleep(1)
        msg_placeholder.empty()

    components.html("""
    <script>
    (function() {
        function patch() {
            try {
                var doc = window.parent.document;
                doc.querySelectorAll('input[type="password"]').forEach(function(el) {
                    el.setAttribute('autocomplete', 'new-password');
                    el.setAttribute('data-lpignore', 'true');
                    el.setAttribute('data-form-type', 'other');
                });
            } catch(e) {}
        }
        patch();
        setTimeout(patch, 300);
        setTimeout(patch, 1000);
    })();
    </script>
    """, height=0)
