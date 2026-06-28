# ViewStats Analytics Feature — Design Spec
**Date:** 2026-06-28  
**Status:** Approved

## Overview

Add a "📊 ViewStats" tab to the Content Creator Tool that lets users paste any YouTube URL (channel or video) and see analytics similar to viewstats.com: real stats fetched from the YouTube Data API v3. No estimated revenue — real data only.

## Architecture

### New files
- `modules/viewstats.py` — pure YouTube Data API v3 logic, no Streamlit imports
- `ui/tab_viewstats.py` — Streamlit UI for the tab
- `tests/test_viewstats.py` — unit tests with mocked API calls

### Modified files
- `config.py` — add `YOUTUBE_API_KEY = ""`
- `app.py` — add 6th tab, import `render_viewstats`
- `requirements.txt` — add `google-api-python-client`

### Data source
YouTube Data API v3 via `google-api-python-client`. Free quota: 10,000 units/day. Requires a Google Cloud API key added to `config.py`.

## URL Auto-Detection

`fetch_stats()` parses the URL and routes to video or channel logic:

| URL pattern | Type |
|---|---|
| `youtube.com/watch?v=ID` | video |
| `youtu.be/ID` | video |
| `youtube.com/shorts/ID` | video |
| `youtube.com/@handle` | channel |
| `youtube.com/channel/ID` | channel |
| `youtube.com/c/NAME` | channel |

## Data Flow

### Video URL
1. Extract video ID from URL
2. Call `videos.list(part="snippet,statistics,contentDetails", id=VIDEO_ID)`
3. Return dict with: `type`, `title`, `channel`, `views`, `likes`, `comments`, `duration`, `upload_date`, `thumbnail`

### Channel URL
1. Extract handle or channel ID from URL
2. Call `channels.list(part="snippet,statistics", forHandle=HANDLE or id=CHANNEL_ID)`
3. Call `search.list(channelId=..., order="viewCount", maxResults=5, part="snippet", type="video")`
4. Calculate upload frequency from `publishedAt` dates of top 5 videos
5. Return dict with: `type`, `name`, `subscribers`, `total_views`, `video_count`, `upload_frequency_days`, `top_videos` (list of `{title, video_id}`), `thumbnail`

## Module Interface

```python
def fetch_stats(url: str, api_key: str) -> dict:
    ...
```

- Raises `ValueError` for unrecognised or non-YouTube URLs
- Raises `Exception` with the API error message for quota/auth/not-found errors
- Never returns partial data — either full dict or raises

## UI Layout

```
📊 ViewStats
Paste any YouTube channel or video URL to see stats.

[URL input                                    ] [ 🔍 Fetch Stats ]

--- VIDEO RESULT ---
┌────────────┐  Title: How to Get Abs in 30 Days
│ [thumbnail]│  Channel: FitnessGuru
│            │  Uploaded: Jan 15, 2025
└────────────┘  ─────────────────────────────
                👁 12.4M views  👍 340K likes  💬 8.2K comments
                ⏱ Duration: 4:32

--- CHANNEL RESULT ---
┌──────┐  FitnessGuru
│[icon]│  👥 2.1M subscribers · 📹 347 videos · 👁 890M total views
└──────┘  📅 Posts every ~3 days

  Top 5 Videos by Views
  ┌──────────────────────────────────────────┐
  │ 1. How to Get Abs in 30 Days — 12.4M    │
  │ 2. Best Pre-Workout Foods — 8.9M        │
  │ 3. 10-Min Morning Routine — 6.2M        │
  │ 4. Protein Myths Debunked — 4.1M        │
  │ 5. Leg Day for Beginners — 3.8M         │
  └──────────────────────────────────────────┘
```

## Error Handling

| Scenario | UI response |
|---|---|
| `YOUTUBE_API_KEY` empty in config.py | `st.error("Add your YOUTUBE_API_KEY to config.py")` before any API call |
| Unrecognised URL format | `st.error("That doesn't look like a YouTube channel or video URL.")` |
| Video/channel not found or private | `st.error("Video/channel not found or is private.")` |
| Quota exceeded (403) | `st.error("YouTube API quota exceeded. Try again tomorrow.")` |
| Invalid API key (400/403) | `st.error("Invalid YouTube API key. Check YOUTUBE_API_KEY in config.py.")` |

## Testing

File: `tests/test_viewstats.py` — all tests offline with mocked `googleapiclient.discovery.build`.

- **test_fetch_stats_video_returns_expected_keys** — mock API response, assert result dict has `type="video"` and all required keys
- **test_fetch_stats_channel_returns_expected_keys** — mock API response, assert result dict has `type="channel"` and all required keys including `top_videos` as a list
- **test_fetch_stats_raises_on_unknown_url** — assert `ValueError` raised for `"https://notayoutubeurl.com/foo"`

## New Dependency

`google-api-python-client>=2.0.0` — official Google API client, used only in `modules/viewstats.py`.

## Out of Scope

- Estimated revenue — real data only
- Historical charts / growth over time
- Competitor comparison
- Instagram / TikTok channels
