# YouTube Download Fix — Design Spec
**Date:** 2026-06-29
**Status:** Approved

---

## Overview

Fix YouTube download failures in the Downloader tab caused by yt-dlp bot detection ("Sign in to confirm you're not a bot", age-restriction blocks, rate limiting). Solution: try multiple YouTube player clients in sequence and add a realistic browser User-Agent. No new dependencies, no UI changes, no cookies required.

---

## Architecture

**Single file changed:** `modules/downloader.py`

No other files touched. The fix is entirely internal to the download logic.

---

## Implementation

### Player Client Fallback

yt-dlp supports different YouTube "player clients" via `extractor_args`. Each client has different restriction levels. The function tries them in order, stopping at the first success:

1. `web_embedded` — bypasses most age restrictions and bot checks
2. `tv_embedded` — TV client, less monitored than web
3. `mweb` — mobile web, different fingerprint

If all three fail, the original exception from the last attempt is raised.

### Additional yt-dlp Options

- `http_headers`: sets a realistic Chrome browser User-Agent to reduce bot fingerprinting
- `sleep_interval_requests: 1`: 1-second pause between requests to avoid rate limiting on consecutive downloads

### Code Shape

```python
_YT_PLAYER_CLIENTS = ["web_embedded", "tv_embedded", "mweb"]

def download_media(url, output_dir, media_type="video", quality="best") -> str:
    base_opts = { ... }  # existing options + new headers + sleep_interval
    
    last_error = None
    for client in _YT_PLAYER_CLIENTS:
        opts = {**base_opts, "extractor_args": {"youtube": {"player_client": [client]}}}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                ...
                return filename
        except Exception as e:
            last_error = e
            continue
    raise last_error
```

For non-YouTube URLs the player client arg is ignored by yt-dlp, so the retry loop adds negligible overhead (first attempt succeeds).

---

## Error Handling

- Each client failure is caught and the next client is tried silently
- If all clients fail, the last error is raised — the existing UI error handling in `tab_downloader.py` displays it unchanged
- No new error types introduced

---

## Limitations

- These player clients may be blocked by YouTube in future updates; when that happens, the list can be updated without changing any other code
- Does not fix private/login-required videos (by design — user explicitly does not want cookies)
- Does not affect non-YouTube URLs

---

## Out of Scope

- Cobalt API integration
- Cookie-based authentication
- UI changes
- Changes to audio extraction or quality selection logic
