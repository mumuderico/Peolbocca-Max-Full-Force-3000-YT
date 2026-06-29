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
