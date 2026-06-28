# Channel Rankings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "🏆 Channel Rankings" tab that fetches YouTube trending videos by country, aggregates channel stats, and shows a sortable leaderboard with 1-hour per-country caching.

**Architecture:** `modules/channel_ranker.py` calls YouTube Data API v3 (up to 4 paginated trending-video requests + batched channel requests), returns unsorted channel dicts. `ui/tab_channel_ranking.py` handles caching in `st.session_state`, metric-based sorting, and renders the leaderboard. `app.py` gets a new tab entry.

**Tech Stack:** `google-api-python-client>=2.0.0`, YouTube Data API v3, `streamlit`, `pytest`, `pytest-mock`

## Global Constraints

- No Streamlit imports in `modules/channel_ranker.py`
- `google-api-python-client>=2.0.0` must be in `requirements.txt`
- `YOUTUBE_API_KEY` read from `config.YOUTUBE_API_KEY` (not hardcoded)
- Cache TTL is exactly 3600 seconds (1 hour) in `st.session_state`
- Cache keys: `f"ranking_{country_code}"` (data) and `f"ranking_{country_code}_ts"` (timestamp)
- All tests run offline — mock `modules.channel_ranker.build` (the imported name, not `googleapiclient.discovery.build`)
- `fetch_trending_channels` returns unsorted list; sorting happens in the UI layer only

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `requirements.txt` | Add `google-api-python-client>=2.0.0` |
| Modify | `config.py` | Add `YOUTUBE_API_KEY = ""` |
| Create | `modules/channel_ranker.py` | YouTube API fetch + aggregation logic |
| Create | `tests/test_channel_ranker.py` | Unit tests (all offline) |
| Create | `ui/tab_channel_ranking.py` | Streamlit UI, cache, sorting, leaderboard |
| Modify | `app.py` | Add new tab, import `render_channel_ranking` |

---

## Task 1: Dependencies + Config

**Files:**
- Modify: `requirements.txt`
- Modify: `config.py`

**Interfaces:**
- Produces: `config.YOUTUBE_API_KEY` (str) — consumed by Tasks 3 and 4

- [ ] **Step 1: Add dependency to requirements.txt**

Open `requirements.txt`. It currently ends with:
```
pytest>=8.2.0
pytest-mock>=3.14.0
```

Add one line after `pytest-mock`:
```
google-api-python-client>=2.0.0
```

- [ ] **Step 2: Install the new dependency**

```
pip install google-api-python-client>=2.0.0
```

Expected: installs `google-api-python-client` and its dependencies (`httplib2`, `uritemplate`, etc.) with no errors.

- [ ] **Step 3: Add YOUTUBE_API_KEY to config.py**

Open `config.py`. After the line `OPENAI_API_KEY = ""`, add:
```python
YOUTUBE_API_KEY = ""               # get a free key at console.cloud.google.com
```

Final config.py should look like:
```python
LLM_PROVIDER = "groq"              # "groq", "gemini", "anthropic", or "openai"
GROQ_API_KEY = ""
GEMINI_API_KEY = ""
ANTHROPIC_API_KEY = ""
OPENAI_API_KEY = ""
YOUTUBE_API_KEY = ""               # get a free key at console.cloud.google.com
ELEVENLABS_API_KEY = ""            # optional
TTS_PROVIDER = "edge-tts"          # "edge-tts" or "elevenlabs"
CAPTION_REMOVER_PROVIDER = "local" # "local" (NVIDIA GPU) or "replicate"
REPLICATE_API_KEY = ""             # only needed if CAPTION_REMOVER_PROVIDER = "replicate"

TRANSCRIPTAPI_KEY = "sk_az4CaFMdZSjHL0FgHDZTtFylhk4u1P-RxRroP5F7-1U"

SCRIPTS_DIR = "data/my_scripts"
DOWNLOADS_DIR = "downloads"
```

- [ ] **Step 4: Verify import works**

```
python -c "from googleapiclient.discovery import build; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add requirements.txt config.py
git commit -m "feat: add google-api-python-client dependency and YOUTUBE_API_KEY config"
```

---

## Task 2: Search module (`modules/channel_ranker.py` + tests)

