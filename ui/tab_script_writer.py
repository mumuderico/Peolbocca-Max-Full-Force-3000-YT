import os
import streamlit as st
import config
from modules.script_generator import (
    delete_script,
    generate_script,
    generate_voiceover,
    list_scripts,
    load_user_scripts,
    save_script,
)

LANGUAGES = ["English", "Portuguese", "Spanish", "French", "German", "Italian", "Japanese", "Korean"]
PLATFORMS = ["TikTok", "Instagram Reels", "YouTube Shorts"]


def render_script_writer():
    st.header("Script Writer")

    # --- Style Library ---
    st.subheader("Your Style Library")
    uploaded_files = st.file_uploader(
        "Upload your sample scripts (.txt) — the AI will match your style",
        type=["txt"],
        accept_multiple_files=True,
        key="script_uploader",
    )
    if uploaded_files:
        for f in uploaded_files:
            save_script(f.name, f.read().decode("utf-8"), config.SCRIPTS_DIR)
        st.success(f"Saved {len(uploaded_files)} script(s) to your library.")
        st.rerun()

    saved = list_scripts(config.SCRIPTS_DIR)
    if saved:
        st.write(f"**Saved scripts ({len(saved)}):**")
        for name in saved:
            col1, col2 = st.columns([5, 1])
            col1.write(f"📄 {name}")
            if col2.button("Delete", key=f"del_{name}"):
                delete_script(name, config.SCRIPTS_DIR)
                st.rerun()
    else:
        st.info("No sample scripts yet. Upload some above to improve generation quality.")

    st.divider()

    # --- Script Generation ---
    st.subheader("Generate a New Script")
    topic = st.text_input("Topic", placeholder="e.g. 5 ways to save money")
    platform = st.selectbox("Platform", PLATFORMS)
    language = st.selectbox("Language", LANGUAGES)

    if st.button("Generate Script", type="primary"):
        if not topic.strip():
            st.error("Please enter a topic.")
            return

        api_key = (
            config.ANTHROPIC_API_KEY
            if config.LLM_PROVIDER == "anthropic"
            else config.OPENAI_API_KEY
        )
        if not api_key:
            st.error(
                f"No API key found. Open config.py and fill in {config.LLM_PROVIDER.upper()}_API_KEY."
            )
            return

        with st.spinner("Generating script..."):
            user_scripts = load_user_scripts(config.SCRIPTS_DIR)
            script = generate_script(topic, platform, language, user_scripts, api_key, config.LLM_PROVIDER)
            st.session_state["generated_script"] = script

    if "generated_script" in st.session_state:
        st.text_area("Generated Script", value=st.session_state["generated_script"], height=300, key="script_output")
        st.download_button(
            "Download as .txt",
            data=st.session_state["generated_script"],
            file_name="script.txt",
            mime="text/plain",
        )

        st.divider()
        st.subheader("Voiceover (optional)")
        if st.button("Generate Voiceover"):
            if config.TTS_PROVIDER == "elevenlabs" and not config.ELEVENLABS_API_KEY:
                st.error("Open config.py and fill in ELEVENLABS_API_KEY.")
                return
            audio_path = os.path.join(config.DOWNLOADS_DIR, "voiceover.mp3")
            with st.spinner("Generating voiceover..."):
                generate_voiceover(
                    st.session_state["generated_script"],
                    audio_path,
                    config.TTS_PROVIDER,
                    config.ELEVENLABS_API_KEY,
                )
            st.audio(audio_path, format="audio/mp3")
            with open(audio_path, "rb") as f:
                st.download_button("Download Voiceover", data=f, file_name="voiceover.mp3", mime="audio/mpeg")
