# Video Search Feature — Design Spec
**Date:** 2026-06-28  
**Status:** Approved

## Overview

Add a "🔎 Video Search" tab to the Content Creator Tool that lets users search for 9:16 vertical videos on YouTube Shorts and TikTok simultaneously by keyword, browse results in a thumbnail grid, select videos, and download them.

## Architecture

### New files
- `modules/video_searcher.py` — pure search logic, no Streamlit imports
- `ui/tab_video_search.py` — Streamlit UI for the tab
- `tests/test_video_searcher.py` — unit tests for the search module

### Modified files
- `app.py` — adds 5th tab and imports `render_video_search`

### Search mechanism
Uses yt-dlp's built-in keyword search (already a project dependency, no new API keys required):
- YouTube Shorts: `ytsearch{n}:keyword`
- TikTok: `ttsearch{n}:keyword`

Both searches run in parallel via `ThreadPoolExecutor`. Each platform fetches up to `n/2` results so the combined total matches the user's chosen limit.

## Data Flow

1. User enters a keyword and selects result count (5–20, default 10)
2. Search button triggers `search_videos(keyword, max_results)` in `modules/video_searcher.py`
3. Function fires both yt-dlp searches in parallel, merges and shuffles results
4. Returns a list of dicts, each with: `title`, `url`, `thumbnail`, `view_count`, `duration`, `platform`
5. UI renders a 4-column grid of video cards
6. Each card shows: thumbnail image, title (2-line truncation), view count, duration, platform badge (🎵 TikTok / ▶️ Shorts), checkbox
7. "Download Selected" button iterates checked videos, calls `download_media()` from the existing `modules/downloader.py`, shows a progress bar with per-video success/error feedback

## Error Handling

- If one platform search fails (e.g. TikTok rate limit or yt-dlp issue), the other platform's results are still displayed
- A non-blocking warning is shown: "TikTok search unavailable, showing YouTube Shorts only" (or vice versa)
- If both platforms fail, an error message is shown with the failure reason
- Individual download failures show per-video error messages without stopping the rest of the queue

## UI Layout

```
Keyword  [________________________]
Results  [10 ▼]    [ 🔍 Search ]

12 results found

┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ thumbnail│  │ thumbnail│  │ thumbnail│  │ thumbnail│
├──────────┤  ├──────────┤  ├──────────┤  ├──────────┤
│ Title... │  │ Title... │  │ Title... │  │ Title... │
│ 👁 2.1M  │  │ 👁 890K  │  │ 👁 450K  │  │ 👁 120K  │
│ ⏱ 0:47  │  │ ⏱ 1:02  │  │ ⏱ 0:58  │  │ ⏱ 1:15  │
│ ▶️ Shorts│  │ 🎵 TikTok│  │ ▶️ Shorts│  │ 🎵 TikTok│
│ ☑ Select │  │ ☑ Select │  │ ☑ Select │  │ ☑ Select │
└──────────┘  └──────────┘  └──────────┘  └──────────┘

2 selected     [ ⬇️ Download Selected ]
```

## Testing

File: `tests/test_video_searcher.py`

- **test_search_returns_expected_keys** — mock yt-dlp, assert each result dict contains `title`, `url`, `thumbnail`, `view_count`, `duration`, `platform`
- **test_partial_failure_returns_remaining_results** — mock one platform to raise an exception, assert the other platform's results are still returned and the error is surfaced
- All tests run offline (yt-dlp calls mocked)

## Out of Scope

- Filtering/sorting results (by views, recency, etc.) — can be added later
- TikTok authentication — public search only
- Preview playback in-app — links open externally
