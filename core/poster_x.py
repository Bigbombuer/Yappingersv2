import os, time
from playwright.sync_api import sync_playwright

X_AUTH_TOKEN = os.getenv("X_AUTH_TOKEN")
X_CT0 = os.getenv("X_CT0")
X_PROFILE_DIR = os.getenv("X_PROFILE_DIR", "x_profile")

def inject_x_cookies(ctx):
    if not X_AUTH_TOKEN or not X_CT0:
        raise RuntimeError("X_AUTH_TOKEN / X_CT0 belum diset")
    ctx.add_cookies([
        {"name":"auth_token","value":X_AUTH_TOKEN,"domain":".x.com","path":"/","httpOnly":True,"secure":True,"sameSite":"Lax"},
        {"name":"ct0","value":X_CT0,"domain":".x.com","path":"/","httpOnly":False,"secure":True,"sameSite":"Lax"},
    ])

def open_context(p):
    return p.chromium.launch_persistent_context(
        user_data_dir=X_PROFILE_DIR,
        headless=True,
        viewport={"width": 430, "height": 900},
        locale="en-US",
    )

def post_thread(thread_lines: list[str]) -> dict:
    lines = [x.strip() for x in thread_lines if x and str(x).strip()]
    if len(lines) < 2:
        raise RuntimeError("Thread terlalu pendek")

    with sync_playwright() as p:
        ctx = open_context(p)
        inject_x_cookies(ctx)
        page = ctx.new_page()

        for i, line in enumerate(lines):
            page.goto("https://x.com/compose/post", wait_until="domcontentloaded")
            time.sleep(3)

            box = page.query_selector('[data-testid="tweetTextarea_0"]')
            if not box:
                raise RuntimeError("Textbox tweet tidak ditemukan (kena captcha/limit?)")
            box.click()
            page.keyboard.type(line, delay=8)

            btn = page.query_selector('[data-testid="tweetButtonInline"]') or page.query_selector('[data-testid="tweetButton"]')
            if not btn:
                raise RuntimeError("Tombol tweet tidak ditemukan")
            btn.click()
            time.sleep(4)

        ctx.close()

    return {"ok": True, "posted": len(lines)}
