# Long-Form Script Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a multi-step long-form YouTube script generator to the Script Writer tab and a "ciencia todo dia" shared style preset backed by the channel's reference docs.

**Architecture:** A new `modules/longform_generator.py` handles all LLM calls (5 stages, system prompt from docs). The existing `ui/tab_script_writer.py` renders a progressive reveal UI when `platform == "Long Form"`. A new `data/shared_scripts/cienciatododia/` folder with 3 `.txt` files powers the shared preset.

**Tech Stack:** Python, Streamlit session state, existing LLM providers (groq/gemini/anthropic/openai via same pattern as `modules/script_generator.py`), pytest + unittest.mock for tests.

## Global Constraints

- Docs live at `docs/principios_roteirizacao.md`, `docs/avatar_audiencia.md`, `docs/anti_slop.md` — paths relative to project root
- LLM providers and their models: groq → `llama-3.3-70b-versatile`, gemini → `gemini-2.0-flash-lite`, anthropic → `claude-sonnet-4-6`, openai → `gpt-4o-mini`
- `max_tokens=2000` for all long-form LLM calls
- All prompts to the LLM are in Portuguese (matching the original .ts)
- Session state keys for long-form: `lf_step`, `lf_tema`, `lf_system_prompt`, `lf_angulos_raw`, `lf_angulo_escolhido`, `lf_payoffs`, `lf_estrutura`, `lf_hooks_raw`, `lf_hook_escolhido`, `lf_roteiro`
- Do not touch short-form flow — only add a branch when `platform == "Long Form"`
- Shared preset folder name: `cienciatododia` (no spaces, no accent)

---

### Task 1: Create `modules/longform_generator.py` with tests

**Files:**
- Create: `modules/longform_generator.py`
- Create: `tests/test_longform_generator.py`

**Interfaces:**
- Produces:
  - `build_system_prompt() -> str`
  - `extract_option(raw_text: str, chosen_label: str) -> str`
  - `gerar_angulos(tema: str, system_prompt: str, api_key: str, provider: str) -> str`
  - `gerar_payoffs(tema: str, angulo: str, system_prompt: str, api_key: str, provider: str) -> str`
  - `gerar_setups(tema: str, angulo: str, payoffs: str, system_prompt: str, api_key: str, provider: str) -> str`
  - `gerar_hook(tema: str, angulo: str, estrutura: str, system_prompt: str, api_key: str, provider: str) -> str`
  - `gerar_roteiro_completo(tema: str, angulo: str, hook: str, estrutura: str, system_prompt: str, api_key: str, provider: str) -> str`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_longform_generator.py`:

```python
import os
import pytest
from unittest.mock import MagicMock, patch


def test_build_system_prompt_contains_all_docs(tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "principios_roteirizacao.md").write_text("PRINCIPIOS", encoding="utf-8")
    (docs / "avatar_audiencia.md").write_text("AVATAR", encoding="utf-8")
    (docs / "anti_slop.md").write_text("ANTISLOP", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_longform_generator.py -v
```

Expected: ImportError or ModuleNotFoundError — `modules/longform_generator.py` does not exist yet.

- [ ] **Step 3: Create `modules/longform_generator.py`**

```python
import os


def _docs_path(filename: str) -> str:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "docs", filename)


def build_system_prompt() -> str:
    principios = open(_docs_path("principios_roteirizacao.md"), encoding="utf-8").read()
    avatar = open(_docs_path("avatar_audiencia.md"), encoding="utf-8").read()
    anti_slop = open(_docs_path("anti_slop.md"), encoding="utf-8").read()

    return f"""Você é um roteirista especialista em YouTube com foco em retenção.
Siga rigorosamente os documentos abaixo em todas as respostas.

=============================
PRINCÍPIOS DE ROTEIRIZAÇÃO
=============================
{principios}

=============================
AVATAR DA AUDIÊNCIA
=============================
{avatar}

=============================
ANTI-SLOP (proibido usar)
=============================
{anti_slop}""".strip()


def extract_option(raw_text: str, chosen_label: str) -> str:
    lines = raw_text.split("\n")
    start = next(
        (i for i, l in enumerate(lines) if chosen_label.lower() in l.lower()),
        None,
    )
    if start is None:
        return raw_text
    # Find where the next labelled block starts
    label_prefix = chosen_label.split()[0].lower()  # "ângulo" or "hook"
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if label_prefix in lines[i].lower() and lines[i].lower() != chosen_label.lower():
            end = i
            break
    return "\n".join(lines[start:end]).strip()