**Files:**
- Create: `modules/channel_ranker.py`
- Create: `tests/test_channel_ranker.py`

**Interfaces:**
- Consumes: `googleapiclient.discovery.build` (imported as `build` inside the module)
- Produces: `fetch_trending_channels(country_code: str, api_key: str) -> list[dict]`
  - Each dict: `{"channel_id": str, "name": str, "thumbnail": str, "subscribers": int, "trending_count": int, "trending_views": int}`
  - Returns unsorted list
  - Raises `Exception` (including `HttpError`) on API errors — does NOT catch them

- [ ] **Step 1: Write the failing tests**

Create `tests/test_channel_ranker.py`:

```python
import pytest
from unittest.mock import MagicMock
from modules.channel_ranker import fetch_trending_channels


def _make_video_item(channel_id: str, view_count: str) -> dict:
    return {
        "snippet": {"channelId": channel_id},
        "statistics": {"viewCount": view_count},
    }


def _make_channel_item(channel_id: str, title: str, subscribers: str) -> dict:
    return {
        "id": channel_id,
        "snippet": {
            "title": title,
            "thumbnails": {"default": {"url": f"https://example.com/{channel_id}.jpg"}},
        },
        "statistics": {"subscriberCount": subscribers},
    }


@pytest.fixture
def mock_youtube(mocker):
    mock = MagicMock()
    mocker.patch("modules.channel_ranker.build", return_value=mock)
    return mock


def test_fetch_trending_channels_returns_expected_keys(mock_youtube):
    mock_youtube.videos.return_value.list.return_value.execute.return_value = {
        "items": [_make_video_item("UC123", "1000000")],
    }
    mock_youtube.channels.return_value.list.return_value.execute.return_value = {
        "items": [_make_channel_item("UC123", "TestChannel", "500000")],
    }

    results = fetch_trending_channels("US", "fake_key")

    assert len(results) == 1
    for key in ("channel_id", "name", "thumbnail", "subscribers", "trending_count", "trending_views"):
        assert key in results[0], f"Missing key: {key}"


def test_channels_aggregated_correctly(mock_youtube):
    mock_youtube.videos.return_value.list.return_value.execute.return_value = {
        "items": [
            _make_video_item("UC123", "1000000"),
            _make_video_item("UC123", "2000000"),
        ],
    }
    mock_youtube.channels.return_value.list.return_value.execute.return_value = {
        "items": [_make_channel_item("UC123", "TestChannel", "500000")],
    }

    results = fetch_trending_channels("US", "fake_key")

    assert len(results) == 1
    assert results[0]["trending_count"] == 2
    assert results[0]["trending_views"] == 3_000_000


def test_fetch_raises_on_api_error(mock_youtube):
    mock_youtube.videos.return_value.list.return_value.execute.side_effect = Exception("403 Quota exceeded")

    with pytest.raises(Exception):
        fetch_trending_channels("US", "fake_key")
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_channel_ranker.py -v
```

Expected: `ModuleNotFoundError` — `modules/channel_ranker.py` does not exist yet.

- [ ] **Step 3: Implement `modules/channel_ranker.py`**

```python
from googleapiclient.discovery import build


def fetch_trending_channels(country_code: str, api_key: str) -> list[dict]:
    youtube = build("youtube", "v3", developerKey=api_key)

    # Step 1: fetch up to 200 trending videos (4 pages × 50)
    channel_data = {}  # channel_id -> {"trending_count": int, "trending_views": int}
    next_page_token = None

    for _ in range(4):
        response = youtube.videos().list(
            part="snippet,statistics",
            chart="mostPopular",
            regionCode=country_code,
            maxResults=50,
            pageToken=next_page_token,
        ).execute()

        for item in response.get("items", []):
            channel_id = item["snippet"]["channelId"]
            views = int(item["statistics"].get("viewCount", 0))
            if channel_id not in channel_data:
                channel_data[channel_id] = {"trending_count": 0, "trending_views": 0}
            channel_data[channel_id]["trending_count"] += 1
            channel_data[channel_id]["trending_views"] += views

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    if not channel_data:
        return []

    # Step 2: fetch channel details in batches of 50
    channel_ids = list(channel_data.keys())
    channels = []

    for i in range(0, len(channel_ids), 50):
        batch = channel_ids[i:i + 50]
        response = youtube.channels().list(
            part="snippet,statistics",
            id=",".join(batch),
        ).execute()

        for item in response.get("items", []):
            cid = item["id"]
            channels.append({
                "channel_id": cid,
                "name": item["snippet"]["title"],
                "thumbnail": item["snippet"]["thumbnails"].get("default", {}).get("url", ""),
                "subscribers": int(item["statistics"].get("subscriberCount", 0)),
                "trending_count": channel_data[cid]["trending_count"],
                "trending_views": channel_data[cid]["trending_views"],
            })

    return channels
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_channel_ranker.py -v
```

