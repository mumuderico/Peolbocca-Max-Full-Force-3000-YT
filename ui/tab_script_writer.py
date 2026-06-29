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
    list_shared_presets,
    list_shared_scripts,
    load_shared_scripts,
    load_user_scripts,
    save_script,
)
from modules.longform_generator import (
    build_system_prompt,
    extract_option,
    gerar_angulos,
    gerar_hook,
    gerar_payoffs,
    gerar_roteiro_completo,
    gerar_setups,
)
from ui.i18n import t
from ui.user_cfg import get_key, get_scripts_dir

LANGUAGES = ["English", "Portuguese", "Spanish", "French", "German", "Italian", "Japanese", "Korean"]
PLATFORMS = ["YouTube Shorts", "Long Form"]

_PACE_OPTIONS = ["Very Slow", "Slow", "Normal", "Fast", "Very Fast"]
_PACE_TO_RATE  = {"Very Slow": "-50%", "Slow": "-25%", "Normal": "+0%", "Fast": "+25%", "Very Fast": "+50%"}
_PITCH_OPTIONS = ["Lower", "Normal", "Higher"]
_PITCH_TO_HZ   = {"Lower": "-5Hz", "Normal": "+0Hz", "Higher": "+5Hz"}


_SHARED_PREFIX = "🌐 "


def _get_api_key_and_provider():
    provider = get_key("LLM_PROVIDER") or config.LLM_PROVIDER
    key_map = {
        "groq": get_key("GROQ_API_KEY"),
        "gemini": get_key("GEMINI_API_KEY"),
        "anthropic": get_key("ANTHROPIC_API_KEY"),
        "openai": get_key("OPENAI_API_KEY"),
    }
    return key_map.get(provider, ""), provider


def _lf_reset():
    for key in ["lf_step", "lf_tema", "lf_language", "lf_system_prompt", "lf_angulos_raw",
                "lf_angulo_escolhido", "lf_payoffs", "lf_estrutura",
                "lf_hooks_raw", "lf_hook_escolhido", "lf_roteiro"]:
        st.session_state.pop(key, None)


