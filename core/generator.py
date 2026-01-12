import os, json, requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

def groq_chat(system: str, user: str, temperature=0.8) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY belum diset")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }

    r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def extract_json(text: str) -> dict:
    s = text.find("{")
    e = text.rfind("}")
    if s == -1 or e == -1 or e <= s:
        raise ValueError("Model output bukan JSON valid")
    return json.loads(text[s:e+1])

def generate_barbar_thread(profile: dict, tweets: list[str], context: dict) -> dict:
    joined = "\n".join(tweets[:60])

    system = (
        "Kamu adalah Auto Yapping Engine Indonesia. "
        "Bikin thread yang informatif + engagement tinggi. "
        "Bedakan fakta vs opini. Jangan ngarang detail."
    )

    user = (
        f"AKUN:\n"
        f"- username: @{profile.get('username')}\n"
        f"- bio: {profile.get('bio')}\n"
        f"- pinned: {profile.get('pinned')}\n\n"
        f"KONTEKS:\n"
        f"- persona_guess: {context.get('persona_guess')}\n"
        f"- topics: {context.get('topics')}\n\n"
        f"TWEETS RAW:\n{joined}\n\n"
        "Output HARUS JSON valid:\n"
        "{\n"
        '  "title": "...",\n'
        '  "hooks": ["...","...","..."],\n'
        '  "thread_clean": ["..."],\n'
        '  "thread_barbar": ["..."],\n'
        '  "timeline": ["..."],\n'
        '  "takeaways": ["..."],\n'
        '  "reply_bait": ["..."],\n'
        '  "cta": "..."\n'
        "}\n"
        "Rules:\n"
        "- tweet max 260 karakter\n"
        "- thread_barbar minimal 15 tweet, maksimal 25 tweet\n"
    )

    raw = groq_chat(system, user, temperature=0.85)
    return extract_json(raw)    system = """Lu adalah Auto Yapping Engine Indonesia.
Lu bukan cuma ngerangkum. Lu nganalisis pake LOGIKA.

Tujuan:
- bikin thread selengkap mungkin
- engagement tinggi
- tetap masuk akal
- bedain FAKTA vs OPINI
- jangan halu / jangan ngarang"""

    user = f"""AKUN:
- username: @{profile.get('username')}
- bio: {profile.get('bio')}
- pinned: {profile.get('pinned')}
- url: {profile.get('url')}

KONTEKS:
- persona_guess: {context.get('persona_guess')}
- topics: {context.get('topics')}

TWEETS (raw):
"""
{joined}
"""

Output JSON valid:
{{
  "title": "...",
  "hooks": ["...", "...", "..."],
  "thread_clean": ["... (10-12 tweet)"],
  "thread_barbar": ["... (15-25 tweet)"],
  "timeline": ["...","...","..."],
  "takeaways": ["...","...","..."],
  "reply_bait": ["...", "...", "..."],
  "cta": "..."
}}

Rules:
- hook tweet1 harus nendang
- thread_barbar min 15 tweet max 25
- sertakan: siapa dia, kenapa rame, dampak, skenario, peluang, redflag
- max 260 karakter per tweet"""

    raw = groq_chat(system, user, temperature=0.85)
    return extract_json(raw)
