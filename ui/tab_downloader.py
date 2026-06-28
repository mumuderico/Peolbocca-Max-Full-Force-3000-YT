import os
import streamlit as st
import config
from modules.downloader import download_media
from ui.i18n import t


def render_downloader():
    st.header(t("dl_header"))
    st.caption(t("dl_caption"))

    url = st.text_input(t("dl_url_label"), placeholder=t("dl_url_placeholder"))
    col1, col2 = st.columns(2)
    media_type = col1.radio(t("dl_type_label"), [t("dl_video"), t("dl_audio")], horizontal=True)
    quality = col2.select_slider(t("dl_quality_label"), options=["low", "medium", "best"], value="best")

    if st.button(t("dl_download_btn"), type="primary"):
        if not url.strip():
            st.error(t("dl_enter_url"))
            return

        with st.spinner(t("dl_downloading")):
            try:
                filepath = download_media(
                    url=url.strip(),
                    output_dir=config.DOWNLOADS_DIR,
                    media_type="audio" if media_type == t("dl_audio") else "video",
                    quality=quality,
                )
                st.success(t("dl_downloaded", filename=os.path.basename(filepath)))

                with open(filepath, "rb") as f:
                    st.download_button(
                        label=t("dl_save_file"),
                        data=f,
                        file_name=os.path.basename(filepath),
                    )
            except Exception as e:
                error_msg = str(e)
                if "login" in error_msg.lower() or "private" in error_msg.lower():
                    st.error(t("dl_private_error"))
                elif "unsupported" in error_msg.lower():
                    st.error(t("dl_unsupported_error"))
                else:
                    st.error(t("dl_failed", error=error_msg))
