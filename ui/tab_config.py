import importlib
import os
import re

import streamlit as st
import config
from ui.i18n import t

_CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.py"))


def _save(updates: dict) -> None:
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    for key, value in updates.items():
        content = re.sub(
            rf'^({re.escape(key)}\s*=\s*)["\'].*?["\']',
            rf'\g<1>"{value}"',
            content,
            flags=re.MULTILINE,
        )
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    importlib.reload(config)


def _link(label: str, url: str) -> str:
    return f'<a href="{url}" target="_blank" style="font-size:0.78rem;color:#7c3aed;">{label} ↗</a>'


def render_config():
    st.header(t("cfg_header"))
    st.caption(t("cfg_caption"))

    st.subheader(t("cfg_script_writer"))
    st.markdown(_link(t("cfg_groq_link"), "https://console.groq.com/keys"), unsafe_allow_html=True)
    groq_key = st.text_input(t("cfg_groq_key"), value=config.GROQ_API_KEY, type="password", key="cfg_groq")

    st.divider()

    st.subheader(t("cfg_voiceover"))
    tts_provider = st.selectbox(
        t("cfg_tts_provider"),
        ["edge-tts", "elevenlabs"],
        index=0 if config.TTS_PROVIDER == "edge-tts" else 1,
        key="cfg_tts",
    )
    st.markdown(_link(t("cfg_elevenlabs_link"), "https://elevenlabs.io/app/settings/api-keys"), unsafe_allow_html=True)
    elevenlabs_key = st.text_input(
        t("cfg_elevenlabs_key"),
        value=config.ELEVENLABS_API_KEY,
        type="password",
        key="cfg_elevenlabs",
        help="Only needed when TTS Provider is set to elevenlabs",
    )

    st.divider()

    st.subheader(t("cfg_youtube"))
    st.markdown(_link(t("cfg_youtube_link"), "https://console.cloud.google.com/apis/library/youtube.googleapis.com"), unsafe_allow_html=True)
    youtube_key = st.text_input(t("cfg_youtube_key"), value=config.YOUTUBE_API_KEY, type="password", key="cfg_youtube")

    st.divider()

    st.subheader(t("cfg_transcript"))
    st.markdown(_link(t("cfg_transcript_link"), "https://transcriptapi.com"), unsafe_allow_html=True)
    transcript_key = st.text_input(t("cfg_transcript_key"), value=config.TRANSCRIPTAPI_KEY, type="password", key="cfg_transcript")

    st.divider()

    st.subheader(t("cfg_caption_remover"))
    caption_provider = st.selectbox(
        t("cfg_caption_provider"),
        ["local", "replicate"],
        index=0 if config.CAPTION_REMOVER_PROVIDER == "local" else 1,
        key="cfg_caption_provider",
        help="local = NVIDIA GPU on this machine · replicate = cloud",
    )
    st.markdown(_link(t("cfg_replicate_link"), "https://replicate.com/account/api-tokens"), unsafe_allow_html=True)
    replicate_key = st.text_input(
        t("cfg_replicate_key"),
        value=config.REPLICATE_API_KEY,
        type="password",
        key="cfg_replicate",
        help="Only needed when Caption Remover Provider is set to replicate",
    )

    st.divider()

    if st.button(t("cfg_save_btn"), type="primary"):
        _save({
            "LLM_PROVIDER": "groq",
            "GROQ_API_KEY": groq_key,
            "TTS_PROVIDER": tts_provider,
            "ELEVENLABS_API_KEY": elevenlabs_key,
            "YOUTUBE_API_KEY": youtube_key,
            "TRANSCRIPTAPI_KEY": transcript_key,
            "CAPTION_REMOVER_PROVIDER": caption_provider,
            "REPLICATE_API_KEY": replicate_key,
        })
        st.success(t("cfg_saved"))
        st.rerun()
