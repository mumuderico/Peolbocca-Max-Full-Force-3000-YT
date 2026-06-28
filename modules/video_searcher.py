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
