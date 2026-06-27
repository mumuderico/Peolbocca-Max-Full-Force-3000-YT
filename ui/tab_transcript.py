import streamlit as st
from youtube_transcript_api import TranscriptsDisabled, NoTranscriptFound
from modules.transcriber import (
    get_transcript,
    translate_text,
    SUPPORTED_LANGUAGES,
    extract_video_id,
)


def render_transcript():
    st.header("YouTube Transcript + Translation")

    url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
    include_timestamps = st.checkbox("Include timestamps")

    if st.button("Get Transcript", type="primary"):
        if not url.strip():
            st.error("Please enter a YouTube URL.")
            return

        try:
            extract_video_id(url.strip())
        except ValueError:
            st.error("That doesn't look like a valid YouTube URL.")
            return

        with st.spinner("Fetching transcript..."):
            try:
                transcript = get_transcript(url.strip(), include_timestamps=include_timestamps)
                st.session_state["transcript"] = transcript
                st.session_state["transcript_url"] = url.strip()
            except TranscriptsDisabled:
                st.error("This video has captions disabled. Try a different video.")
                return
            except NoTranscriptFound:
                st.error("No transcript found for this video.")
                return
            except Exception as e:
                st.error(f"Could not fetch transcript: {e}")
                return

    if "transcript" in st.session_state:
        st.text_area("Transcript", value=st.session_state["transcript"], height=350, key="transcript_display")
        st.download_button(
            "Download Transcript (.txt)",
            data=st.session_state["transcript"],
            file_name="transcript.txt",
            mime="text/plain",
        )

        st.divider()
        st.subheader("Translate")
        target_lang_name = st.selectbox(
            "Translate to",
            options=[name for name in SUPPORTED_LANGUAGES if name != "English"],
        )
        if st.button("Translate"):
            lang_code = SUPPORTED_LANGUAGES[target_lang_name]
            with st.spinner(f"Translating to {target_lang_name}..."):
                translated = translate_text(st.session_state["transcript"], lang_code)
                st.session_state["translated"] = translated

        if "translated" in st.session_state:
            st.text_area(
                "Translated Transcript",
                value=st.session_state["translated"],
                height=350,
                key="translated_display",
            )
            st.download_button(
                "Download Translation (.txt)",
                data=st.session_state["translated"],
                file_name="translated_transcript.txt",
                mime="text/plain",
            )