def _call_llm(user_prompt: str, system_prompt: str, api_key: str, provider: str) -> str:
    if provider == "groq":
        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=2000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content

    if provider == "gemini":
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=user_prompt,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
        )
        return response.text

    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text

    if provider == "openai":
        import openai
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=2000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content

    raise ValueError(f"Unknown provider: {provider}")


def gerar_angulos(tema: str, system_prompt: str, api_key: str, provider: str) -> str:
    prompt = f"""Tema do vídeo: "{tema}"

Sugira 3 ângulos ou estruturas lógicas para o roteiro.
Para cada ângulo, escreva:
- Nome do ângulo
- Fio condutor (como o vídeo vai se desenvolver)
- Payoff filosófico final (a ideia maior que o espectador vai levar)

Numere como Ângulo A, Ângulo B e Ângulo C."""
    return _call_llm(prompt, system_prompt, api_key, provider)


def gerar_payoffs(tema: str, angulo: str, system_prompt: str, api_key: str, provider: str) -> str:
    prompt = f"""Tema do vídeo: "{tema}"
Ângulo escolhido: "{angulo}"

Liste os payoffs (entregas de valor) de cada segmento do vídeo.
Cada payoff deve ser uma frase ou ideia que o espectador não esperava.
Inclua também o payoff final, que deve transcender o tema técnico."""
    return _call_llm(prompt, system_prompt, api_key, provider)


def gerar_setups(tema: str, angulo: str, payoffs: str, system_prompt: str, api_key: str, provider: str) -> str:
    prompt = f"""Tema do vídeo: "{tema}"
Ângulo: "{angulo}"

Payoffs definidos:
{payoffs}

Agora escreva o Setup e a Tensão de cada segmento para conectar os payoffs.
- Setup: contexto mínimo necessário para o espectador entender o que vem
- Tensão: o problema, a contradição, a pergunta sem resposta
- Inclua rehooks entre os segmentos (especialmente antes e depois do bloco do patrocinador)
- Não escreva o roteiro final ainda — apenas a estrutura de cada segmento"""
    return _call_llm(prompt, system_prompt, api_key, provider)


def gerar_hook(tema: str, angulo: str, estrutura: str, system_prompt: str, api_key: str, provider: str) -> str:
    prompt = f"""Tema do vídeo: "{tema}"
Ângulo: "{angulo}"

Estrutura do vídeo:
{estrutura}

Escreva 3 versões do hook (primeiros 30 segundos).
Cada versão deve:
1. Confirmar o clique (mostrar que o vídeo vai entregar o que o título prometeu)
2. Abrir um loop de curiosidade que só fecha lá na frente
3. Subverter a expectativa óbvia do espectador

Numere como Hook A, Hook B e Hook C."""
    return _call_llm(prompt, system_prompt, api_key, provider)


def gerar_roteiro_completo(
    tema: str,
    angulo: str,
    hook: str,
    estrutura: str,
    system_prompt: str,
    api_key: str,
    provider: str,
) -> str:
    prompt = f"""Tema do vídeo: "{tema}"
Ângulo: "{angulo}"

Hook escolhido:
{hook}

Estrutura (setups, tensões e payoffs):
{estrutura}

Agora escreva o roteiro completo em ordem, do hook ao payoff final.
- Use linguagem conversacional e informal
- Aplique todos os princípios de roteirização
- Evite todas as palavras e estruturas do Anti-Slop
- Marque onde deve entrar o bloco do patrocinador com [PATROCINADOR]
- Ao final, escreva o payoff filosófico que o espectador vai levar"""
    return _call_llm(prompt, system_prompt, api_key, provider)
```

- [ ] **Step 4: Run tests to confirm they pass**

```
pytest tests/test_longform_generator.py -v
```

Expected: all 12 tests PASS.

- [ ] **Step 5: Commit**

```
git add modules/longform_generator.py tests/test_longform_generator.py
git commit -m "feat: add longform_generator module with 5-stage script generation"
```

---

### Task 2: Create "ciencia todo dia" shared preset files

**Files:**
- Create: `data/shared_scripts/cienciatododia/principios_roteirizacao.txt`
- Create: `data/shared_scripts/cienciatododia/avatar_audiencia.txt`
- Create: `data/shared_scripts/cienciatododia/anti_slop.txt`

**Interfaces:**
- Consumes: nothing from prior tasks
- Produces: `data/shared_scripts/cienciatododia/` folder readable by `load_shared_scripts()` in `modules/script_generator.py`

- [ ] **Step 1: Copy the docs as .txt files**

Run this Python snippet from the project root:

```python
import os, shutil

