import pytest
from unittest.mock import MagicMock
from modules.transcriber import (
    extract_video_id,
    get_transcript,
    translate_text,
    SUPPORTED_LANGUAGES,
)


def test_extract_video_id_standard_url():
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_short_url():
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_with_extra_params():
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s") == "dQw4w9WgXcQ"


def test_extract_video_id_invalid_raises():
    with pytest.raises(ValueError, match="Could not extract video ID"):
        extract_video_id("https://www.google.com")


def test_get_transcript_plain(mocker):
    entry1 = MagicMock()
    entry1.text = "Hello world"
    entry1.start = 0.0
    entry2 = MagicMock()
    entry2.text = "This is a test"
    entry2.start = 2.0

    mock_api = MagicMock()
    mock_api.fetch.return_value = [entry1, entry2]
    mocker.patch("modules.transcriber.YouTubeTranscriptApi", return_value=mock_api)

    result = get_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert "Hello world" in result
    assert "This is a test" in result


def test_get_transcript_with_timestamps(mocker):
    entry = MagicMock()
    entry.text = "Hello"
    entry.start = 5.3

    mock_api = MagicMock()
    mock_api.fetch.return_value = [entry]
    mocker.patch("modules.transcriber.YouTubeTranscriptApi", return_value=mock_api)

    result = get_transcript(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ", include_timestamps=True
    )
    assert "[5s]" in result
    assert "Hello" in result


def test_get_transcript_no_captions_raises(mocker):
    from youtube_transcript_api import TranscriptsDisabled

    mock_api = MagicMock()
    mock_api.fetch.side_effect = TranscriptsDisabled("dQw4w9WgXcQ")
    mocker.patch("modules.transcriber.YouTubeTranscriptApi", return_value=mock_api)

    with pytest.raises(TranscriptsDisabled):
        get_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")


def test_translate_text(mocker):
    mock_translator = MagicMock()
    mock_translator.translate.return_value = "Olá mundo"
    mocker.patch("modules.transcriber.GoogleTranslator", return_value=mock_translator)

    result = translate_text("Hello world", "pt")
    assert result == "Olá mundo"
    mock_translator.translate.assert_called_once_with("Hello world")


def test_supported_languages_contains_required_entries():
    assert "English" in SUPPORTED_LANGUAGES
    assert "Portuguese" in SUPPORTED_LANGUAGES
    assert "Spanish" in SUPPORTED_LANGUAGES
    assert SUPPORTED_LANGUAGES["Portuguese"] == "pt"
    assert SUPPORTED_LANGUAGES["English"] == "en"
