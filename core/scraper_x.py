import os, time, re
from playwright.sync_api import sync_playwright

X_AUTH_TOKEN = os.getenv("X_AUTH_TOKEN")
X_CT0 = os.getenv("X_CT0")
X_PROFILE_DIR = os.getenv("X_PROFILE_DIR", "x_profile")

def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def inject_x_cookies(ctx):
    if not X_AUTH_TOKEN or not X_CT0:
        raise RuntimeError("X_AUTH_TOKEN / X_CT0 belum diset")

    ctx.add_cookies([
        {"name": "auth_token", "value": X_AUTH_TOKEN, "domain": ".x.com", "path": "/", "httpOnly": True, "secure": True, "sameSite": "Lax"},
        {"name": "ct0", "value": X_CT0, "domain": ".x.com", "path": "/", "httpOnly": False, "secure": True, "sameSite": "Lax"},
    ])

def open_context(p):
    os.makedirs(X_PROFILE_DIR, exist_ok=True)
    return p.chromium.launch_persistent_context(
    user_data_dir=X_PROFILE_DIR,
    headless=True,
    viewport={"width": 430, "height": 900},
    locale="en-US",
    user_agent="Mozilla/5.0 (Linux; Android 12; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
)

def is_logged_in(page) -> bool:
    page.goto("https://x.com/home", wait_until="domcontentloaded")
    time.sleep(2)
    if "login" in page.url:
        return False
    html = (page.content() or "").lower()
    if "log in" in html and "sign in" in html:
        return False
    return True

def looks_like_spam(t: str) -> bool:
    low = (t or "").lower()
    spam_kw = ["giveaway", "retweet", "tag", "winner", "prize", "wagmi"]
    if any(k in low for k in spam_kw):
        return True
    if len(t) < 60:
        return True
    return False

def fetch_profile(username: str) -> dict:
    username = username.replace("@", "").strip()

    with sync_playwright() as p:
        ctx = open_context(p)
        inject_x_cookies(ctx)
        page = ctx.new_page()

        if not is_logged_in(page):
            ctx.close()
            raise RuntimeError("Cookie X invalid/expired")

        page.goto(f"https://x.com/{username}", wait_until="domcontentloaded")
        time.sleep(3)

        bio = ""
        pinned = ""

        try:
            bio_el = page.query_selector('[data-testid="UserDescription"]')
            if bio_el:
                bio = clean_text(bio_el.inner_text())
        except:
            pass

        try:
            arts = page.query_selector_all("article")
            if arts:
                pinned = clean_text(arts[0].inner_text())
        except:
            pass

        ctx.close()

    return {
        "username": username,
        "bio": bio,
        "pinned": pinned,
        "url": f"https://x.com/{username}"
    }

def fetch_tweets(username: str, limit=80, max_scan=250) -> list[str]:
    username = username.replace("@", "").strip()
    limit = max(20, min(int(limit), 200))

    tweets = []
    seen = set()

    with sync_playwright() as p:
        ctx = open_context(p)
        inject_x_cookies(ctx)
        page = ctx.new_page()

        if not is_logged_in(page):
            ctx.close()
            raise RuntimeError("Cookie X invalid/expired")

        page.goto(f"https://x.com/{username}", wait_until="domcontentloaded")
        time.sleep(3)

        scanned = 0
        for _ in range(25):
            arts = page.query_selector_all("article")

            for art in arts:
                if scanned >= max_scan:
                    break
                try:
                    raw = clean_text(art.inner_text())
                    scanned += 1

                    if raw in seen:
                        continue
                    seen.add(raw)

                    if "reposted" in raw.lower():
                        continue
                    if looks_like_spam(raw):
                        continue

                    tweets.append(raw)
                    if len(tweets) >= limit:
                        break
                except:
                    pass

            if scanned >= max_scan or len(tweets) >= limit:
                break

            page.mouse.wheel(0, 2400)
            time.sleep(1)

        ctx.close()

    return tweets[:limit]