import os
import pytest
from unittest.mock import MagicMock, patch


def test_build_system_prompt_contains_all_docs(tmp_path, mocker):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "principios_roteirizacao.md").write_text("PRINCIPIOS", encoding="utf-8")
    (docs / "avatar_audiencia.md").write_text("AVATAR", encoding="utf-8")
    (docs / "anti_slop.md").write_text("ANTISLOP", encoding="utf-8")

    mocker.patch("modules.longform_generator._docs_path", side_effect=lambda f: str(docs / f))
    from modules.longform_generator import build_system_prompt
    result = build_system_prompt()
    assert "PRINCIPIOS" in result
    assert "AVATAR" in result
    assert "ANTISLOP" in result


def test_extract_option_returns_correct_block():
    from modules.longform_generator import extract_option
    raw = "Ângulo A\nsome text\nmore text\nÂngulo B\nother text\nÂngulo C\nlast text"
    result = extract_option(raw, "Ângulo A")
    assert "some text" in result
    assert "other text" not in result


def test_extract_option_last_block():
    from modules.longform_generator import extract_option
    raw = "Hook A\nfirst\nHook B\nsecond\nHook C\nthird"
    result = extract_option(raw, "Hook C")
    assert "third" in result
    assert "first" not in result


def test_extract_option_fallback_returns_raw():
    from modules.longform_generator import extract_option
    raw = "no labels here at all"
    result = extract_option(raw, "Ângulo A")
    assert result == raw


def test_gerar_angulos_calls_llm_and_returns_string(mocker):
    mocker.patch("modules.longform_generator._call_llm", return_value="Ângulo A\ntest")
    from modules.longform_generator import gerar_angulos
    result = gerar_angulos("buracos negros", "sys", "key", "groq")
    assert isinstance(result, str)
    assert len(result) > 0


def test_gerar_payoffs_passes_context(mocker):
    mock = mocker.patch("modules.longform_generator._call_llm", return_value="payoffs here")
    from modules.longform_generator import gerar_payoffs
    gerar_payoffs("buracos negros", "Ângulo A\nfio condutor", "sys", "key", "groq")
    call_args = mock.call_args[0]
    assert "buracos negros" in call_args[0]
    assert "Ângulo A" in call_args[0]


def test_gerar_setups_passes_context(mocker):
    mock = mocker.patch("modules.longform_generator._call_llm", return_value="setups here")
    from modules.longform_generator import gerar_setups
    gerar_setups("tema", "angulo", "payoffs", "sys", "key", "groq")
    call_args = mock.call_args[0]
    assert "payoffs" in call_args[0]


def test_gerar_hook_passes_context(mocker):
    mock = mocker.patch("modules.longform_generator._call_llm", return_value="Hook A\nhook text")
    from modules.longform_generator import gerar_hook
    gerar_hook("tema", "angulo", "estrutura", "sys", "key", "groq")
    call_args = mock.call_args[0]
    assert "estrutura" in call_args[0]


def test_gerar_roteiro_completo_passes_all_context(mocker):
    mock = mocker.patch("modules.longform_generator._call_llm", return_value="roteiro completo")
    from modules.longform_generator import gerar_roteiro_completo
    gerar_roteiro_completo("tema", "angulo", "hook", "estrutura", "sys", "key", "groq")
    call_args = mock.call_args[0]
    assert "hook" in call_args[0]
    assert "estrutura" in call_args[0]


def test_call_llm_groq(mocker):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value.choices[0].message.content = "groq response"
    mocker.patch("groq.Groq", return_value=mock_client)
    from modules.longform_generator import _call_llm
    result = _call_llm("user prompt", "system prompt", "fake-key", "groq")
    assert result == "groq response"
    mock_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_client.chat.completions.create.call_args[1]
    messages = call_kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "system prompt"
    assert messages[1]["role"] == "user"


def test_call_llm_unknown_provider():
    from modules.longform_generator import _call_llm
    with pytest.raises(ValueError, match="Unknown provider"):
        _call_llm("prompt", "sys", "key", "unknown_provider")
