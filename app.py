import os
from flask import Flask, request, jsonify, render_template

from core.scraper_x import fetch_profile, fetch_tweets
from core.reasoning import build_story_context
from core.generator import generate_thread_pack

app = Flask(__name__)

REQUIRED_ENV = ["GROQ_API_KEY", "X_AUTH_TOKEN", "X_CT0"]

def missing_env():
    return [k for k in REQUIRED_ENV if not os.getenv(k)]

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/health")
def health():
    miss = missing_env()
    if miss:
        return jsonify({"ok": False, "missing": miss})
    return jsonify({"ok": True})

@app.get("/watchlist")
def watchlist():
    accounts = []
    try:
        with open("watchlist.txt", "r", encoding="utf-8") as f:
            accounts = [x.strip() for x in f.read().splitlines() if x.strip()]
    except Exception:
        pass
    return render_template("watchlist.html", accounts=accounts)

@app.post("/api/generate")
def api_generate():
    data = request.get_json(force=True) or {}

    username = (data.get("username") or "").strip().replace("@", "")
    limit = int(data.get("limit") or 80)

    if not username:
        return jsonify({"ok": False, "error": "username kosong"}), 400

    profile = fetch_profile(username)
    tweets = fetch_tweets(username, limit=limit)

    ctx = build_story_context(profile, tweets)
    pack = generate_thread_pack(profile, tweets, ctx)

    return jsonify({
        "ok": True,
        "profile": profile,
        "context": ctx,
        "pack": pack
    })

@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({"ok": False, "error": str(e)}), 500