# YouTube Download Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix YouTube bot-detection failures in yt-dlp by retrying with multiple player clients and a realistic browser User-Agent.

**Architecture:** Modify `modules/downloader.py` to wrap the download attempt in a loop over three YouTube player clients (`web_embedded`, `tv_embedded`, `mweb`). On non-YouTube URLs the client arg is ignored, so overhead is zero. All other behavior (quality, audio extraction, output path) is unchanged.

**Tech Stack:** Python, yt-dlp (already a project dependency).

## Global Constraints

- Only `modules/downloader.py` and `tests/test_downloader.py` are touched — no UI changes
- No new dependencies
- No cookies
- Player clients to try in order: `["web_embedded", "tv_embedded", "mweb"]`
- User-Agent: `"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"`
- `sleep_interval_requests`: `1`

---

### Task 1: Add player-client fallback to `download_media`

**Files:**
- Modify: `modules/downloader.py`
- Modify: `tests/test_downloader.py`

**Interfaces:**
- Produces: same `download_media(url, output_dir, media_type, quality) -> str` signature — callers unchanged

- [ ] **Step 1: Write the failing tests**

Open `tests/test_downloader.py` and add these tests at the end of the file:

```python
def test_download_tries_next_client_on_failure(mocker):
    def fake_ydl(opts):
        client = opts.get("extractor_args", {}).get("youtube", {}).get("player_client", [None])[0]
        ctx = mocker.MagicMock()
        if client == "web_embedded":
            ctx.__enter__ = mocker.MagicMock(return_value=ctx)
            ctx.__exit__ = mocker.MagicMock(return_value=False)
            ctx.extract_info = mocker.MagicMock(side_effect=Exception("bot detected"))
        else:
            info = {"title": "test", "ext": "mp4"}
            ctx.__enter__ = mocker.MagicMock(return_value=ctx)
            ctx.__exit__ = mocker.MagicMock(return_value=False)
            ctx.extract_info = mocker.MagicMock(return_value=info)
            ctx.prepare_filename = mocker.MagicMock(return_value="/tmp/test.mp4")
        return ctx

    mocker.patch("yt_dlp.YoutubeDL", side_effect=fake_ydl)
    from modules.downloader import download_media
    result = download_media("https://youtube.com/watch?v=test", "/tmp", "video", "best")
    assert result == "/tmp/test.mp4"


def test_download_raises_after_all_clients_fail(mocker):
    ctx = mocker.MagicMock()
    ctx.__enter__ = mocker.MagicMock(return_value=ctx)
    ctx.__exit__ = mocker.MagicMock(return_value=False)
    ctx.extract_info = mocker.MagicMock(side_effect=Exception("all blocked"))
    mocker.patch("yt_dlp.YoutubeDL", return_value=ctx)
    from modules.downloader import download_media
    with pytest.raises(Exception, match="all blocked"):
        download_media("https://youtube.com/watch?v=test", "/tmp", "video", "best")


def test_download_sets_browser_user_agent(mocker):
    captured = {}

    def fake_ydl(opts):
        captured["opts"] = opts
        ctx = mocker.MagicMock()
        ctx.__enter__ = mocker.MagicMock(return_value=ctx)
        ctx.__exit__ = mocker.MagicMock(return_value=False)
        info = {"title": "test", "ext": "mp4"}
        ctx.extract_info = mocker.MagicMock(return_value=info)
        ctx.prepare_filename = mocker.MagicMock(return_value="/tmp/test.mp4")
        return ctx

    mocker.patch("yt_dlp.YoutubeDL", side_effect=fake_ydl)
    from modules.downloader import download_media
    download_media("https://youtube.com/watch?v=test", "/tmp", "video", "best")
    assert "User-Agent" in captured["opts"].get("http_headers", {})
```

Also add `import pytest` at the top of the file if not already present.

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_downloader.py::test_download_tries_next_client_on_failure tests/test_downloader.py::test_download_raises_after_all_clients_fail tests/test_downloader.py::test_download_sets_browser_user_agent -v
```

Expected: all 3 FAIL (current `download_media` has no retry loop).

- [ ] **Step 3: Rewrite `modules/downloader.py`**

Replace the entire file with:

```python
import os
import yt_dlp


QUALITY_FORMATS = {
    "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "medium": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]",
    "low": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best[height<=480]",
}

_YT_PLAYER_CLIENTS = ["web_embedded", "tv_embedded", "mweb"]

_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


def download_media(
    url: str,
    output_dir: str,
    media_type: str = "video",
    quality: str = "best",
) -> str:
    os.makedirs(output_dir, exist_ok=True)

    base_opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "format": QUALITY_FORMATS.get(quality, QUALITY_FORMATS["best"]),
        "quiet": True,
        "no_warnings": True,
        "http_headers": {"User-Agent": _BROWSER_UA},
        "sleep_interval_requests": 1,
    }
    if os.path.isdir(r"C:\Program Files\FFmpeg\bin"):
        base_opts["ffmpeg_location"] = r"C:\Program Files\FFmpeg\bin"

    if media_type == "audio":
        base_opts["format"] = "bestaudio/best"
        base_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]

    last_error = None
    for client in _YT_PLAYER_CLIENTS:
        opts = {**base_opts, "extractor_args": {"youtube": {"player_client": [client]}}}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if media_type == "audio":
                    filename = os.path.splitext(filename)[0] + ".mp3"
                return filename
        except Exception as e:
            last_error = e
            continue

    raise last_error
```

- [ ] **Step 4: Run tests to confirm they pass**

```
pytest tests/test_downloader.py -v
```

Expected: all tests PASS including the 3 new ones.

- [ ] **Step 5: Commit and push**

```
git add modules/downloader.py tests/test_downloader.py
git commit -m "fix: retry YouTube downloads with multiple player clients to bypass bot detection"
git push origin main
```
