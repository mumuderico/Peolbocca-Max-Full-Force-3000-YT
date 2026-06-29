import json
import os

_KEYS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "keys.json"))

PROFILE_FIELDS = [
    "LLM_PROVIDER", "GROQ_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY", "YOUTUBE_API_KEY", "ELEVENLABS_API_KEY", "TTS_PROVIDER",
    "CAPTION_REMOVER_PROVIDER", "REPLICATE_API_KEY", "TRANSCRIPTAPI_KEY",
    "SCRIPT_PRESET",
]


def _load_data() -> dict:
    if not os.path.exists(_KEYS_PATH):
        return {"profiles": {}}
    try:
        raw = json.loads(open(_KEYS_PATH, encoding="utf-8").read())
    except Exception:
        return {"profiles": {}}
    if "profiles" not in raw:
        # migrate old flat format → single "Default" profile
        return {"profiles": {"Default": {k: raw[k] for k in PROFILE_FIELDS if k in raw}}}
    return raw


def list_profiles() -> list[str]:
    return list(_load_data().get("profiles", {}).keys())


def load_profile(name: str) -> dict:
    return _load_data().get("profiles", {}).get(name, {})


def save_profile(name: str, keys: dict) -> None:
    data = _load_data()
    data["profiles"][name] = keys
    with open(_KEYS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
