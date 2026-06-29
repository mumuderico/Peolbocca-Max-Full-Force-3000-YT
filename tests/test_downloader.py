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


def test_download_tries_next_client_on_failure(mocker):
    def fake_ydl(opts):
        client = opts.get("extractor_args", {}).get("youtube", {}).get("player_client", [None])[0]
        ctx = mocker.MagicMock()
        if client == "web_embedded":
            ctx.__enter__ = mocker.MagicMock(return_value=ctx)
            ctx.__exit__ = mocker.MagicMock(return_value=False)
            ctx.extract_info = mocker.MagicMock(side_effect=Exception("bot detected"))
        else:
            info = {"title": "test", "ext": "mp4"}
            ctx.__enter__ = mocker.MagicMock(return_value=ctx)
            ctx.__exit__ = mocker.MagicMock(return_value=False)
            ctx.extract_info = mocker.MagicMock(return_value=info)
            ctx.prepare_filename = mocker.MagicMock(return_value="/tmp/test.mp4")
        return ctx

    mocker.patch("yt_dlp.YoutubeDL", side_effect=fake_ydl)
    from modules.downloader import download_media
    result = download_media("https://youtube.com/watch?v=test", "/tmp", "video", "best")
    assert result == "/tmp/test.mp4"


def test_download_raises_after_all_clients_fail(mocker):
    ctx = mocker.MagicMock()
    ctx.__enter__ = mocker.MagicMock(return_value=ctx)
    ctx.__exit__ = mocker.MagicMock(return_value=False)
    ctx.extract_info = mocker.MagicMock(side_effect=Exception("all blocked"))
    mocker.patch("yt_dlp.YoutubeDL", return_value=ctx)
    from modules.downloader import download_media
    with pytest.raises(Exception, match="all blocked"):
        download_media("https://youtube.com/watch?v=test", "/tmp", "video", "best")


def test_download_sets_browser_user_agent(mocker):
    captured = {}

    def fake_ydl(opts):
        captured["opts"] = opts
        ctx = mocker.MagicMock()
        ctx.__enter__ = mocker.MagicMock(return_value=ctx)
        ctx.__exit__ = mocker.MagicMock(return_value=False)
        info = {"title": "test", "ext": "mp4"}
        ctx.extract_info = mocker.MagicMock(return_value=info)
        ctx.prepare_filename = mocker.MagicMock(return_value="/tmp/test.mp4")
        return ctx

    mocker.patch("yt_dlp.YoutubeDL", side_effect=fake_ydl)
    from modules.downloader import download_media
    download_media("https://youtube.com/watch?v=test", "/tmp", "video", "best")
    assert "User-Agent" in captured["opts"].get("http_headers", {})
