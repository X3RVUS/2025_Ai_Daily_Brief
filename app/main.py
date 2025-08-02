import os
import json
from datetime import datetime
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from .src.value import DailyBrief
from .src.prompt import PromptManager
from .src.knowledge_scraper import KnowledgeScraper

# -------------------------------------------------------
# 1️⃣ ENV & CONFIG
# -------------------------------------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("❌ WARNUNG: Kein OPENAI_API_KEY in .env gefunden!")

BASE_DIR = Path(__file__).parent
INTERESTS_FILE = BASE_DIR / "interests.json"
PROMPT_FILE = BASE_DIR / "prompt.yml"

# PromptManager initialisieren (falls du noch interne Prompts nutzt)
prompt_manager = PromptManager(PROMPT_FILE)

# FastAPI Setup
app = FastAPI()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


# -------------------------------------------------------
# 2️⃣ HTML Routen
# -------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/interests", response_class=HTMLResponse)
async def interests_page(request: Request):
    return templates.TemplateResponse("interests.html", {"request": request})


# -------------------------------------------------------
# 3️⃣ API: Interessen speichern/laden
# -------------------------------------------------------
@app.get("/api/interests")
async def get_interests():
    with open(INTERESTS_FILE) as f:
        return json.load(f)

@app.post("/api/interests")
async def save_interests(interests: dict):
    with open(INTERESTS_FILE, "w") as f:
        json.dump(interests, f, indent=2)
    return {"status": "saved"}


# -------------------------------------------------------
# 4️⃣ API: Daily Brief mit KnowledgeScraper
# -------------------------------------------------------
@app.get("/api/daily-brief")
async def daily_brief():
    """
    Holt aktuelle Themen aus freien Quellen für jede aktive Interesse
    und erstellt ein Markdown-Daily-Briefing per OpenAI.
    """
    briefing = DailyBrief(
        title="Tägliches KI-Briefing",
        briefing_text="Kein Briefing geladen...",
        timestamp=datetime.now().isoformat(),
        status="error",
    )

    try:
        # 1. Interessen laden
        with open(INTERESTS_FILE) as f:
            interests = json.load(f)

        # 2. KnowledgeScraper initialisieren
        scraper = KnowledgeScraper(interests, OPENAI_API_KEY)

        # 3. Nacheinander alle aktiven Interessen abarbeiten
        all_briefs = []
        for interest, active in interests.items():
            if not active:
                continue

            # Aktuelle Themen holen
            topics = scraper.fetch_latest(interest)

            # GPT Markdown-Briefing erzeugen
            brief_md = await scraper.generate_daily_brief(interest, topics)
            all_briefs.append(brief_md)

        # 4. Gesamtbriefing zusammenführen
        briefing.briefing_text = "\n\n---\n\n".join(all_briefs)
        briefing.status = "success"
        briefing.error_message = None

    except Exception as e:
        briefing.error_message = f"Fehler bei Daily Brief Generierung: {str(e)}"

    return briefing.dict()
