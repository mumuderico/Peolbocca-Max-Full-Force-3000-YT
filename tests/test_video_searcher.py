import pytest
from unittest.mock import MagicMock
from modules.video_searcher import search_videos, _search_platform


def _make_mock_ydl(entries):
    mock_ydl = MagicMock()
    mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
    mock_ydl.__exit__ = MagicMock(return_value=False)
    mock_ydl.extract_info.return_value = {"entries": entries}
    return mock_ydl


FAKE_ENTRY = {
    "id": "abc123",
    "title": "Morning Routine Video",
    "url": "https://example.com/video/abc123",
    "thumbnail": "https://example.com/thumb.jpg",
    "view_count": 1_200_000,
    "duration": 47,
}


def test_search_returns_expected_keys(mocker):
    mock_ydl = _make_mock_ydl([FAKE_ENTRY])
    mocker.patch("yt_dlp.YoutubeDL", return_value=mock_ydl)

    results, errors = search_videos("morning routine", max_results=2)

    assert isinstance(results, list)
    assert len(errors) == 0
    for result in results:
        for key in ("title", "url", "thumbnail", "view_count", "duration", "platform"):
            assert key in result, f"Missing key: {key}"


def test_search_success_returns_results_and_no_errors(mocker):
    good_result = {
        "title": "Good Video",
        "url": "https://www.youtube.com/shorts/abc123",
        "thumbnail": "https://i.ytimg.com/vi/abc123/hqdefault.jpg",
        "view_count": 1000,
        "duration": 30,
        "platform": "youtube_shorts",
    }
    mocker.patch("modules.video_searcher._search_platform", return_value=[good_result])

    results, errors = search_videos("morning routine", max_results=2)

    assert len(results) == 1
    assert results[0]["platform"] == "youtube_shorts"
    assert len(errors) == 0


def test_search_failure_returns_empty_results_and_error(mocker):
    mocker.patch(
        "modules.video_searcher._search_platform",
        side_effect=Exception("network error"),
    )
    results, errors = search_videos("keyword", max_results=4)
    assert results == []
    assert len(errors) == 1
    assert "YouTube Shorts" in errors[0]
