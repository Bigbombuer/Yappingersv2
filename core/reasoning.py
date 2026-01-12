import re
from collections import Counter

DEFAULT_KEYWORDS = [
    "airdrop","points","testnet","incentive","season","quest",
    "ai","agent","mcp","llm",
    "token","listing","tge","raise","funding","mainnet","launch",
    "hack","exploit","scam","rug","exposed","drama"
]

def detect_topics(tweets: list[str], topn=6):
    text = " ".join([t.lower() for t in tweets])
    hits = [kw for kw in DEFAULT_KEYWORDS if kw in text]
    hashtags = re.findall(r"#\w+", text)
    return [x[0] for x in Counter(hits + hashtags).most_common(topn)]

def guess_persona(profile: dict, tweets: list[str]) -> str:
    bio = (profile.get("bio") or "").lower()
    txt = bio + " " + " ".join(tweets[:15]).lower()

    if "founder" in txt or "ceo" in txt:
        return "builder/founder vibes"
    if "trader" in txt or "signals" in txt:
        return "trader/influencer vibes"
    if "research" in txt:
        return "research vibes"
    return "general"

def build_story_context(profile: dict, tweets: list[str]) -> dict:
    return {
        "persona_guess": guess_persona(profile, tweets),
        "topics": detect_topics(tweets),
        "top_signal": tweets[0][:220] if tweets else ""
    }