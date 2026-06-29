import streamlit as st
import config
from ui.user_cfg import get_key
from youtube_transcript_api import TranscriptsDisabled, NoTranscriptFound
from modules.transcriber import (
    get_transcript,
    translate_text,
    SUPPORTED_LANGUAGES,
    extract_video_id,
)
from modules.script_generator import save_script, delete_script, list_scripts
from ui.i18n import t


def render_transcript():
    st.header(t("tr_header"))

    if not get_key("TRANSCRIPTAPI_KEY"):
        st.info(t("tr_tip"), icon="💡")

    url = st.text_input(t("tr_url_label"), placeholder=t("tr_url_placeholder"))
    include_timestamps = st.checkbox(t("tr_timestamps"))

    if st.button(t("tr_get_btn"), type="primary"):
        if not url.strip():
            st.error(t("tr_enter_url"))
            return

        if not get_key("TRANSCRIPTAPI_KEY"):
            try:
                extract_video_id(url.strip())
            except ValueError:
                st.error(t("tr_invalid_url"))
                return

        with st.spinner(t("tr_fetching")):
            try:
                transcript = get_transcript(
                    url.strip(),
                    include_timestamps=include_timestamps,
                    api_key=get_key("TRANSCRIPTAPI_KEY"),
                )
                st.session_state["transcript"] = transcript
                st.session_state["transcript_url"] = url.strip()
            except TranscriptsDisabled:
                st.error(t("tr_captions_disabled"))
                return
            except NoTranscriptFound:
                st.error(t("tr_no_transcript"))
                return
            except Exception as e:
                msg = str(e)
                if "401" in msg or "403" in msg:
                    st.error(t("tr_invalid_key"))
                elif "402" in msg:
                    st.error(t("tr_credits_exhausted"))
                else:
                    st.error(t("tr_fetch_error", error=e))
                return

    if "transcript" in st.session_state:
        left_col, right_col = st.columns(2)

        LABEL = "font-size:0.8rem;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;margin-bottom:4px;"

        with left_col:
            st.markdown(f'<p style="{LABEL}color:#7c3aed;">{t("tr_transcript_label")}</p>', unsafe_allow_html=True)
            st.text_area("", value=st.session_state["transcript"], height=400, key="transcript_display")

            script_filename = "transcript_style.txt"
            already_saved = script_filename in list_scripts(config.SCRIPTS_DIR)
            use_as_script = st.toggle(
                t("tr_use_as_style"),
                value=already_saved,
                key="transcript_as_script",
            )
            if use_as_script and not already_saved:
                save_script(script_filename, st.session_state["transcript"], config.SCRIPTS_DIR)
                st.success(t("tr_saved_style"))
            elif not use_as_script and already_saved:
                delete_script(script_filename, config.SCRIPTS_DIR)
                st.info(t("tr_removed_style"))

            st.download_button(
                t("tr_download_transcript"),
                data=st.session_state["transcript"],
                file_name="transcript.txt",
                mime="text/plain",
                use_container_width=True,
            )

        with right_col:
            st.markdown(f'<p style="{LABEL}color:#0ea5e9;">{t("tr_translation_label")}</p>', unsafe_allow_html=True)
            lang_col, btn_col = st.columns([3, 1])
            with lang_col:
                target_lang_name = st.selectbox(t("tr_translate_to"), options=list(SUPPORTED_LANGUAGES.keys()), label_visibility="collapsed")
            with btn_col:
                st.markdown("<div style='padding-top:4px'>", unsafe_allow_html=True)
                do_translate = st.button(t("tr_translate_btn"), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            if do_translate:
                lang_code = SUPPORTED_LANGUAGES[target_lang_name]
                with st.spinner(t("tr_translating", lang=target_lang_name)):
                    translated = translate_text(st.session_state["transcript"], lang_code)
                    st.session_state["translated"] = translated

            translated_value = st.session_state.get("translated", "")
            st.text_area("", value=translated_value, height=400, key="translated_display", placeholder=t("tr_translation_placeholder"))
            st.download_button(
                t("tr_download_translation"),
                data=translated_value or " ",
                file_name="translated_transcript.txt",
                mime="text/plain",
                use_container_width=True,
                disabled=not translated_value,
            )
