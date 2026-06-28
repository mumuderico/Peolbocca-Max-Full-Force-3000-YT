import streamlit as st
import config
from modules.video_searcher import search_videos
from modules.downloader import download_media


def _fmt_views(n) -> str:
    if not n:
        return "—"
    n = int(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def _fmt_duration(secs) -> str:
    if not secs:
        return "—"
    m, s = divmod(int(secs), 60)
    return f"{m}:{s:02d}"


def render_video_search():
    st.header("Video Search")
    st.caption("Search 9:16 vertical videos from YouTube Shorts by keyword.")

    keyword = st.text_input("Keyword / theme", placeholder="e.g. morning routine, gym motivation...")
    max_results = st.slider("Number of results", min_value=5, max_value=20, value=10, step=1)

    if st.button("🔍 Search", type="primary"):
        if not keyword.strip():
            st.error("Please enter a keyword.")
            return
        with st.spinner("Searching YouTube Shorts..."):
            results, errors = search_videos(keyword.strip(), max_results)
            for k in [k for k in st.session_state if k.startswith("sel_")]:
                del st.session_state[k]
            st.session_state["search_results"] = results
            st.session_state["search_selections"] = {}
            for err in errors:
                st.warning(err)
            if not results:
                st.error("No results found. Try a different keyword or check your connection.")
                return

    results = st.session_state.get("search_results")
    if not results:
        return

    st.markdown(f"**{len(results)} results found**")
    st.divider()

    COLS = 4
    selections = st.session_state.get("search_selections", {})

    for row_start in range(0, len(results), COLS):
        row_items = results[row_start: row_start + COLS]
        cols = st.columns(COLS)
        for col, (idx, video) in zip(cols, enumerate(row_items, start=row_start)):
            with col:
                if video["thumbnail"]:
                    st.markdown(
                        f'<a href="{video["url"]}" target="_blank">'
                        f'<img src="{video["thumbnail"]}" style="width:100%;border-radius:8px;"/>'
                        f'</a>',
                        unsafe_allow_html=True,
                    )
                badge = "▶️ YouTube Shorts"
                title = video["title"][:55] + "…" if len(video["title"]) > 55 else video["title"]
                st.markdown(
                    f'<a href="{video["url"]}" target="_blank" style="color:#e2e8f0;text-decoration:none;font-weight:600;">{title}</a>  \n'
                    f"👁 {_fmt_views(video['view_count'])}  ·  "
                    f"⏱ {_fmt_duration(video['duration'])}  ·  {badge}",
                    unsafe_allow_html=True,
                )
                checked = st.checkbox("Select", key=f"sel_{idx}", value=selections.get(idx, False))
                selections[idx] = checked

    st.session_state["search_selections"] = selections
    selected = [results[i] for i, v in selections.items() if v]

    if selected:
        st.divider()
        st.markdown(f"**{len(selected)} video(s) selected**")
        if st.button(f"⬇️ Download Selected ({len(selected)})", type="primary"):
            progress = st.progress(0)
            for i, video in enumerate(selected):
                label = video["title"][:45]
                with st.spinner(f"Downloading: {label}..."):
                    try:
                        download_media(
                            url=video["url"],
                            output_dir=config.DOWNLOADS_DIR,
                            media_type="video",
                            quality="best",
                        )
                        st.success(f"✓ {label}")
                    except Exception as e:
                        st.error(f"✗ {label}: {e}")
                progress.progress((i + 1) / len(selected))
