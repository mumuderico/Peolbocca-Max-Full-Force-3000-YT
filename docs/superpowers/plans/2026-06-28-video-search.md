# Video Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "🔎 Video Search" tab that searches YouTube Shorts and TikTok simultaneously by keyword, displays results in a 4-column thumbnail grid, and lets the user select and download videos.

**Architecture:** A pure-logic module `modules/video_searcher.py` runs two yt-dlp keyword searches in parallel via `ThreadPoolExecutor` and returns merged, shuffled results. The UI tab `ui/tab_video_search.py` renders the grid and wires the Download Selected button to the existing `download_media()` function. `app.py` gets a 5th tab entry.

**Tech Stack:** Python stdlib (`concurrent.futures`, `random`), `yt-dlp` (already installed), `streamlit`, `pytest`, `pytest-mock`

## Global Constraints

- No new pip dependencies — use only packages already in `requirements.txt`
- Follow existing module pattern: pure logic in `modules/`, Streamlit only in `ui/`
- All tests must run offline (mock all `yt_dlp.YoutubeDL` calls)
- FFmpeg path hardcoded as `r"C:\Program Files\FFmpeg\bin"` (matches existing `downloader.py`)
- Downloads go to `config.DOWNLOADS_DIR` (matches existing tabs)

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `modules/video_searcher.py` | Search logic — parallel yt-dlp calls, result normalisation |
| Create | `ui/tab_video_search.py` | Streamlit grid UI, selection state, download loop |
| Create | `tests/test_video_searcher.py` | Unit tests for search module |
| Modify | `app.py` lines 289–306 | Add 5th tab, import `render_video_search` |

---

## Task 1: Search module (`modules/video_searcher.py`)

**Files:**
- Create: `modules/video_searcher.py`
- Test: `tests/test_video_searcher.py`

**Interfaces:**
- Produces: `search_videos(keyword: str, max_results: int = 10) -> tuple[list[dict], list[str]]`
  - First element: list of result dicts with keys `title`, `url`, `thumbnail`, `view_count` (int), `duration` (int, seconds), `platform` (`"youtube_shorts"` or `"tiktok"`)
  - Second element: list of human-readable error strings (one per failed platform, empty if both succeed)
- Internal helper (also patchable in tests): `_search_platform(keyword: str, n: int, platform: str) -> list[dict]`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_video_searcher.py`:

```python
import pytest
from unittest.mock import MagicMock
from modules.video_searcher import search_videos, _search_platform


def _make_mock_ydl(entries):
    mock_ydl = MagicMock()
    mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
    mock_ydl.__exit__ = MagicMock(return_value=False)
    mock_ydl.extract_info.return_value = {"entries": entries}
    return mock_ydl


FAKE_ENTRY = {
    "id": "abc123",
    "title": "Morning Routine Video",
    "url": "https://example.com/video/abc123",
    "thumbnail": "https://example.com/thumb.jpg",
    "view_count": 1_200_000,
    "duration": 47,
}


def test_search_returns_expected_keys(mocker):
    mock_ydl = _make_mock_ydl([FAKE_ENTRY])
    mocker.patch("yt_dlp.YoutubeDL", return_value=mock_ydl)

    results, errors = search_videos("morning routine", max_results=2)

    assert isinstance(results, list)
    assert len(errors) == 0
    for result in results:
        for key in ("title", "url", "thumbnail", "view_count", "duration", "platform"):
            assert key in result, f"Missing key: {key}"


def test_partial_failure_returns_remaining_results(mocker):
    good_result = {
        "title": "Good Video",
        "url": "https://www.youtube.com/shorts/abc123",
        "thumbnail": "https://i.ytimg.com/vi/abc123/hqdefault.jpg",
        "view_count": 1000,
        "duration": 30,
        "platform": "youtube_shorts",
    }

    def fake_search(keyword, n, platform):
        if platform == "tiktok":
            raise Exception("TikTok rate limited")
        return [good_result]

    mocker.patch("modules.video_searcher._search_platform", side_effect=fake_search)

    results, errors = search_videos("morning routine", max_results=2)

    assert len(results) == 1
    assert results[0]["platform"] == "youtube_shorts"
    assert len(errors) == 1
    assert "TikTok" in errors[0]
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_video_searcher.py -v
```

Expected: `ModuleNotFoundError` or `ImportError` — `modules/video_searcher.py` does not exist yet.

- [ ] **Step 3: Implement `modules/video_searcher.py`**

```python
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import yt_dlp


def _search_platform(keyword: str, n: int, platform: str) -> list[dict]:
    prefix = "ytsearch" if platform == "youtube_shorts" else "ttsearch"
    query = f"{prefix}{n}:{keyword}"
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
    }
    results = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        for entry in (info.get("entries") or []):
            if not entry:
                continue
            video_id = entry.get("id", "")
            if platform == "youtube_shorts":
                url = f"https://www.youtube.com/shorts/{video_id}"
                thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
            else:
                url = entry.get("url") or entry.get("webpage_url", "")
                thumbnail = entry.get("thumbnail", "")
            results.append({
                "title": entry.get("title", "Unknown"),
                "url": url,
                "thumbnail": thumbnail,
                "view_count": entry.get("view_count") or 0,
                "duration": entry.get("duration") or 0,
                "platform": platform,
            })
    return results