src = "docs"
dst = os.path.join("data", "shared_scripts", "cienciatododia")
os.makedirs(dst, exist_ok=True)

files = [
    ("principios_roteirizacao.md", "principios_roteirizacao.txt"),
    ("avatar_audiencia.md", "avatar_audiencia.txt"),
    ("anti_slop.md", "anti_slop.txt"),
]
for src_name, dst_name in files:
    shutil.copy(os.path.join(src, src_name), os.path.join(dst, dst_name))
    print(f"Copied {src_name} → {dst_name}")
```

Or run directly in the terminal:

```
python -c "
import os, shutil
dst = os.path.join('data', 'shared_scripts', 'cienciatododia')
os.makedirs(dst, exist_ok=True)
for s, d in [('principios_roteirizacao.md','principios_roteirizacao.txt'),('avatar_audiencia.md','avatar_audiencia.txt'),('anti_slop.md','anti_slop.txt')]:
    shutil.copy(os.path.join('docs', s), os.path.join(dst, d))
    print(f'OK: {d}')
"
```

- [ ] **Step 2: Verify the files exist**

```
python -c "import os; files = os.listdir(os.path.join('data','shared_scripts','cienciatododia')); print(files); assert len(files) == 3"
```

Expected output: `['anti_slop.txt', 'avatar_audiencia.txt', 'principios_roteirizacao.txt']`

- [ ] **Step 3: Verify the preset appears in the app's shared preset list**

```python
from modules.script_generator import list_shared_presets
import config
presets = list_shared_presets(config.SHARED_SCRIPTS_DIR)
assert "cienciatododia" in presets, f"Got: {presets}"
print("OK:", presets)
```

Run with: `python -c "<above code>"`

- [ ] **Step 4: Commit**

```
git add data/shared_scripts/cienciatododia/
git commit -m "feat: add cienciatododia shared style preset from docs"
```

---

### Task 3: Add long-form progressive reveal UI to Script Writer tab

**Files:**
- Modify: `ui/tab_script_writer.py`

**Interfaces:**
- Consumes from Task 1:
  - `build_system_prompt() -> str`
  - `extract_option(raw_text: str, chosen_label: str) -> str`
  - `gerar_angulos(tema, system_prompt, api_key, provider) -> str`
  - `gerar_payoffs(tema, angulo, system_prompt, api_key, provider) -> str`
  - `gerar_setups(tema, angulo, payoffs, system_prompt, api_key, provider) -> str`
  - `gerar_hook(tema, angulo, estrutura, system_prompt, api_key, provider) -> str`
  - `gerar_roteiro_completo(tema, angulo, hook, estrutura, system_prompt, api_key, provider) -> str`
- Consumes from existing code:
  - `get_key(name: str) -> str` from `ui/user_cfg.py`
  - `config.LLM_PROVIDER`

- [ ] **Step 1: Add the import at the top of `ui/tab_script_writer.py`**

After the existing imports block (after `from ui.user_cfg import get_key, get_scripts_dir`), add:

```python
from modules.longform_generator import (
    build_system_prompt,
    extract_option,
    gerar_angulos,
    gerar_hook,
    gerar_payoffs,
    gerar_roteiro_completo,
    gerar_setups,
)
```

- [ ] **Step 2: Add the `_render_longform` helper function**

Add this function before `render_script_writer()`:

```python
def _get_api_key_and_provider():
    provider = get_key("LLM_PROVIDER") or config.LLM_PROVIDER
    key_map = {
        "groq": get_key("GROQ_API_KEY"),
        "gemini": get_key("GEMINI_API_KEY"),
        "anthropic": get_key("ANTHROPIC_API_KEY"),
        "openai": get_key("OPENAI_API_KEY"),
    }
    return key_map.get(provider, ""), provider


def _lf_reset():
    for key in ["lf_step", "lf_tema", "lf_system_prompt", "lf_angulos_raw",
                "lf_angulo_escolhido", "lf_payoffs", "lf_estrutura",
                "lf_hooks_raw", "lf_hook_escolhido", "lf_roteiro"]:
        st.session_state.pop(key, None)