def _render_longform(topic: str, language: str = "Portuguese"):
    step = st.session_state.get("lf_step", 0)
    api_key, provider = _get_api_key_and_provider()

    if not api_key:
        st.error(t("sw_no_api_key", provider=provider.upper()))
        return

    # ── Step 0: start ──────────────────────────────────────────────────
    if step == 0:
        if st.button("Gerar Ângulos", type="primary", use_container_width=True):
            if not topic.strip():
                st.error(t("sw_enter_name"))
                return
            with st.spinner("Gerando ângulos..."):
                try:
                    sys_prompt = build_system_prompt()
                    angulos = gerar_angulos(topic, sys_prompt, api_key, provider)
                    st.session_state["lf_step"] = 1
                    st.session_state["lf_tema"] = topic
                    st.session_state["lf_language"] = language
                    st.session_state["lf_system_prompt"] = sys_prompt
                    st.session_state["lf_angulos_raw"] = angulos
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao gerar ângulos: {e}")
        return

    tema = st.session_state["lf_tema"]
    sys_prompt = st.session_state["lf_system_prompt"]

    # ── Step 1: choose angle ────────────────────────────────────────────
    if step >= 1:
        with st.expander("📐 Ângulos sugeridos", expanded=(step == 1)):
            st.text_area("", value=st.session_state["lf_angulos_raw"], height=300,
                         disabled=True, key="lf_angulos_display", label_visibility="collapsed")
            if step == 1:
                escolha = st.radio("Qual ângulo você escolhe?", ["Ângulo A", "Ângulo B", "Ângulo C"],
                                   horizontal=True, key="lf_radio_angulo")
                if st.button("Continuar com este ângulo", type="primary"):
                    angulo_texto = extract_option(st.session_state["lf_angulos_raw"], escolha)
                    with st.spinner("Gerando payoffs..."):
                        try:
                            payoffs = gerar_payoffs(tema, angulo_texto, sys_prompt, api_key, provider)
                            st.session_state["lf_angulo_escolhido"] = angulo_texto
                            st.session_state["lf_payoffs"] = payoffs
                            st.session_state["lf_step"] = 2
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao gerar payoffs: {e}")

    # ── Step 2: confirm payoffs ─────────────────────────────────────────
    if step >= 2:
        angulo = st.session_state["lf_angulo_escolhido"]
        with st.expander("🎯 Payoffs", expanded=(step == 2)):
            st.text_area("", value=st.session_state["lf_payoffs"], height=250,
                         disabled=True, key="lf_payoffs_display", label_visibility="collapsed")
            if step == 2:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Continuar", type="primary", use_container_width=True):
                        with st.spinner("Gerando estrutura..."):
                            try:
                                estrutura = gerar_setups(tema, angulo, st.session_state["lf_payoffs"],
                                                         sys_prompt, api_key, provider)
                                st.session_state["lf_estrutura"] = estrutura
                                st.session_state["lf_step"] = 3
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao gerar estrutura: {e}")
                with col2:
                    if st.button("Gerar novamente", use_container_width=True):
                        with st.spinner("Regerando payoffs..."):
                            try:
                                payoffs = gerar_payoffs(tema, angulo, sys_prompt, api_key, provider)
                                st.session_state["lf_payoffs"] = payoffs
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao regerar payoffs: {e}")

    # ── Step 3: structure (auto) ────────────────────────────────────────
    if step >= 3:
        with st.expander("🏗️ Estrutura (setups e tensões)", expanded=(step == 3)):
            st.text_area("", value=st.session_state["lf_estrutura"], height=300,
                         disabled=True, key="lf_estrutura_display", label_visibility="collapsed")
            if step == 3:
                if st.button("Gerar Hooks", type="primary"):
                    with st.spinner("Gerando hooks..."):
                        try:
                            hooks = gerar_hook(tema, st.session_state["lf_angulo_escolhido"],
                                               st.session_state["lf_estrutura"], sys_prompt, api_key, provider)
                            st.session_state["lf_hooks_raw"] = hooks
                            st.session_state["lf_step"] = 4
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao gerar hooks: {e}")

    # ── Step 4: choose hook ─────────────────────────────────────────────
    if step >= 4:
        with st.expander("🪝 Hooks sugeridos", expanded=(step == 4)):
            st.text_area("", value=st.session_state["lf_hooks_raw"], height=300,
                         disabled=True, key="lf_hooks_display", label_visibility="collapsed")
            if step == 4:
                escolha_hook = st.radio("Qual hook você escolhe?", ["Hook A", "Hook B", "Hook C"],
                                        horizontal=True, key="lf_radio_hook")
                if st.button("Gerar Roteiro Completo", type="primary"):
                    hook_texto = extract_option(st.session_state["lf_hooks_raw"], escolha_hook)
                    with st.spinner("Escrevendo o roteiro completo..."):
                        try:
                            roteiro = gerar_roteiro_completo(
                                tema,
                                st.session_state["lf_angulo_escolhido"],
                                hook_texto,
                                st.session_state["lf_estrutura"],
                                sys_prompt,
                                api_key,
                                provider,
                                language=st.session_state.get("lf_language", "Portuguese"),
                            )
                            st.session_state["lf_hook_escolhido"] = hook_texto
                            st.session_state["lf_roteiro"] = roteiro
                            st.session_state["lf_step"] = 5
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao gerar roteiro: {e}")

    # ── Step 5: complete script ─────────────────────────────────────────
    if step >= 5:
        st.markdown("### 📄 Roteiro Completo")
        st.text_area("", value=st.session_state["lf_roteiro"], height=500,
                     key="lf_roteiro_display", label_visibility="collapsed")
        st.download_button(
            "⬇️ Baixar roteiro (.txt)",
            data=st.session_state["lf_roteiro"],
            file_name=f"roteiro_{tema[:30].replace(' ', '_')}.txt",
            mime="text/plain",
        )
        if st.button("🔄 Começar de novo"):
            _lf_reset()
            st.rerun()


