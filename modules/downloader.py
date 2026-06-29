import os
import yt_dlp


QUALITY_FORMATS = {
    "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "medium": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]",
    "low": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best[height<=480]",
}

_QUALITY_RES = {"best": None, "medium": "720p", "low": "480p"}


def _download_with_pytubefix(url: str, output_dir: str, media_type: str, quality: str) -> str:
    from pytubefix import YouTube
    yt = YouTube(url, use_oauth=False, allow_oauth_cache=False)

    if media_type == "audio":
        stream = yt.streams.get_audio_only()
        path = stream.download(output_path=output_dir)
        base = os.path.splitext(path)[0] + ".mp3"
        os.rename(path, base)
        return base

    res = _QUALITY_RES.get(quality)
    stream = None
    if res:
        stream = yt.streams.filter(res=res, file_extension="mp4", progressive=True).first()
    if stream is None:
        stream = yt.streams.get_highest_resolution()
    return stream.download(output_path=output_dir)


def download_media(
    url: str,
    output_dir: str,
    media_type: str = "video",
    quality: str = "best",
) -> str:
    os.makedirs(output_dir, exist_ok=True)

    try:
        return _download_with_pytubefix(url, output_dir, media_type, quality)
    except Exception:
        pass

    _win_ffmpeg = r"C:\Program Files\FFmpeg\bin"
    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "format": QUALITY_FORMATS.get(quality, QUALITY_FORMATS["best"]),
        "quiet": True,
        "no_warnings": True,
    }
    if os.path.isdir(_win_ffmpeg):
        ydl_opts["ffmpeg_location"] = _win_ffmpeg

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
