LLM_PROVIDER = "groq"              # "groq", "gemini", "anthropic", or "openai"
GROQ_API_KEY = ""
GEMINI_API_KEY = ""
ANTHROPIC_API_KEY = ""
OPENAI_API_KEY = ""
YOUTUBE_API_KEY = ""
ELEVENLABS_API_KEY = ""            # optional
TTS_PROVIDER = "edge-tts"          # "edge-tts" or "elevenlabs"
CAPTION_REMOVER_PROVIDER = "local" # "local" (NVIDIA GPU) or "replicate"
REPLICATE_API_KEY = ""             # only needed if CAPTION_REMOVER_PROVIDER = "replicate"

TRANSCRIPTAPI_KEY = ""

SCRIPTS_DIR = "data/my_scripts"
SHARED_SCRIPTS_DIR = "data/shared_scripts"
DOWNLOADS_DIR = "downloads"

# Environment variables override the defaults above (used on hosted platforms).
# Locally, keys are stored per-user in keys.json via the ⚙️ Config tab.
import os as _os, sys as _sys
_m = _sys.modules[__name__]
for _k in [
    "LLM_PROVIDER", "GROQ_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY", "YOUTUBE_API_KEY", "ELEVENLABS_API_KEY", "TTS_PROVIDER",
    "CAPTION_REMOVER_PROVIDER", "REPLICATE_API_KEY", "TRANSCRIPTAPI_KEY",
    "SCRIPTS_DIR", "DOWNLOADS_DIR",
]:
    _v = _os.environ.get(_k)
    if _v is not None:
        setattr(_m, _k, _v)
del _os, _sys, _m, _k, _v
