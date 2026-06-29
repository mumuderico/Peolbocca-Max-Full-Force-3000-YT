# Long-Form Script Generator — Design Spec
**Date:** 2026-06-29
**Status:** Approved

---

## Overview

Integrate a multi-step long-form YouTube script generator into the existing Script Writer tab, and add a "ciencia todo dia" shared style preset backed by the channel's reference docs. The long-form flow is a 5-stage progressive reveal: the user picks an angle and a hook at two decision points, and all other stages generate automatically. Uses whichever LLM provider the user has configured (same as the short-form generator).

---

## Architecture

### New files
- `modules/longform_generator.py` — pure generation logic, no Streamlit imports. Contains `build_system_prompt()` and one async-style function per stage.

### Modified files
- `ui/tab_script_writer.py` — when `platform == "Long Form"`, renders the progressive reveal flow instead of the one-shot generate button
- `data/shared_scripts/cienciatododia/` — new shared preset folder with 3 `.txt` files (copies of the docs)

### No changes to
- `config.py`, `modules/script_generator.py`, `app.py` — no new API keys, tabs, or provider logic needed

---

## Module: `modules/longform_generator.py`

### `build_system_prompt() -> str`

Reads the three reference docs at runtime and returns a single system prompt string:

```
docs/principios_roteirizacao.md
docs/avatar_audiencia.md
docs/anti_slop.md
```

The prompt instructs the LLM to act as a YouTube scriptwriter focused on retention, following the docs strictly.

### Stage functions

Each function takes the accumulated context and calls the LLM via the existing provider abstraction (same call pattern as `generate_script` in `script_generator.py`):

```python
def gerar_angulos(tema: str, system_prompt: str, api_key: str, provider: str) -> str
def gerar_payoffs(tema: str, angulo: str, system_prompt: str, api_key: str, provider: str) -> str
def gerar_setups(tema: str, angulo: str, payoffs: str, system_prompt: str, api_key: str, provider: str) -> str
def gerar_hook(tema: str, angulo: str, estrutura: str, system_prompt: str, api_key: str, provider: str) -> str
def gerar_roteiro_completo(tema: str, angulo: str, hook: str, estrutura: str, system_prompt: str, api_key: str, provider: str) -> str
```

Each function returns the raw LLM response as a string. No parsing — the raw text is displayed directly in the UI and passed as context to the next stage.

`max_tokens`: 2000 per call (same as the original .ts).

### Error handling
Raises `Exception` with a descriptive message on API errors. The UI catches and displays it with `st.error`.

---

## UI Flow: Progressive Reveal

Triggered when `platform == "Long Form"` in `tab_script_writer.py`. The short-form flow is completely unchanged when `platform == "YouTube Shorts"`.

### Session state keys

| Key | Type | Description |
|---|---|---|
| `lf_step` | int | Current stage (0–5). 0 = not started |
| `lf_tema` | str | Video topic entered by user |
| `lf_angulos_raw` | str | Raw LLM output from stage 1 |
| `lf_angulo_escolhido` | str | Selected angle text |
| `lf_payoffs` | str | Raw LLM output from stage 2 |
| `lf_estrutura` | str | Raw LLM output from stage 3 |
| `lf_hooks_raw` | str | Raw LLM output from stage 4 |
| `lf_hook_escolhido` | str | Selected hook text |
| `lf_roteiro` | str | Raw LLM output from stage 5 |

### Stage progression

**Step 0 — Initial state**
- Topic input (same `st.text_input` already in the tab)
- Button: "Gerar Ângulos" → runs `gerar_angulos()`, sets `lf_step = 1`

**Step 1 — Angle selection**
- Shows `lf_angulos_raw` in a `st.text_area` (read-only)
- `st.radio` with options: "Ângulo A", "Ângulo B", "Ângulo C"
- Button: "Continuar com este ângulo" → extracts chosen angle text from raw output, runs `gerar_payoffs()`, sets `lf_step = 2`

**Step 2 — Payoff confirmation**
- Shows `lf_payoffs` in a `st.text_area` (read-only)
- Two buttons: "Continuar" → runs `gerar_setups()` and sets `lf_step = 3` | "Gerar novamente" → re-runs `gerar_payoffs()` with same angle
- Stage 3 (setups) runs automatically on "Continuar" — no extra user interaction

**Step 3 — Structure (auto)**
- Shows `lf_estrutura` in a `st.text_area` (read-only)
- Button: "Gerar Hooks" → runs `gerar_hook()`, sets `lf_step = 4`

**Step 4 — Hook selection**
- Shows `lf_hooks_raw` in a `st.text_area` (read-only)
- `st.radio` with options: "Hook A", "Hook B", "Hook C"
- Button: "Gerar Roteiro Completo" → extracts chosen hook, runs `gerar_roteiro_completo()`, sets `lf_step = 5`

**Step 5 — Complete script**
- Shows `lf_roteiro` in an editable `st.text_area`
- `st.download_button` → downloads as `roteiro.txt`
- Button: "Começar de novo" → clears all `lf_*` session state keys, resets `lf_step = 0`

All previous steps remain visible above the current step (standard Streamlit top-to-bottom render). Each completed step is shown in a collapsed `st.expander` to save vertical space.

---

## Shared Preset: "ciencia todo dia"

### Folder structure
```
data/shared_scripts/cienciatododia/
├── principios_roteirizacao.txt   ← copy of docs/principios_roteirizacao.md
├── avatar_audiencia.txt          ← copy of docs/avatar_audiencia.md
└── anti_slop.txt                 ← copy of docs/anti_slop.md
```

### Behavior
- Appears in the style preset dropdown as **🌐 ciencia todo dia**
- **Short-form (YouTube Shorts):** the 3 `.txt` files are loaded as style examples and passed to the LLM alongside the generation prompt — the LLM infers tone, audience, and rules from the docs
- **Long-form:** the preset selection has no effect on the system prompt (the docs are already loaded directly from `docs/` by `build_system_prompt()`); the style preset dropdown is not rendered when `platform == "Long Form"` — it is irrelevant to that mode

No special-case detection code is needed — the preset enters the same shared preset loading path as juanminiboi.

---

## Data Flow Summary

```
User enters topic
        ↓
gerar_angulos(tema) → LLM → shows 3 angles → user picks one
        ↓
gerar_payoffs(tema, angulo) → LLM → shows payoffs → user confirms
        ↓
gerar_setups(tema, angulo, payoffs) → LLM → shows structure (auto)
        ↓
gerar_hook(tema, angulo, estrutura) → LLM → shows 3 hooks → user picks one
        ↓
gerar_roteiro_completo(tema, angulo, hook, estrutura) → LLM → full script
        ↓
Download as .txt
```

System prompt (docs) is built once at the start of the flow and passed to every stage.

---

## Error Handling

- API errors at any stage: `st.error` with the exception message; the current step stays visible so the user can retry
- Missing API key: same check as short-form — `st.error` before any LLM call
- The "Gerar novamente" button on Step 2 covers the case where payoffs are unsatisfactory

---

## Out of Scope

- Saving generated long-form scripts to the style library (user can copy manually)
- Per-stage regeneration beyond Step 2 (not in original design)
- Voiceover generation for long-form scripts
