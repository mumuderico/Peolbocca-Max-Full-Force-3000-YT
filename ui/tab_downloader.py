import os
import streamlit as st
import config
from modules.downloader import download_media


def render_downloader():
    st.header("Social Media Downloader")
    st.caption("Supports YouTube, TikTok, Instagram, Twitter/X, Facebook, and 1000+ other sites.")

    url = st.text_input("Paste a video URL", placeholder="https://www.youtube.com/watch?v=...")
    col1, col2 = st.columns(2)
    media_type = col1.radio("Download type", ["Video", "Audio only"], horizontal=True)
    quality = col2.select_slider("Quality", options=["low", "medium", "best"], value="best")

    if st.button("Download", type="primary"):
        if not url.strip():
            st.error("Please enter a URL.")
            return

        with st.spinner("Downloading... this may take a moment."):
            try:
                filepath = download_media(
                    url=url.strip(),
                    output_dir=config.DOWNLOADS_DIR,
                    media_type="audio" if media_type == "Audio only" else "video",
                    quality=quality,
                )
                st.success(f"Downloaded: `{os.path.basename(filepath)}`")

                with open(filepath, "rb") as f:
                    st.download_button(
                        label="Save file",
                        data=f,
                        file_name=os.path.basename(filepath),
                    )
            except Exception as e:
                error_msg = str(e)
                if "login" in error_msg.lower() or "private" in error_msg.lower():
                    st.error("This video requires a login or is private. Public videos only.")
                elif "unsupported" in error_msg.lower():
                    st.error("This URL is not supported. Try a different platform or URL.")
                else:
                    st.error(f"Download failed: {error_msg}")
