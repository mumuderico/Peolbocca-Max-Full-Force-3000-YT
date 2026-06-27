import asyncio
import os


PLATFORM_INSTRUCTIONS = {
    "TikTok": "short and punchy, hook in the first line, 150–250 words",
    "Instagram Reels": "engaging with a strong opening, 200–300 words, add 5–8 relevant hashtags at the end",
    "YouTube Shorts": "slightly more informative, clear structure, 200–300 words",
}


def list_scripts(scripts_dir: str) -> list[str]:
    if not os.path.exists(scripts_dir):
        return []
    return [f for f in os.listdir(scripts_dir) if f.endswith(".txt")]


def save_script(filename: str, content: str, scripts_dir: str) -> None:
    os.makedirs(scripts_dir, exist_ok=True)
    with open(os.path.join(scripts_dir, filename), "w", encoding="utf-8") as f:
        f.write(content)


def delete_script(filename: str, scripts_dir: str) -> None:
    path = os.path.join(scripts_dir, filename)
    if os.path.exists(path):
        os.remove(path)


def load_user_scripts(scripts_dir: str) -> list[str]:
    contents = []
    for filename in list_scripts(scripts_dir):
        with open(os.path.join(scripts_dir, filename), "r", encoding="utf-8") as f:
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
    style_examples = (
        "\n\n---\n\n".join(user_scripts)
        if user_scripts
        else "No examples provided — use a generic engaging style."
    )
    platform_guide = PLATFORM_INSTRUCTIONS.get(platform, "engaging and concise")

    prompt = (
        f"You are a social media content creator. Generate a script for a {platform} video "
        f"about \"{topic}\" written in {language}.\n\n"
        f"Format: {platform_guide}.\n\n"
        f"Here are examples of the creator's writing style — match their tone, vocabulary, and structure:\n\n"
        f"---\n{style_examples}\n---\n\n"
        f"Write only the script text. No introductions, no meta-commentary."
    )

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


async def _edge_tts_generate(text: str, output_path: str, voice: str) -> None:
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def generate_voiceover(
    text: str,
    output_path: str,
    provider: str = "edge-tts",
    elevenlabs_api_key: str = "",
) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    if provider == "edge-tts":
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                _edge_tts_generate(text, output_path, "en-US-JennyNeural")
            )
        finally:
            loop.close()

    elif provider == "elevenlabs":
        from elevenlabs import ElevenLabs
        client = ElevenLabs(api_key=elevenlabs_api_key)
        audio = client.text_to_speech.convert(
            voice_id="21m00Tcm4TlvDq8ikWAM",
            text=text,
        )
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)

    else:
        raise ValueError(f"Unknown TTS provider: {provider}")

    return output_path
