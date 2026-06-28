# Channel Ranking Feature — Design Spec
**Date:** 2026-06-28  
**Status:** Approved

## Overview

Add a "🏆 Channel Rankings" tab that shows the top channels currently dominating YouTube trending in any country. Users pick a country, choose a ranking metric (trending video count or total trending views), and see a live leaderboard. Results are cached per country for 1 hour — switching the metric re-sorts cached data without a refetch.

## Architecture

### New files
- `modules/channel_ranker.py` — pure YouTube Data API v3 logic, no Streamlit imports
- `ui/tab_channel_ranking.py` — Streamlit UI: country selector, metric toggle, ranked table
- `tests/test_channel_ranker.py` — unit tests with mocked API calls

### Modified files
- `app.py` — add 7th tab, import `render_channel_ranking`

### Dependencies
- `google-api-python-client` — already added by ViewStats feature
- `config.YOUTUBE_API_KEY` — shared with ViewStats

## Module Interface

```python
def fetch_trending_channels(country_code: str, api_key: str) -> list[dict]:
    ...
```

Returns a list of channel dicts (unsorted — sorting is done in the UI layer):

```python
{
    "channel_id": str,
    "name": str,
    "thumbnail": str,       # channel icon URL
    "subscribers": int,
    "trending_count": int,  # number of videos in current trending list
    "trending_views": int,  # sum of views across their trending videos
}
```

Raises `Exception` with a descriptive message on API errors (quota, invalid key, network).

## Data Flow

### Fetch path (cache miss)
1. 4 paginated calls to `videos.list(part="snippet,statistics", chart="mostPopular", regionCode=COUNTRY, maxResults=50)` → up to 200 trending videos
2. Extract unique channel IDs and accumulate per-channel `trending_count` and `trending_views` from video statistics
3. Batch `channels.list(part="snippet,statistics", id=",".join(batch))` calls (50 IDs per call) → channel name, thumbnail, subscriber count
4. Merge into list of channel dicts
5. Store in `st.session_state[f"ranking_{country_code}"]` with `st.session_state[f"ranking_{country_code}_ts"]` = current timestamp

### Cache path (< 1 hour old)
- Skip all API calls
- Re-sort cached list by selected metric
- Show "Last updated X min ago" label

### Metric toggle (no refetch)
- **🔥 Trending Videos** — sort descending by `trending_count`
- **👁 Trending Views** — sort descending by `trending_views`
- Switching metric re-sorts in-memory; no API call fired

## UI Layout

```
🏆 Channel Rankings
Top channels dominating YouTube trending right now.

Country   [Brazil 🇧🇷 ▼]    Rank by  ● 🔥 Trending Videos  ○ 👁 Trending Views
[ Load Rankings ]                     Last updated 4 min ago

#   Channel          Subscribers   Trending Videos   Trending Views
─────────────────────────────────────────────────────────────────────
1   [icon] MrBeast   230M          8                 42.1M
2   [icon] Loud Babi 19M           6                 18.4M
3   [icon] CazéTV    7.2M          5                 11.2M
...
```

- Rank numbers 1–N (N = number of unique channels found, typically 20–80)
- Channel thumbnail shown as small icon
- Subscribers, trending_count, trending_views all formatted (e.g. 230M, 42.1M)
- Clicking channel name opens their YouTube channel page in a new tab

## Error Handling

| Scenario | UI response |
|---|---|
| `YOUTUBE_API_KEY` empty | `st.error("Add your YOUTUBE_API_KEY to config.py")` — shown before any fetch |
| Quota exceeded (403) | `st.error("YouTube API quota exceeded. Try again tomorrow.")` |
| Invalid API key (400/403) | `st.error("Invalid YouTube API key. Check YOUTUBE_API_KEY in config.py.")` |
| Country returns 0 results | `st.info("No trending data available for this country. Try another.")` |

## Country List

A hardcoded dict of `{display_name: iso_code}` covering ~60 major countries across all regions, used to populate the country selectbox. Sorted alphabetically by display name.

Examples: `"Brazil": "BR"`, `"United States": "US"`, `"Japan": "JP"`, `"South Korea": "KR"`, `"India": "IN"`, `"United Kingdom": "GB"`, `"Germany": "DE"`, `"France": "FR"`, `"Mexico": "MX"`, `"Indonesia": "ID"`.

## Testing

File: `tests/test_channel_ranker.py` — all tests offline with mocked `googleapiclient.discovery.build`.

- **test_fetch_trending_channels_returns_expected_keys** — mock `videos.list` and `channels.list` responses, assert each returned dict contains `channel_id`, `name`, `thumbnail`, `subscribers`, `trending_count`, `trending_views`
- **test_channels_aggregated_correctly** — two videos from the same channel in the mock response; assert `trending_count == 2` and `trending_views` equals the sum of both videos' view counts
- **test_fetch_raises_on_api_error** — mock API to raise `HttpError`, assert it propagates as an `Exception`

## Out of Scope

- TikTok rankings — TikTok's API requires developer approval and doesn't expose trending channels
- All-time global top 100 — requires paid data sources (Social Blade, HypeAuditor)
- Historical trend charts — can be added later
- Filtering by video category within a country