def render_script_writer():
    scripts_dir = get_scripts_dir()
    shared_dir = config.SHARED_SCRIPTS_DIR
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

        user_presets = [p for p in list_presets(scripts_dir) if p != "Default"]
        shared_labels = [_SHARED_PREFIX + p for p in list_shared_presets(shared_dir)]
        all_presets = shared_labels + user_presets  # shared first so juanminiboi is the default
        saved_preset = get_key("SCRIPT_PRESET") or ""
        preset_idx = all_presets.index(saved_preset) if saved_preset in all_presets else 0
        if platform != "Long Form":
            style_preset = st.selectbox(
                t("sw_style_preset"),
                all_presets,
                index=preset_idx,
                key="gen_style_preset",
                help=t("sw_preset_help"),
            )
        else:
            style_preset = ""

        st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)

        if platform == "Long Form":
            _render_longform(topic, language)
        else:
            if st.button(t("sw_generate_btn"), type="primary", use_container_width=True):
                if not topic.strip():
                    st.error(t("sw_enter_name"))
                else:
                    llm_provider = get_key("LLM_PROVIDER") or config.LLM_PROVIDER
                    key_map = {
                        "groq": get_key("GROQ_API_KEY"),
                        "gemini": get_key("GEMINI_API_KEY"),
                        "anthropic": get_key("ANTHROPIC_API_KEY"),
                        "openai": get_key("OPENAI_API_KEY"),
                    }
                    api_key = key_map.get(llm_provider, "")
                    if not api_key:
                        st.error(t("sw_no_api_key", provider=llm_provider.upper()))
                    else:
                        with st.spinner(t("sw_crafting")):
                            try:
                                if style_preset.startswith(_SHARED_PREFIX):
                                    user_scripts = load_shared_scripts(shared_dir, style_preset[len(_SHARED_PREFIX):])
                                else:
                                    user_scripts = load_user_scripts(scripts_dir, style_preset)
                                script = generate_script(topic, platform, language, user_scripts, api_key, llm_provider)
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
                        tts_provider = get_key("TTS_PROVIDER") or config.TTS_PROVIDER
                        elevenlabs_key = get_key("ELEVENLABS_API_KEY")
                        if tts_provider == "elevenlabs" and not elevenlabs_key:
                            st.error(t("sw_elevenlabs_missing"))
                        else:
                            audio_path = os.path.join(config.DOWNLOADS_DIR, "voiceover.mp3")
                            with st.spinner(t("sw_generating_voc")):
                                generate_voiceover(
                                    st.session_state["generated_script"],
                                    audio_path,
                                    tts_provider,
                                    elevenlabs_key,
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

        # personal named presets only — no "Default"
        presets = [p for p in list_presets(scripts_dir) if p != "Default"]

        if presets:
            p_col, d_col = st.columns([4, 1])
            with p_col:
                active_preset = st.selectbox(t("sw_preset_name_label"), presets, key="lib_active_preset", label_visibility="collapsed")
            with d_col:
                st.markdown("<div style='padding-top:0.3rem'>", unsafe_allow_html=True)
                if st.button("🗑️", key="del_preset_btn", help=t("sw_delete_preset_help", name=active_preset)):
                    delete_preset(active_preset, scripts_dir)
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

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
                    save_script(f.name, f.read().decode("utf-8"), scripts_dir, active_preset)
                st.success(t("sw_saved_scripts", n=len(uploaded_files), preset=active_preset))
                st.rerun()

            st.markdown("<div style='height: 4px'></div>", unsafe_allow_html=True)

            saved = list_scripts(scripts_dir, active_preset)
            with st.expander(t("sw_scripts_label", n=len(saved))):
                if saved:
                    for name in saved:
                        c1, c2 = st.columns([4, 1])
                        c1.caption(f"📄 {name}")
                        if c2.button("✕", key=f"del_{active_preset}_{name}", help=f"Delete {name}"):
                            delete_script(name, scripts_dir, active_preset)
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
                        save_script(name, text, scripts_dir, active_preset)
                        st.success(t("sw_saved_to_preset", name=name, preset=active_preset))
                        st.rerun()
        else:
            st.caption("No personal presets yet. Create one below to build your style library.")

        with st.expander(t("sw_new_preset")):
            new_name = st.text_input(t("sw_preset_name_label"), placeholder=t("sw_preset_placeholder"), key="new_preset_name")
            if st.button(t("sw_create_btn"), key="create_preset_btn"):
                name = new_name.strip()
                if not name:
                    st.error(t("sw_enter_name"))
                elif name in presets:
                    st.error(t("sw_already_exists"))
                else:
                    create_preset(name, scripts_dir)
                    st.success(t("sw_created_preset", name=name))
                    st.rerun()
