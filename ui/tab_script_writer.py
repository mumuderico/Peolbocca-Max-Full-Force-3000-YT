import os
import streamlit as st
import config
from modules.script_generator import (
    create_preset,
    delete_preset,
    delete_script,
    generate_script,
    generate_voiceover,
    list_presets,
    list_scripts,
    load_user_scripts,
    save_script,
)
from ui.i18n import t

LANGUAGES = ["English", "Portuguese", "Spanish", "French", "German", "Italian", "Japanese", "Korean"]
PLATFORMS = ["YouTube Shorts", "Long Form"]

_PACE_OPTIONS = ["Very Slow", "Slow", "Normal", "Fast", "Very Fast"]
_PACE_TO_RATE  = {"Very Slow": "-50%", "Slow": "-25%", "Normal": "+0%", "Fast": "+25%", "Very Fast": "+50%"}
_PITCH_OPTIONS = ["Lower", "Normal", "Higher"]
_PITCH_TO_HZ   = {"Lower": "-5Hz", "Normal": "+0Hz", "Higher": "+5Hz"}


def render_script_writer():
    left_col, right_col = st.columns([3, 1])

    with left_col:
        st.markdown(f"""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="margin-bottom: 0.25rem;">{t('sw_header')}</h2>
            <p style="font-size: 0.88rem; color: #64748b; margin: 0;">
                {t('sw_caption')}
            </p>
        </div>
        """, unsafe_allow_html=True)

        topic = st.text_input(t("sw_topic"), placeholder="e.g. 5 ways to save money this year")
        col_platform, col_language = st.columns(2)
        with col_platform:
            platform = st.selectbox(t("sw_format"), PLATFORMS)
        with col_language:
            default_lang = st.session_state.get("app_language", "English")
            default_idx = LANGUAGES.index(default_lang) if default_lang in LANGUAGES else 0
            language = st.selectbox(t("sw_language"), LANGUAGES, index=default_idx)

        presets = list_presets(config.SCRIPTS_DIR)
        style_preset = st.selectbox(
            t("sw_style_preset"),
            presets,
            key="gen_style_preset",
            help=t("sw_preset_help"),
        )

        st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)

        if st.button(t("sw_generate_btn"), type="primary", use_container_width=True):
            if not topic.strip():
                st.error(t("sw_enter_name"))
            else:
                key_map = {
                    "groq": config.GROQ_API_KEY,
                    "gemini": config.GEMINI_API_KEY,
                    "anthropic": config.ANTHROPIC_API_KEY,
                    "openai": config.OPENAI_API_KEY,
                }
                api_key = key_map.get(config.LLM_PROVIDER, "")
                if not api_key:
                    st.error(t("sw_no_api_key", provider=config.LLM_PROVIDER.upper()))
                else:
                    with st.spinner(t("sw_crafting")):
                        try:
                            user_scripts = load_user_scripts(config.SCRIPTS_DIR, style_preset)
                            script = generate_script(topic, platform, language, user_scripts, api_key, config.LLM_PROVIDER)
                            st.session_state["generated_script"] = script
                            st.session_state["script_output"] = script
                        except Exception as e:
                            msg = str(e)
                            if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
                                st.error(t("sw_quota_error"))
                            elif "401" in msg or "API_KEY" in msg or "invalid" in msg.lower():
                                st.error(t("sw_key_error"))
                            else:
                                st.error(t("sw_gen_error", error=e))

        if "generated_script" in st.session_state:
            st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)
            st.markdown(f"""
            <p style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em;
                       color: #7c3aed; font-weight: 600; margin-bottom: 4px;">
                {t('sw_generated_label')}
            </p>
            """, unsafe_allow_html=True)
            st.text_area(
                label="",
                value=st.session_state["generated_script"],
                height=320,
                key="script_output",
            )
            st.download_button(
                t("sw_download_txt"),
                data=st.session_state["generated_script"],
                file_name="script.txt",
                mime="text/plain",
            )

            st.divider()

            st.markdown(f"""
            <p style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em;
                       color: #0ea5e9; font-weight: 600; margin-bottom: 4px;">
                {t('sw_voiceover_label')}
            </p>
            """, unsafe_allow_html=True)

            voc_tab, notes_tab = st.tabs([t("sw_voc_tab_generate"), t("sw_voc_tab_notes")])

            with notes_tab:
                st.caption(t("sw_notes_caption"))
                st.radio(t("sw_voice"), ["Female", "Male"], horizontal=True, key="vo_gender")
                st.select_slider(t("sw_pace"), options=_PACE_OPTIONS, value="Normal", key="vo_pace")
                st.select_slider(t("sw_pitch"), options=_PITCH_OPTIONS, value="Normal", key="vo_pitch")
                st.text_area(
                    t("sw_style_notes_label"),
                    placeholder=t("sw_style_notes_placeholder"),
                    key="vo_notes",
                    height=80,
                )

            with voc_tab:
                pace   = st.session_state.get("vo_pace", "Normal")
                pitch  = st.session_state.get("vo_pitch", "Normal")
                gender = st.session_state.get("vo_gender", "Female")
                st.caption(t("sw_voc_settings_caption", gender=gender, pace=pace, pitch=pitch))
                if st.button(t("sw_generate_voc_btn")):
                    if config.TTS_PROVIDER == "elevenlabs" and not config.ELEVENLABS_API_KEY:
                        st.error(t("sw_elevenlabs_missing"))
                    else:
                        audio_path = os.path.join(config.DOWNLOADS_DIR, "voiceover.mp3")
                        with st.spinner(t("sw_generating_voc")):
                            generate_voiceover(
                                st.session_state["generated_script"],
                                audio_path,
                                config.TTS_PROVIDER,
                                config.ELEVENLABS_API_KEY,
                                rate=_PACE_TO_RATE[pace],
                                pitch=_PITCH_TO_HZ[pitch],
                                gender=gender,
                            )
                        st.audio(audio_path, format="audio/mp3")
                        with open(audio_path, "rb") as f:
                            st.download_button(t("sw_download_voc"), data=f, file_name="voiceover.mp3", mime="audio/mpeg")

    with right_col:
        st.markdown(f"""
        <div style="margin-bottom: 1rem;">
            <h2 style="margin-bottom: 0.2rem; font-size: 1rem !important;">{t('sw_style_library_header')}</h2>
            <p style="font-size: 0.78rem; color: #475569; margin: 0; line-height: 1.4;">
                {t('sw_style_library_caption')}
            </p>
        </div>
        """, unsafe_allow_html=True)

        presets = list_presets(config.SCRIPTS_DIR)

        p_col, d_col = st.columns([4, 1])
        with p_col:
            active_preset = st.selectbox(t("sw_preset_name_label"), presets, key="lib_active_preset", label_visibility="collapsed")
        with d_col:
            st.markdown("<div style='padding-top:0.3rem'>", unsafe_allow_html=True)
            if active_preset != "Default":
                if st.button("🗑️", key="del_preset_btn", help=t("sw_delete_preset_help", name=active_preset)):
                    delete_preset(active_preset, config.SCRIPTS_DIR)
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with st.expander(t("sw_new_preset")):
            new_name = st.text_input(t("sw_preset_name_label"), placeholder=t("sw_preset_placeholder"), key="new_preset_name")
            if st.button(t("sw_create_btn"), key="create_preset_btn"):
                name = new_name.strip()
                if not name:
                    st.error(t("sw_enter_name"))
                elif name in presets:
                    st.error(t("sw_already_exists"))
                else:
                    create_preset(name, config.SCRIPTS_DIR)
                    st.success(t("sw_created_preset", name=name))
                    st.rerun()

        st.markdown("<div style='height: 4px'></div>", unsafe_allow_html=True)

        uploaded_files = st.file_uploader(
            "Upload .txt files",
            type=["txt"],
            accept_multiple_files=True,
            key=f"uploader_{active_preset}",
            label_visibility="collapsed",
        )
        if uploaded_files:
            for f in uploaded_files:
                save_script(f.name, f.read().decode("utf-8"), config.SCRIPTS_DIR, active_preset)
            st.success(t("sw_saved_scripts", n=len(uploaded_files), preset=active_preset))
            st.rerun()

        st.markdown("<div style='height: 4px'></div>", unsafe_allow_html=True)

        saved = list_scripts(config.SCRIPTS_DIR, active_preset)
        with st.expander(t("sw_scripts_label", n=len(saved))):
            if saved:
                for name in saved:
                    c1, c2 = st.columns([4, 1])
                    c1.caption(f"📄 {name}")
                    if c2.button("✕", key=f"del_{active_preset}_{name}", help=f"Delete {name}"):
                        delete_script(name, config.SCRIPTS_DIR, active_preset)
                        st.rerun()
            else:
                st.caption(t("sw_no_scripts"))

        with st.expander(t("sw_paste_manually")):
            manual_name = st.text_input(t("sw_name_label"), placeholder=t("sw_name_placeholder"), key=f"manual_name_{active_preset}")
            manual_text = st.text_area(t("sw_script_label"), height=140, key=f"manual_text_{active_preset}")
            if st.button(t("sw_save_btn"), key=f"save_manual_{active_preset}"):
                name = manual_name.strip()
                text = manual_text.strip()
                if not name:
                    st.error(t("sw_enter_name"))
                elif not name.endswith(".txt"):
                    st.error(t("sw_name_must_end_txt"))
                elif not text:
                    st.error(t("sw_paste_first"))
                else:
                    save_script(name, text, config.SCRIPTS_DIR, active_preset)
                    st.success(t("sw_saved_to_preset", name=name, preset=active_preset))
                    st.rerun()