def _render_longform(topic: str):
    step = st.session_state.get("lf_step", 0)
    api_key, provider = _get_api_key_and_provider()

    if not api_key:
        st.error(t("sw_no_api_key", provider=provider.upper()))
        return

    # ── Step 0: start ──────────────────────────────────────────────────
    if step == 0:
        if st.button("Gerar Ângulos", type="primary", use_container_width=True):
            if not topic.strip():
                st.error(t("sw_enter_name"))
                return
            with st.spinner("Gerando ângulos..."):
                try:
                    sys_prompt = build_system_prompt()
                    angulos = gerar_angulos(topic, sys_prompt, api_key, provider)
                    st.session_state["lf_step"] = 1
                    st.session_state["lf_tema"] = topic
                    st.session_state["lf_system_prompt"] = sys_prompt
                    st.session_state["lf_angulos_raw"] = angulos
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao gerar ângulos: {e}")
        return

    tema = st.session_state["lf_tema"]
    sys_prompt = st.session_state["lf_system_prompt"]

    # ── Step 1: choose angle ────────────────────────────────────────────
    if step >= 1:
        with st.expander("📐 Ângulos sugeridos", expanded=(step == 1)):
            st.text_area("", value=st.session_state["lf_angulos_raw"], height=300,
                         disabled=True, key="lf_angulos_display", label_visibility="collapsed")
            if step == 1:
                escolha = st.radio("Qual ângulo você escolhe?", ["Ângulo A", "Ângulo B", "Ângulo C"],
                                   horizontal=True, key="lf_radio_angulo")
                if st.button("Continuar com este ângulo", type="primary"):
                    angulo_texto = extract_option(st.session_state["lf_angulos_raw"], escolha)
                    with st.spinner("Gerando payoffs..."):
                        try:
                            payoffs = gerar_payoffs(tema, angulo_texto, sys_prompt, api_key, provider)
                            st.session_state["lf_angulo_escolhido"] = angulo_texto
                            st.session_state["lf_payoffs"] = payoffs
                            st.session_state["lf_step"] = 2
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao gerar payoffs: {e}")

    # ── Step 2: confirm payoffs ─────────────────────────────────────────
    if step >= 2:
        angulo = st.session_state["lf_angulo_escolhido"]
        with st.expander("🎯 Payoffs", expanded=(step == 2)):
            st.text_area("", value=st.session_state["lf_payoffs"], height=250,
                         disabled=True, key="lf_payoffs_display", label_visibility="collapsed")
            if step == 2:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Continuar", type="primary", use_container_width=True):
                        with st.spinner("Gerando estrutura..."):
                            try:
                                estrutura = gerar_setups(tema, angulo, st.session_state["lf_payoffs"],
                                                         sys_prompt, api_key, provider)
                                st.session_state["lf_estrutura"] = estrutura
                                st.session_state["lf_step"] = 3
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao gerar estrutura: {e}")
                with col2:
                    if st.button("Gerar novamente", use_container_width=True):
                        with st.spinner("Regerando payoffs..."):
                            try:
                                payoffs = gerar_payoffs(tema, angulo, sys_prompt, api_key, provider)
                                st.session_state["lf_payoffs"] = payoffs
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao regerar payoffs: {e}")

    # ── Step 3: structure (auto) ────────────────────────────────────────
    if step >= 3:
        with st.expander("🏗️ Estrutura (setups e tensões)", expanded=(step == 3)):
            st.text_area("", value=st.session_state["lf_estrutura"], height=300,
                         disabled=True, key="lf_estrutura_display", label_visibility="collapsed")
            if step == 3:
                if st.button("Gerar Hooks", type="primary"):
                    with st.spinner("Gerando hooks..."):
                        try:
                            hooks = gerar_hook(tema, st.session_state["lf_angulo_escolhido"],
                                               st.session_state["lf_estrutura"], sys_prompt, api_key, provider)
                            st.session_state["lf_hooks_raw"] = hooks
                            st.session_state["lf_step"] = 4
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao gerar hooks: {e}")

    # ── Step 4: choose hook ─────────────────────────────────────────────
    if step >= 4:
        with st.expander("🪝 Hooks sugeridos", expanded=(step == 4)):
            st.text_area("", value=st.session_state["lf_hooks_raw"], height=300,
                         disabled=True, key="lf_hooks_display", label_visibility="collapsed")
            if step == 4:
                escolha_hook = st.radio("Qual hook você escolhe?", ["Hook A", "Hook B", "Hook C"],
                                        horizontal=True, key="lf_radio_hook")
                if st.button("Gerar Roteiro Completo", type="primary"):
                    hook_texto = extract_option(st.session_state["lf_hooks_raw"], escolha_hook)
                    with st.spinner("Escrevendo o roteiro completo..."):
                        try:
                            roteiro = gerar_roteiro_completo(
                                tema,
                                st.session_state["lf_angulo_escolhido"],
                                hook_texto,
                                st.session_state["lf_estrutura"],
                                sys_prompt,
                                api_key,
                                provider,
                            )
                            st.session_state["lf_hook_escolhido"] = hook_texto
                            st.session_state["lf_roteiro"] = roteiro
                            st.session_state["lf_step"] = 5
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao gerar roteiro: {e}")

    # ── Step 5: complete script ─────────────────────────────────────────
    if step >= 5:
        st.markdown("### 📄 Roteiro Completo")
        roteiro = st.text_area("", value=st.session_state["lf_roteiro"], height=500,
                               key="lf_roteiro_display", label_visibility="collapsed")
        st.download_button(
            "⬇️ Baixar roteiro (.txt)",
            data=st.session_state["lf_roteiro"],
            file_name=f"roteiro_{tema[:30].replace(' ', '_')}.txt",
            mime="text/plain",
        )
        if st.button("🔄 Começar de novo"):
            _lf_reset()
            st.rerun()
