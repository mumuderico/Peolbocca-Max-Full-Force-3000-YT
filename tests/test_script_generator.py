import os
import pytest
from unittest.mock import MagicMock, AsyncMock
from modules.script_generator import (
    list_scripts,
    save_script,
    delete_script,
    load_user_scripts,
    generate_script,
    generate_voiceover,
)


def test_save_creates_file_and_list_returns_it(tmp_path):
    scripts_dir = str(tmp_path / "scripts")
    save_script("my_script.txt", "Hello creator", scripts_dir)
    assert "my_script.txt" in list_scripts(scripts_dir)


def test_list_scripts_empty_dir_returns_empty(tmp_path):
    scripts_dir = str(tmp_path / "empty")
    os.makedirs(scripts_dir)
    assert list_scripts(scripts_dir) == []


def test_delete_script_removes_file(tmp_path):
    scripts_dir = str(tmp_path / "scripts")
    save_script("remove_me.txt", "content", scripts_dir)
    delete_script("remove_me.txt", scripts_dir)
    assert "remove_me.txt" not in list_scripts(scripts_dir)


def test_load_user_scripts_returns_contents(tmp_path):
    scripts_dir = str(tmp_path / "scripts")
    save_script("a.txt", "Script A content", scripts_dir)
    save_script("b.txt", "Script B content", scripts_dir)
    contents = load_user_scripts(scripts_dir)
    assert len(contents) == 2
    assert "Script A content" in contents
    assert "Script B content" in contents


def test_load_user_scripts_empty_dir_returns_empty(tmp_path):
    scripts_dir = str(tmp_path / "empty")
    os.makedirs(scripts_dir)
    assert load_user_scripts(scripts_dir) == []


def test_generate_script_anthropic(mocker):
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="TikTok script about money")]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message
    mocker.patch("anthropic.Anthropic", return_value=mock_client)

    result = generate_script(
        topic="5 ways to save money",
        platform="TikTok",
        language="English",
        user_scripts=["Example script showing my style"],
        api_key="test-key",
        provider="anthropic",
    )

    assert result == "TikTok script about money"
    mock_client.messages.create.assert_called_once()
    call_kwargs = mock_client.messages.create.call_args[1]
    assert call_kwargs["model"] == "claude-sonnet-4-6"
    assert "5 ways to save money" in call_kwargs["messages"][0]["content"]
    assert "TikTok" in call_kwargs["messages"][0]["content"]


def test_generate_script_openai(mocker):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="OpenAI script"))]
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    mocker.patch("openai.OpenAI", return_value=mock_client)

    result = generate_script(
        topic="travel tips",
        platform="Instagram Reels",
        language="English",
        user_scripts=[],
        api_key="test-key",
        provider="openai",
    )

    assert result == "OpenAI script"


def test_generate_script_unknown_provider_raises():
    with pytest.raises(ValueError, match="Unknown provider"):
        generate_script("topic", "TikTok", "English", [], "key", "unknown")


def test_generate_voiceover_edge_tts(tmp_path, mocker):
    output_path = str(tmp_path / "output.mp3")

    async def fake_edge_tts(text, path, voice):
        with open(path, "wb") as f:
            f.write(b"fake audio data")

    mocker.patch(
        "modules.script_generator._edge_tts_generate", side_effect=fake_edge_tts
    )

    result = generate_voiceover("Hello world", output_path, provider="edge-tts")
    assert result == output_path
    assert os.path.exists(output_path)
