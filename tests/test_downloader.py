import pytest
from unittest.mock import MagicMock
from modules.downloader import download_media


def _make_mock_ydl(mocker, filename: str, ext: str):
    mock_ydl = MagicMock()
    mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
    mock_ydl.__exit__ = MagicMock(return_value=False)
    mock_ydl.extract_info.return_value = {"title": "test", "ext": ext}
    mock_ydl.prepare_filename.return_value = filename
    mocker.patch("yt_dlp.YoutubeDL", return_value=mock_ydl)
    return mock_ydl


def test_download_video_returns_mp4_path(tmp_path, mocker):
    expected = str(tmp_path / "test.mp4")
    _make_mock_ydl(mocker, expected, "mp4")

    result = download_media(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        output_dir=str(tmp_path),
        media_type="video",
        quality="best",
    )
    assert result == expected


def test_download_audio_returns_mp3_path(tmp_path, mocker):
    base_path = str(tmp_path / "test.webm")
    _make_mock_ydl(mocker, base_path, "webm")

    result = download_media(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        output_dir=str(tmp_path),
        media_type="audio",
        quality="best",
    )
    assert result.endswith(".mp3")


def test_download_uses_correct_format_for_medium_quality(tmp_path, mocker):
    expected = str(tmp_path / "test.mp4")
    mock_ydl = _make_mock_ydl(mocker, expected, "mp4")
    import yt_dlp

    download_media(
        url="https://www.youtube.com/watch?v=test",
        output_dir=str(tmp_path),
        media_type="video",
        quality="medium",
    )

    called_opts = yt_dlp.YoutubeDL.call_args[0][0]
    assert "720" in called_opts["format"]


def test_download_propagates_ydl_exception(tmp_path, mocker):
    mock_ydl = MagicMock()
    mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
    mock_ydl.__exit__ = MagicMock(return_value=False)
    mock_ydl.extract_info.side_effect = Exception("Video unavailable")
    mocker.patch("yt_dlp.YoutubeDL", return_value=mock_ydl)

    with pytest.raises(Exception, match="Video unavailable"):
        download_media("https://invalid.example.com", str(tmp_path))
