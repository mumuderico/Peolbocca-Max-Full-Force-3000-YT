import os
import tempfile
import streamlit as st
import config
from ui.user_cfg import get_key
from modules.caption_remover import remove_captions
from ui.i18n import t


def render_caption_remover():
    st.header(t("cr_header"))
    st.caption(t("cr_caption"))

    uploaded = st.file_uploader(t("cr_upload_label"), type=["mp4", "mov", "avi", "mkv", "webm"])

    with st.expander(t("cr_speed_settings")):
        ocr_interval = st.slider(
            t("cr_ocr_label"),
            min_value=1, max_value=30, value=8,
            help=t("cr_ocr_help"),
        )
        caption_zone = st.slider(
            t("cr_zone_label"),
            min_value=10, max_value=60, value=35,
            help=t("cr_zone_help"),
        )

    if uploaded and st.button(t("cr_remove_btn"), type="primary"):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = os.path.join(tmp_dir, uploaded.name)
            output_path = os.path.join(config.DOWNLOADS_DIR, f"clean_{uploaded.name}")

            with open(input_path, "wb") as f:
                f.write(uploaded.read())

            os.makedirs(config.DOWNLOADS_DIR, exist_ok=True)

            progress_bar = st.progress(0, text=t("cr_initializing"))
            status = st.empty()

            def on_progress(fraction: float):
                pct = int(fraction * 100)
                progress_bar.progress(pct, text=t("cr_processing", pct=pct))
                status.caption(t("cr_pct_complete", pct=pct))

            try:
                result_path = remove_captions(
                    input_path,
                    output_path,
                    provider=get_key("CAPTION_REMOVER_PROVIDER"),
                    replicate_api_key=get_key("REPLICATE_API_KEY"),
                    ocr_every_n_frames=ocr_interval,
                    caption_zone=caption_zone / 100,
                    progress_callback=on_progress,
                )
                progress_bar.progress(100, text=t("cr_done"))
                status.empty()
                st.success(t("cr_success"))

                with open(result_path, "rb") as f:
                    st.download_button(
                        t("cr_download_btn"),
                        data=f,
                        file_name=os.path.basename(result_path),
                        use_container_width=True,
                    )
            except FileNotFoundError as e:
                if "ffmpeg" in str(e).lower():
                    st.error(t("cr_ffmpeg_error"))
                else:
                    st.error(t("cr_file_error", error=e))
            except Exception as e:
                st.error(t("cr_process_error", error=e))
