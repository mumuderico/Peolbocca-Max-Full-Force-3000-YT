import asyncio
import os
import threading
import streamlit as st


PLATFORM_INSTRUCTIONS = {
    "YouTube Shorts": "short and punchy, hook in the first line, 150–250 words, no hashtags",
    "Long Form": "in-depth and structured, strong intro and clear sections, 500–900 words",
}


def _preset_dir(scripts_dir: str, preset: str) -> str:
    return scripts_dir if preset == "Default" else os.path.join(scripts_dir, preset)


def list_presets(scripts_dir: str) -> list[str]:
    presets = ["Default"]
    if os.path.exists(scripts_dir):
        presets += sorted(
            n for n in os.listdir(scripts_dir)
            if os.path.isdir(os.path.join(scripts_dir, n))
        )
    return presets


def _profile_id() -> str:
    return st.session_state.get("active_profile", "")


def _sync(fn, *args):
    threading.Thread(target=fn, args=args, daemon=True).start()


def create_preset(name: str, scripts_dir: str) -> None:
    os.makedirs(os.path.join(scripts_dir, name), exist_ok=True)
    from modules.cloud_store import create_preset_in_cloud
    _sync(create_preset_in_cloud, _profile_id(), name)


def delete_preset(name: str, scripts_dir: str) -> None:
    import shutil
    path = os.path.join(scripts_dir, name)
    if os.path.exists(path):
        shutil.rmtree(path)
    from modules.cloud_store import delete_preset_from_cloud
    _sync(delete_preset_from_cloud, _profile_id(), name)


def list_scripts(scripts_dir: str, preset: str = "Default") -> list[str]:
    target = _preset_dir(scripts_dir, preset)
    if not os.path.exists(target):
        return []
    return sorted(
        f for f in os.listdir(target)
        if f.endswith(".txt") and os.path.isfile(os.path.join(target, f))
    )


def save_script(filename: str, content: str, scripts_dir: str, preset: str = "Default") -> None:
    target = _preset_dir(scripts_dir, preset)
    os.makedirs(target, exist_ok=True)
    with open(os.path.join(target, filename), "w", encoding="utf-8") as f:
        f.write(content)
    from modules.cloud_store import save_script_to_cloud
    _sync(save_script_to_cloud, _profile_id(), preset, filename, content)


def delete_script(filename: str, scripts_dir: str, preset: str = "Default") -> None:
    path = os.path.join(_preset_dir(scripts_dir, preset), filename)
    if os.path.exists(path):
        os.remove(path)
    from modules.cloud_store import delete_script_from_cloud
    _sync(delete_script_from_cloud, _profile_id(), preset, filename)


def load_user_scripts(scripts_dir: str, preset: str = "Default") -> list[str]:
    target = _preset_dir(scripts_dir, preset)
    contents = []
    for filename in list_scripts(scripts_dir, preset):
        with open(os.path.join(target, filename), "r", encoding="utf-8") as f:
            contents.append(f.read())
    return contents


def generate_script(
    topic: str,
    platform: str,
    language: str,
    user_scripts: list[str],
    api_key: str,
    provider: str,
) -> str:
    MAX_EXAMPLE_CHARS = 3000
    combined = "\n\n---\n\n".join(user_scripts) if user_scripts else ""
    if combined:
        style_examples = combined[:MAX_EXAMPLE_CHARS]
        if len(combined) > MAX_EXAMPLE_CHARS:
            style_examples += "\n[...examples trimmed to fit...]"
    else:
        style_examples = "No examples provided — use a generic engaging style."
    platform_guide = PLATFORM_INSTRUCTIONS.get(platform, "engaging and concise")

    prompt = (
        f"You are a social media content creator. Generate a script for a {platform} video "
        f"about \"{topic}\".\n\n"
        f"CRITICAL: The script MUST be written entirely in {language}. "
        f"The style examples below may be in a different language — ignore their language and use them ONLY "
        f"to learn the creator's tone, vocabulary style, and structure. Your output must be 100% in {language}.\n\n"
        f"Format: {platform_guide}.\n\n"
        f"Style examples (reference only — do NOT copy language, only style):\n\n"
        f"---\n{style_examples}\n---\n\n"
        f"Write only the script text in {language}. No introductions, no meta-commentary."
    )

    if provider == "groq":
        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    if provider == "gemini":
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt,
        )
        return response.text

    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    if provider == "openai":
        import openai
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    raise ValueError(f"Unknown provider: {provider}")


async def _edge_tts_generate(text: str, output_path: str, voice: str, rate: str = "+0%", pitch: str = "+0Hz") -> None:
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(output_path)


_EDGE_TTS_VOICES = {"Female": "en-US-JennyNeural", "Male": "en-US-GuyNeural"}
_ELEVENLABS_VOICES = {
    "Female": "21m00Tcm4TlvDq8ikWAM",  # Rachel
    "Male": "TxGEqnHWrfWFTfGW9XjX",    # Josh
}


def generate_voiceover(
    text: str,
    output_path: str,
    provider: str = "edge-tts",
    elevenlabs_api_key: str = "",
    rate: str = "+0%",
    pitch: str = "+0Hz",
    gender: str = "Female",
) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    if provider == "edge-tts":
        voice = _EDGE_TTS_VOICES.get(gender, "en-US-JennyNeural")
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                _edge_tts_generate(text, output_path, voice, rate=rate, pitch=pitch)
            )
        finally:
            loop.close()

    elif provider == "elevenlabs":
        _rate_to_speed = {"-50%": 0.7, "-25%": 0.85, "+0%": 1.0, "+25%": 1.15, "+50%": 1.3}
        speed = _rate_to_speed.get(rate, 1.0)
        voice_id = _ELEVENLABS_VOICES.get(gender, "21m00Tcm4TlvDq8ikWAM")
        from elevenlabs import ElevenLabs
        from elevenlabs.types import VoiceSettings
        client = ElevenLabs(api_key=elevenlabs_api_key)
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            voice_settings=VoiceSettings(speed=speed),
        )
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)

    else:
        raise ValueError(f"Unknown TTS provider: {provider}")

    return output_path