Expected output:
```
tests/test_channel_ranker.py::test_fetch_trending_channels_returns_expected_keys PASSED
tests/test_channel_ranker.py::test_channels_aggregated_correctly PASSED
tests/test_channel_ranker.py::test_fetch_raises_on_api_error PASSED
3 passed in ...s
```

- [ ] **Step 5: Commit**

```bash
git add modules/channel_ranker.py tests/test_channel_ranker.py
git commit -m "feat: add channel_ranker module with YouTube trending aggregation"
```

---

## Task 3: UI tab (`ui/tab_channel_ranking.py`)

**Files:**
- Create: `ui/tab_channel_ranking.py`

**Interfaces:**
- Consumes: `fetch_trending_channels(country_code: str, api_key: str) -> list[dict]` from `modules.channel_ranker`
- Consumes: `config.YOUTUBE_API_KEY` (str)
- Produces: `render_channel_ranking()` — called by `app.py`

- [ ] **Step 1: Create `ui/tab_channel_ranking.py`**

```python
import time
import streamlit as st
import config
from modules.channel_ranker import fetch_trending_channels


COUNTRIES = {
    "Argentina": "AR", "Australia": "AU", "Austria": "AT", "Belgium": "BE",
    "Bolivia": "BO", "Brazil": "BR", "Canada": "CA", "Chile": "CL",
    "Colombia": "CO", "Croatia": "HR", "Czech Republic": "CZ", "Denmark": "DK",
    "Ecuador": "EC", "Egypt": "EG", "Finland": "FI", "France": "FR",
    "Germany": "DE", "Ghana": "GH", "Greece": "GR", "Hungary": "HU",
    "India": "IN", "Indonesia": "ID", "Ireland": "IE", "Israel": "IL",
    "Italy": "IT", "Japan": "JP", "Kenya": "KE", "Malaysia": "MY",
    "Mexico": "MX", "Morocco": "MA", "Netherlands": "NL", "New Zealand": "NZ",
    "Nigeria": "NG", "Norway": "NO", "Pakistan": "PK", "Panama": "PA",
    "Paraguay": "PY", "Peru": "PE", "Philippines": "PH", "Poland": "PL",
    "Portugal": "PT", "Romania": "RO", "Russia": "RU", "Saudi Arabia": "SA",
    "Singapore": "SG", "South Africa": "ZA", "South Korea": "KR", "Spain": "ES",
    "Sweden": "SE", "Switzerland": "CH", "Taiwan": "TW", "Thailand": "TH",
    "Turkey": "TR", "Ukraine": "UA", "United Arab Emirates": "AE",
    "United Kingdom": "GB", "United States": "US", "Uruguay": "UY",
    "Venezuela": "VE", "Vietnam": "VN", "Zimbabwe": "ZW",
}

CACHE_TTL = 3600  # 1 hour


def _fmt_number(n: int) -> str:
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def render_channel_ranking():
    st.header("Channel Rankings")
    st.caption("Top channels dominating YouTube trending right now, by country.")

    if not config.YOUTUBE_API_KEY:
        st.error("Add your YOUTUBE_API_KEY to config.py to use this feature.")
        return

    col1, col2 = st.columns([2, 2])
    with col1:
        sorted_countries = sorted(COUNTRIES.keys())
        default_idx = sorted_countries.index("United States")
        country_name = st.selectbox("Country", options=sorted_countries, index=default_idx)
    with col2:
        metric = st.radio("Rank by", ["🔥 Trending Videos", "👁 Trending Views"], horizontal=True)

    country_code = COUNTRIES[country_name]
    cache_key = f"ranking_{country_code}"
    cache_ts_key = f"ranking_{country_code}_ts"

    now = time.time()
    cached_ts = st.session_state.get(cache_ts_key, 0)
    is_fresh = (now - cached_ts) < CACHE_TTL

    if is_fresh and cache_key in st.session_state:
        age_min = int((now - cached_ts) / 60)
        st.caption(f"Last updated {age_min} min ago · click Load Rankings to refresh")

    if st.button("Load Rankings", type="primary"):
        with st.spinner(f"Fetching trending data for {country_name}..."):
            try:
                results = fetch_trending_channels(country_code, config.YOUTUBE_API_KEY)
                st.session_state[cache_key] = results
                st.session_state[cache_ts_key] = time.time()
            except Exception as e:
                msg = str(e)
                if "quota" in msg.lower() or "403" in msg:
                    st.error("YouTube API quota exceeded. Try again tomorrow.")
                elif "400" in msg or "invalid" in msg.lower():
                    st.error("Invalid YouTube API key. Check YOUTUBE_API_KEY in config.py.")
                else:
                    st.error(f"Failed to fetch rankings: {e}")
                return

    results = st.session_state.get(cache_key)
    if not results:
        return

    sort_key = "trending_count" if "Videos" in metric else "trending_views"
    sorted_results = sorted(results, key=lambda x: x[sort_key], reverse=True)

    st.divider()
    for rank, ch in enumerate(sorted_results, start=1):
        col_rank, col_thumb, col_info = st.columns([0.5, 1, 8])
        with col_rank:
            st.markdown(f"**#{rank}**")
        with col_thumb:
            if ch["thumbnail"]:
                st.image(ch["thumbnail"], width=40)
        with col_info:
            yt_url = f"https://www.youtube.com/channel/{ch['channel_id']}"
            st.markdown(
                f'<a href="{yt_url}" target="_blank" style="color:#e2e8f0;font-weight:600;text-decoration:none;">{ch["name"]}</a>'
                f'&nbsp;&nbsp;·&nbsp;&nbsp;👥 {_fmt_number(ch["subscribers"])} subs'
                f'&nbsp;&nbsp;·&nbsp;&nbsp;🔥 {ch["trending_count"]} trending'
                f'&nbsp;&nbsp;·&nbsp;&nbsp;👁 {_fmt_number(ch["trending_views"])} views',
                unsafe_allow_html=True,
            )
```

