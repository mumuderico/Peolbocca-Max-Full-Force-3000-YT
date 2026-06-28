import pytest
from unittest.mock import MagicMock
from modules.channel_ranker import fetch_trending_channels


def _make_video_item(channel_id: str, view_count: str) -> dict:
    return {
        "snippet": {"channelId": channel_id},
        "statistics": {"viewCount": view_count},
    }


def _make_channel_item(channel_id: str, title: str, subscribers: str) -> dict:
    return {
        "id": channel_id,
        "snippet": {
            "title": title,
            "thumbnails": {"default": {"url": f"https://example.com/{channel_id}.jpg"}},
        },
        "statistics": {"subscriberCount": subscribers},
    }


@pytest.fixture
def mock_youtube(mocker):
    mock = MagicMock()
    mocker.patch("modules.channel_ranker.build", return_value=mock)
    return mock


def test_fetch_trending_channels_returns_expected_keys(mock_youtube):
    mock_youtube.videos.return_value.list.return_value.execute.return_value = {
        "items": [_make_video_item("UC123", "1000000")],
    }
    mock_youtube.channels.return_value.list.return_value.execute.return_value = {
        "items": [_make_channel_item("UC123", "TestChannel", "500000")],
    }

    results = fetch_trending_channels("US", "fake_key")

    assert len(results) == 1
    for key in ("channel_id", "name", "thumbnail", "subscribers", "trending_count", "trending_views"):
        assert key in results[0], f"Missing key: {key}"


def test_channels_aggregated_correctly(mock_youtube):
    mock_youtube.videos.return_value.list.return_value.execute.return_value = {
        "items": [
            _make_video_item("UC123", "1000000"),
            _make_video_item("UC123", "2000000"),
        ],
    }
    mock_youtube.channels.return_value.list.return_value.execute.return_value = {
        "items": [_make_channel_item("UC123", "TestChannel", "500000")],
    }

    results = fetch_trending_channels("US", "fake_key")

    assert len(results) == 1
    assert results[0]["trending_count"] == 2
    assert results[0]["trending_views"] == 3_000_000


def test_fetch_raises_on_api_error(mock_youtube):
    mock_youtube.videos.return_value.list.return_value.execute.side_effect = Exception("403 Quota exceeded")

    with pytest.raises(Exception):
        fetch_trending_channels("US", "fake_key")
