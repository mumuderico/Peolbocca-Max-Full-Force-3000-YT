import os
import tempfile
import streamlit as st
import config
from modules.caption_remover import remove_captions


def render_caption_remover():
    st.header("Caption Remover")
    st.caption(
        "Upload a video with burned-in captions. The AI detects and removes the text, "
        "then rebuilds the background. Works best on captions over simple backgrounds."
    )

    uploaded = st.file_uploader(
        "Upload video", type=["mp4", "mov", "avi", "mkv", "webm"]
    )

    if uploaded and st.button("Remove Captions", type="primary"):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = os.path.join(tmp_dir, uploaded.name)
            output_path = os.path.join(config.DOWNLOADS_DIR, f"clean_{uploaded.name}")

            with open(input_path, "wb") as f:
                f.write(uploaded.read())

            os.makedirs(config.DOWNLOADS_DIR, exist_ok=True)

            progress = st.progress(0, text="Initializing OCR model (first run downloads ~200MB)...")

            try:
                with st.spinner("Processing video — this may take a few minutes..."):
                    progress.progress(10, text="Detecting captions frame by frame...")
                    result_path = remove_captions(
                        input_path,
                        output_path,
                        provider=config.CAPTION_REMOVER_PROVIDER,
                        replicate_api_key=config.REPLICATE_API_KEY,
                    )
                progress.progress(100, text="Done!")
                st.success("Captions removed successfully.")

                with open(result_path, "rb") as f:
                    st.download_button(
                        "Download Clean Video",
                        data=f,
                        file_name=os.path.basename(result_path),
                    )
            except FileNotFoundError as e:
                if "ffmpeg" in str(e).lower():
                    st.error(
                        "ffmpeg not found. Install it from https://ffmpeg.org/download.html "
                        "and make sure it's added to your PATH."
                    )
                else:
                    st.error(f"File error: {e}")
            except Exception as e:
                st.error(f"Processing failed: {e}")