```

- [ ] **Step 3: Wire `_render_longform` into `render_script_writer`**

Inside `render_script_writer`, in the `with left_col:` block, find the section where the generate button and script output are rendered. It currently looks like:

```python
        if st.button(t("sw_generate_btn"), type="primary", use_container_width=True):
```

Replace everything from that button down to the end of the `with left_col:` block (including the `if "generated_script" in st.session_state:` block and the voiceover section) with this conditional:

```python
        if platform == "Long Form":
            _render_longform(topic)
        else:
            if st.button(t("sw_generate_btn"), type="primary", use_container_width=True):
                if not topic.strip():
                    st.error(t("sw_enter_name"))
                else:
                    llm_provider = get_key("LLM_PROVIDER") or config.LLM_PROVIDER
                    key_map = {
                        "groq": get_key("GROQ_API_KEY"),
                        "gemini": get_key("GEMINI_API_KEY"),
                        "anthropic": get_key("ANTHROPIC_API_KEY"),
                        "openai": get_key("OPENAI_API_KEY"),
                    }
                    api_key = key_map.get(llm_provider, "")
                    if not api_key:
                        st.error(t("sw_no_api_key", provider=llm_provider.upper()))
                    else:
                        with st.spinner(t("sw_crafting")):
                            try:
                                if style_preset.startswith(_SHARED_PREFIX):
                                    user_scripts = load_shared_scripts(shared_dir, style_preset[len(_SHARED_PREFIX):])
                                else:
                                    user_scripts = load_user_scripts(scripts_dir, style_preset)
                                script = generate_script(topic, platform, language, user_scripts, api_key, llm_provider)
                                st.session_state["generated_script"] = script
                                st.session_state["script_output"] = script
                            except Exception as e:
                                msg = str(e)
                                if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
                                    st.error(t("sw_quota_error"))
                                elif "401" in msg or "API_KEY" in msg or "invalid" in msg.lower():
                                    st.error(t("sw_key_error"))
                                else:
                                    st.error(t("sw_gen_error", error=e))

            if "generated_script" in st.session_state:
                st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)
                st.markdown(f"""
                <p style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em;
                           color: #7c3aed; font-weight: 600; margin-bottom: 4px;">
                    {t('sw_generated_label')}
                </p>
                """, unsafe_allow_html=True)
                st.text_area(
                    label="",
                    value=st.session_state["generated_script"],
                    height=320,
                    key="script_output",
                )
                st.download_button(
                    t("sw_download_txt"),
                    data=st.session_state["generated_script"],
                    file_name="script.txt",
                    mime="text/plain",
                )

                st.divider()

                st.markdown(f"""
                <p style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em;
                           color: #0ea5e9; font-weight: 600; margin-bottom: 4px;">
                    {t('sw_voiceover_label')}
                </p>
                """, unsafe_allow_html=True)

                voc_tab, notes_tab = st.tabs([t("sw_voc_tab_generate"), t("sw_voc_tab_notes")])

                with notes_tab:
                    st.caption(t("sw_notes_caption"))
                    st.radio(t("sw_voice"), ["Female", "Male"], horizontal=True, key="vo_gender")
                    st.select_slider(t("sw_pace"), options=_PACE_OPTIONS, value="Normal", key="vo_pace")
                    st.select_slider(t("sw_pitch"), options=_PITCH_OPTIONS, value="Normal", key="vo_pitch")
                    st.text_area(
                        t("sw_style_notes_label"),
                        placeholder=t("sw_style_notes_placeholder"),
                        key="vo_notes",
                        height=80,
                    )

                with voc_tab:
                    pace   = st.session_state.get("vo_pace", "Normal")
                    pitch  = st.session_state.get("vo_pitch", "Normal")
                    gender = st.session_state.get("vo_gender", "Female")
                    st.caption(t("sw_voc_settings_caption", gender=gender, pace=pace, pitch=pitch))
                    if st.button(t("sw_generate_voc_btn")):
                        tts_provider = get_key("TTS_PROVIDER") or config.TTS_PROVIDER
                        elevenlabs_key = get_key("ELEVENLABS_API_KEY")
                        if tts_provider == "elevenlabs" and not elevenlabs_key:
                            st.error(t("sw_elevenlabs_missing"))
                        else:
                            audio_path = os.path.join(config.DOWNLOADS_DIR, "voiceover.mp3")
                            with st.spinner(t("sw_generating_voc")):
                                generate_voiceover(
                                    st.session_state["generated_script"],
                                    audio_path,
                                    tts_provider,
                                    elevenlabs_key,
                                    rate=_PACE_TO_RATE[pace],
                                    pitch=_PITCH_TO_HZ[pitch],
                                    gender=gender,
                                )
                            st.audio(audio_path, format="audio/mp3")
                            with open(audio_path, "rb") as f:
                                st.download_button(t("sw_download_voc"), data=f, file_name="voiceover.mp3", mime="audio/mpeg")
