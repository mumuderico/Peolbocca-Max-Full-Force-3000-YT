import os
import tempfile
import yt_dlp


QUALITY_FORMATS = {
    "best": "best[ext=mp4]/best",
    "medium": "best[height<=720][ext=mp4]/best[height<=720]/best",
    "low": "best[height<=480][ext=mp4]/best[height<=480]/best",
}


def download_media(
    url: str,
    output_dir: str,
    media_type: str = "video",
    quality: str = "best",
) -> str:
    os.makedirs(output_dir, exist_ok=True)

    _win_ffmpeg = r"C:\Program Files\FFmpeg\bin"
    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "format": QUALITY_FORMATS.get(quality, QUALITY_FORMATS["best"]),
        "quiet": True,
        "no_warnings": True,
    }
    if os.path.isdir(_win_ffmpeg):
        ydl_opts["ffmpeg_location"] = _win_ffmpeg

    ydl_opts["extractor_args"] = {"youtube": {"player_client": ["ios"]}}

    _tmp_cookies = None
    cookies_content = os.environ.get("YOUTUBE_COOKIES")
    if cookies_content:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        tmp.write(cookies_content)
        tmp.close()
        _tmp_cookies = tmp.name
        ydl_opts["cookiefile"] = _tmp_cookies

    if media_type == "audio":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if media_type == "audio":
                filename = os.path.splitext(filename)[0] + ".mp3"
            return filename
    finally:
        if _tmp_cookies and os.path.exists(_tmp_cookies):
            os.unlink(_tmp_cookies)