- [ ] **Step 2: Verify syntax**

```
python -c "import py_compile; py_compile.compile('ui/tab_channel_ranking.py', doraise=True); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add ui/tab_channel_ranking.py
git commit -m "feat: add channel ranking UI tab"
```

---

## Task 4: Wire into `app.py`

**Files:**
- Modify: `app.py`

**Interfaces:**
- Consumes: `render_channel_ranking()` from `ui.tab_channel_ranking`

- [ ] **Step 1: Add import to app.py**

Find the imports block at the top of `app.py` (lines importing from `ui.*`). Add:

```python
from ui.tab_channel_ranking import render_channel_ranking
```

alongside the existing `from ui.tab_*` imports.

- [ ] **Step 2: Add the new tab**

Find the `st.tabs([...])` call in `app.py`. Add `"🏆  Channel Rankings"` as the last entry and unpack one more variable. For example, if app.py currently has:

```python
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "✍️  Script Writer",
    "⬇️  Downloader",
    "📝  Transcript",
    "🎞️  Caption Remover",
    "🔎  Video Search",
])
```

Change to:

```python
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "✍️  Script Writer",
    "⬇️  Downloader",
    "📝  Transcript",
    "🎞️  Caption Remover",
    "🔎  Video Search",
    "🏆  Channel Rankings",
])
```

- [ ] **Step 3: Add the tab body**

After the last `with tabN:` block, add:

```python
with tab6:
    render_channel_ranking()
```

- [ ] **Step 4: Run the full test suite**

```
pytest tests/ -v
```

Expected: all existing tests pass (including the 3 new channel ranker tests). The one pre-existing failure in `test_caption_remover.py::test_remove_captions_local_provider_calls_local` is unrelated to this feature and can be ignored.

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "feat: wire Channel Rankings tab into app"
```