```

Also, hide the style preset selector when `platform == "Long Form"`. Find this block:

```python
        user_presets = [p for p in list_presets(scripts_dir) if p != "Default"]
        shared_labels = [_SHARED_PREFIX + p for p in list_shared_presets(shared_dir)]
        all_presets = shared_labels + user_presets  # shared first so juanminiboi is the default
        saved_preset = get_key("SCRIPT_PRESET") or ""
        preset_idx = all_presets.index(saved_preset) if saved_preset in all_presets else 0
        style_preset = st.selectbox(
            t("sw_style_preset"),
            all_presets,
            index=preset_idx,
            key="gen_style_preset",
            help=t("sw_preset_help"),
        )
```

Wrap it in a condition so it only renders for short-form:

```python
        user_presets = [p for p in list_presets(scripts_dir) if p != "Default"]
        shared_labels = [_SHARED_PREFIX + p for p in list_shared_presets(shared_dir)]
        all_presets = shared_labels + user_presets  # shared first so juanminiboi is the default
        saved_preset = get_key("SCRIPT_PRESET") or ""
        preset_idx = all_presets.index(saved_preset) if saved_preset in all_presets else 0
        if platform != "Long Form":
            style_preset = st.selectbox(
                t("sw_style_preset"),
                all_presets,
                index=preset_idx,
                key="gen_style_preset",
                help=t("sw_preset_help"),
            )
        else:
            style_preset = ""
```

- [ ] **Step 4: Verify the app starts without errors**

```
streamlit run app.py
```

Expected: app starts, Script Writer tab opens, platform selector shows "YouTube Shorts" and "Long Form". Switching to "Long Form" hides the style preset and shows the "Gerar Ângulos" button. No Python errors in the terminal.

- [ ] **Step 5: Manual test — full long-form flow**

1. Select "Long Form" platform
2. Enter a topic (e.g. "por que buracos negros não sugam tudo ao redor")
3. Click "Gerar Ângulos" — wait for spinner — 3 angles appear in expander
4. Select "Ângulo B" via radio — click "Continuar com este ângulo"
5. Payoffs appear — click "Gerar novamente" — new payoffs appear (same angle)
6. Click "Continuar" — structure appears
7. Click "Gerar Hooks" — 3 hooks appear
8. Select "Hook A" — click "Gerar Roteiro Completo"
9. Full script appears in editable text area — download button works
10. Click "Começar de novo" — resets to step 0, topic field is empty

Also test: switch to "YouTube Shorts" — short-form flow works exactly as before (style preset shows, generate button works).

- [ ] **Step 6: Commit**

```
git add ui/tab_script_writer.py
git commit -m "feat: add long-form progressive reveal UI to Script Writer tab"
```
