import re
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
]


def extract_video_id(url: str) -> str:
    for pattern in _VIDEO_ID_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


def get_transcript(youtube_url: str, include_timestamps: bool = False) -> str:
    video_id = extract_video_id(youtube_url)
    api = YouTubeTranscriptApi()
    fetched = api.fetch(video_id)

    if include_timestamps:
        lines = [f"[{int(entry.start)}s] {entry.text}" for entry in fetched]
    else:
        lines = [entry.text for entry in fetched]

    return "\n".join(lines)


def translate_text(text: str, target_language_code: str) -> str:
    translator = GoogleTranslator(source="auto", target=target_language_code)
    return translator.translate(text)