def search_videos(keyword: str, max_results: int = 10) -> tuple[list[dict], list[str]]:
    per_platform = max(1, max_results // 2)
    platforms = ["youtube_shorts", "tiktok"]
    all_results: list[dict] = []
    errors: list[str] = []

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(_search_platform, keyword, per_platform, p): p
            for p in platforms
        }
        for future in as_completed(futures):
            platform = futures[future]
            try:
                all_results.extend(future.result())
            except Exception as exc:
                label = "YouTube Shorts" if platform == "youtube_shorts" else "TikTok"
                errors.append(f"{label} search unavailable: {exc}")

    random.shuffle(all_results)
    return all_results, errors
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_video_searcher.py -v
```

Expected output:
```
tests/test_video_searcher.py::test_search_returns_expected_keys PASSED
tests/test_video_searcher.py::test_partial_failure_returns_remaining_results PASSED
2 passed in ...s
```

- [ ] **Step 5: Commit**

```bash
git add modules/video_searcher.py tests/test_video_searcher.py
git commit -m "feat: add video_searcher module with parallel yt-dlp search"
```

---

## Task 2: UI tab (`ui/tab_video_search.py`)

**Files:**
- Create: `ui/tab_video_search.py`

**Interfaces:**
- Consumes: `search_videos(keyword: str, max_results: int) -> tuple[list[dict], list[str]]` from `modules.video_searcher`
- Consumes: `download_media(url: str, output_dir: str, media_type: str, quality: str) -> str` from `modules.downloader`
- Consumes: `config.DOWNLOADS_DIR` (str)
- Produces: `render_video_search()` — called by `app.py`

- [ ] **Step 1: Create `ui/tab_video_search.py`**

```python
import streamlit as st
import config
from modules.video_searcher import search_videos
from modules.downloader import download_media


def _fmt_views(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n) if n else "—"


def _fmt_duration(secs: int) -> str:
    if not secs:
        return "—"
    m, s = divmod(secs, 60)
    return f"{m}:{s:02d}"


def render_video_search():
    st.header("Video Search")
    st.caption("Search 9:16 vertical videos from YouTube Shorts and TikTok simultaneously.")

    keyword = st.text_input("Keyword / theme", placeholder="e.g. morning routine, gym motivation...")
    max_results = st.slider("Number of results", min_value=5, max_value=20, value=10, step=1)

    if st.button("🔍 Search", type="primary"):
        if not keyword.strip():
            st.error("Please enter a keyword.")
            return
        with st.spinner("Searching YouTube Shorts and TikTok..."):
            results, errors = search_videos(keyword.strip(), max_results)
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
                    st.image(video["thumbnail"], use_container_width=True)
                badge = "▶️ Shorts" if video["platform"] == "youtube_shorts" else "🎵 TikTok"
                title = video["title"][:55] + "…" if len(video["title"]) > 55 else video["title"]
                st.markdown(
                    f"**{title}**  \n"
                    f"👁 {_fmt_views(video['view_count'])}  ·  "
                    f"⏱ {_fmt_duration(video['duration'])}  ·  {badge}"
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
```

- [ ] **Step 2: Manually verify the file looks right**

Open `ui/tab_video_search.py` and check:
- `_fmt_views(1_200_000)` would return `"1.2M"` ✓
- `_fmt_duration(47)` would return `"0:47"` ✓
- `_fmt_duration(125)` would return `"2:05"` ✓

No automated test needed for this step — the logic is wired up in Task 3 and verified end-to-end there.

- [ ] **Step 3: Commit**

```bash
git add ui/tab_video_search.py
git commit -m "feat: add video search UI tab"
```

---

## Task 3: Wire into `app.py`

**Files:**
- Modify: `app.py` (lines 289–306)

**Interfaces:**
- Consumes: `render_video_search()` from `ui.tab_video_search`

- [ ] **Step 1: Add the import at the top of `app.py`**

Find the existing imports block (lines 1–5):
```python
import streamlit as st
from ui.tab_script_writer import render_script_writer
from ui.tab_downloader import render_downloader
from ui.tab_transcript import render_transcript
from ui.tab_caption_remover import render_caption_remover
```

Replace with:
```python
import streamlit as st
from ui.tab_script_writer import render_script_writer
from ui.tab_downloader import render_downloader
from ui.tab_transcript import render_transcript
from ui.tab_caption_remover import render_caption_remover
from ui.tab_video_search import render_video_search
```

- [ ] **Step 2: Add the 5th tab**

Find (line 289):
```python
tab1, tab2, tab3, tab4 = st.tabs([
    "✍️  Script Writer",
    "⬇️  Downloader",
    "📝  Transcript",
    "🎞️  Caption Remover",
])
```

Replace with:
```python
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "✍️  Script Writer",
    "⬇️  Downloader",
    "📝  Transcript",
    "🎞️  Caption Remover",
    "🔎  Video Search",
])
```

- [ ] **Step 3: Add the tab body**

Find (lines 296–306):
```python
with tab1:
    render_script_writer()

with tab2:
    render_downloader()

with tab3:
    render_transcript()

with tab4:
    render_caption_remover()
```

Replace with:
```python
with tab1:
    render_script_writer()

with tab2:
    render_downloader()

with tab3:
    render_transcript()

with tab4:
    render_caption_remover()

with tab5:
    render_video_search()
```

- [ ] **Step 4: Run the full test suite to confirm nothing broke**

```
pytest tests/ -v
```

Expected: all existing tests still pass, plus the 2 new video searcher tests.

- [ ] **Step 5: Start the app and manually test the new tab**

```
streamlit run app.py
```

Manual checks:
1. "🔎 Video Search" tab appears in the tab bar
2. Typing a keyword and clicking Search shows a spinner
3. Results appear as a 4-column thumbnail grid
4. Each card shows title, view count, duration, platform badge
5. Checking a card shows "N selected" and the Download button
6. Download button triggers downloads and shows per-video success/error

- [ ] **Step 6: Commit**

```bash
git add app.py
git commit -m "feat: wire Video Search tab into app"
```
