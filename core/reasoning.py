import re
from collections import Counter

DEFAULT_KEYWORDS = [
    "airdrop","points","testnet","incentive","season","quest",
    "ai","agent","mcp","llm",
    "token","listing","tge","raise","funding","mainnet","launch",
    "hack","exploit","scam","rug","exposed","drama"
]

def detect_topics(tweets: list[str], topn=5):
    text = " ".join([t.lower() for t in tweets])
    hits = []
    for kw in DEFAULT_KEYWORDS:
        if kw in text:
            hits.append(kw)

    hashtags = re.findall(r"#\w+", text)
    common = Counter(hits + hashtags).most_common(topn)
    return [x[0] for x in common]

def guess_persona(profile: dict, tweets: list[str]) -> str:
    bio = (profile.get("bio","") or "").lower()
    alltxt = (bio + " " + " ".join(tweets[:15]).lower())

    if "founder" in alltxt or "ceo" in alltxt:
        return "builder/founder vibes"
    if "trader" in alltxt or "signals" in alltxt:
        return "trader/influencer vibes"
    if "research" in alltxt:
        return "researcher vibes"
    if "ai" in alltxt:
        return "AI niche"
    if "airdrop" in alltxt or "points" in alltxt:
        return "airdrop farmer niche"
    return "general influencer/project"

def build_story_context(profile: dict, tweets: list[str]) -> dict:
    topics = detect_topics(tweets)
    return {
        "persona_guess": guess_persona(profile, tweets),
        "topics": topics,
        "top_signal": tweets[0][:220] if tweets else ""
    }
