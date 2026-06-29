import os
import yt_dlp


QUALITY_FORMATS = {
    "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "medium": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]",
    "low": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best[height<=480]",
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
        "quiet": False,
        "verbose": True,
    }
    if os.path.isdir(_win_ffmpeg):
        ydl_opts["ffmpeg_location"] = _win_ffmpeg

    # Point yt-dlp to nodejs binary (Debian installs as /usr/bin/nodejs, not /usr/bin/node)
    if os.path.exists("/usr/bin/nodejs"):
        ydl_opts["js_runtimes"] = {"node": {"path": "/usr/bin/nodejs"}}

    cookies_file = os.environ.get("YOUTUBE_COOKIES_FILE")
    if cookies_file and os.path.exists(cookies_file):
        ydl_opts["cookiefile"] = cookies_file
        print(f"[downloader] using cookies file: {cookies_file}")
    else:
        print(f"[downloader] no cookies file found (YOUTUBE_COOKIES_FILE={cookies_file!r})")

    if media_type == "audio":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if media_type == "audio":
            filename = os.path.splitext(filename)[0] + ".mp3"
        return filename
