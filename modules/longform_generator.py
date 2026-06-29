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
- Inclua rehooks entre os segmentos para manter o espectador engajado
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
- Ao final, escreva o payoff filosófico que o espectador vai levar
- NÃO inclua nenhum rótulo estrutural no texto (sem "Segmento", "Rehook", "Payoff", "Setup", "Tensão", "Hook" como títulos ou marcadores — escreva o roteiro corrido, como se fosse falar direto para a câmera)"""
    return _call_llm(prompt, system_prompt, api_key, provider)
