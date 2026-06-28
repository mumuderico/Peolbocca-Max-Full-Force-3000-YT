import yt_dlp


def _search_platform(keyword: str, n: int, platform: str) -> list[dict]:
    # Fetch 3× to have enough after filtering to ≤60s
    query = f"ytsearch{n * 3}:{keyword} shorts"
    ydl_opts = {"quiet": True, "no_warnings": True, "extract_flat": True}
    results = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        for entry in (info.get("entries") or []):
            if not entry:
                continue
            duration = entry.get("duration") or 0
            # Skip YouTube videos longer than 60s — Shorts are ≤60s
            if platform == "youtube_shorts" and duration > 60:
                continue
            video_id = entry.get("id", "")
            url = f"https://www.youtube.com/shorts/{video_id}"
            thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
            results.append({
                "title": entry.get("title", "Unknown"),
                "url": url,
                "thumbnail": thumbnail,
                "view_count": entry.get("view_count") or 0,
                "duration": duration,
                "platform": "youtube_shorts",
            })
            if len(results) >= n:
                break
    return results


def search_videos(keyword: str, max_results: int = 10) -> tuple[list[dict], list[str]]:
    try:
        results = _search_platform(keyword, max_results, "youtube_shorts")
    except Exception as exc:
        return [], [f"YouTube Shorts search unavailable: {exc}"]
    return results, []
