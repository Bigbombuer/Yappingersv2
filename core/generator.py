import os, json, requests, re, time

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

def groq_chat(system: str, user: str, temperature=0.2) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY belum diset")

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
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
    if not text:
        raise ValueError("Model output kosong")

    # ambil JSON object pertama yang ketemu
    s = text.find("{")
    e = text.rfind("}")

    if s == -1 or e == -1 or e <= s:
        raise ValueError("Model output bukan JSON valid")

    raw = text[s:e+1].strip()

    # bersihin trailing triple backticks kalau ada
    raw = raw.strip("`")

    return json.loads(raw)

def generate_thread_pack(profile: dict, tweets: list[str], context: dict) -> dict:
    joined = "\n".join(tweets[:60])

    system = (
        "Kamu adalah Auto Yapping Engine Indonesia.\n"
        "Kamu HARUS output dalam JSON VALID.\n"
        "DILARANG output teks di luar JSON.\n"
        "DILARANG pakai markdown.\n"
        "Kalau tidak yakin data, tulis sebagai opini/kemungkinan.\n"
    )

    user = (
        f"AKUN:\n"
        f"- username: @{profile.get('username')}\n"
        f"- bio: {profile.get('bio')}\n"
        f"- pinned: {profile.get('pinned')}\n"
        f"- url: {profile.get('url')}\n\n"
        f"KONTEKS:\n"
        f"- persona_guess: {context.get('persona_guess')}\n"
        f"- topics: {context.get('topics')}\n\n"
        f"TWEETS RAW:\n{joined}\n\n"
        "OUTPUT HARUS JSON VALID persis format ini:\n"
        "{\n"
        '  "title":"...",\n'
        '  "hooks":["...","...","..."],\n'
        '  "thread_clean":["tweet1","tweet2"],\n'
        '  "thread_barbar":["tweet1","tweet2"],\n'
        '  "timeline":["..."],\n'
        '  "takeaways":["..."],\n'
        '  "reply_bait":["..."],\n'
        '  "cta":"..."\n'
        "}\n\n"
        "Rules:\n"
        "- BALAS HANYA JSON\n"
        "- max 260 karakter per tweet\n"
        "- thread_barbar 12-20 tweet\n"
    )

    last_raw = ""
    for attempt in range(1, 4):
        raw = groq_chat(system, user, temperature=0.2)
        last_raw = raw

        try:
            return extract_json(raw)
        except Exception:
            # retry dengan instruksi lebih keras
            user2 = (
                "ERROR: JSON kamu tidak valid.\n"
                "PERBAIKI. BALAS HANYA JSON VALID TANPA TEKS LAIN.\n\n"
                "Ini outputmu sebelumnya:\n"
                + raw +
                "\n\nSekarang ulangi dalam JSON VALID:"
            )
            user = user2
            time.sleep(1)

    # kalau 3x gagal → tampilkan raw biar gampang debug
    raise RuntimeError("Model output bukan JSON valid. RAW:\n" + last_raw)