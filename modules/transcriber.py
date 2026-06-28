import re
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from deep_translator import GoogleTranslator


SUPPORTED_LANGUAGES = {
    "English": "en",
    "Portuguese": "pt",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
    "Chinese (Simplified)": "zh-CN",
}

_VIDEO_ID_PATTERNS = [
    r"(?:v=)([a-zA-Z0-9_-]{11})",
    r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
    r"(?:shorts/)([a-zA-Z0-9_-]{11})",
    r"(?:embed/)([a-zA-Z0-9_-]{11})",
]


def extract_video_id(url: str) -> str:
    for pattern in _VIDEO_ID_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


def _get_transcript_transcriptapi(youtube_url: str, include_timestamps: bool, api_key: str) -> str:
    response = requests.get(
        "https://transcriptapi.com/api/v2/youtube/transcript",
        params={
            "video_url": youtube_url,
            "format": "json",
            "include_timestamp": str(include_timestamps).lower(),
        },
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    entries = data.get("transcript", [])
    if include_timestamps:
        lines = [f"[{int(e['start'])}s] {e['text']}" for e in entries]
    else:
        lines = [e["text"] for e in entries]
    return "\n".join(lines)


def _get_transcript_local(youtube_url: str, include_timestamps: bool) -> str:
    video_id = extract_video_id(youtube_url)
    api = YouTubeTranscriptApi()
    fetched = api.fetch(video_id)
    if include_timestamps:
        lines = [f"[{int(entry.start)}s] {entry.text}" for entry in fetched]
    else:
        lines = [entry.text for entry in fetched]
    return "\n".join(lines)


def get_transcript(youtube_url: str, include_timestamps: bool = False, api_key: str = "") -> str:
    if api_key:
        return _get_transcript_transcriptapi(youtube_url, include_timestamps, api_key)
    return _get_transcript_local(youtube_url, include_timestamps)


def translate_text(text: str, target_language_code: str) -> str:
    translator = GoogleTranslator(source="auto", target=target_language_code)
    max_chars = 4900
    if len(text) <= max_chars:
        return translator.translate(text)

    lines = text.split("\n")
    chunks = []
    current = []
    current_len = 0
    for line in lines:
        needed = len(line) + (1 if current else 0)
        if current_len + needed > max_chars:
            chunks.append("\n".join(current))
            current = [line]
            current_len = len(line)
        else:
            current.append(line)
            current_len += needed
    if current:
        chunks.append("\n".join(current))

    return "\n".join(translator.translate(chunk) for chunk in chunks)
