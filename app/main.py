from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, json, httpx
from dotenv import load_dotenv
from datetime import datetime

from app.value import DailyBrief
from app.prompt import PromptManager

# .env laden
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("❌ WARNUNG: Kein OPENAI_API_KEY in .env gefunden! Bitte eintragen und Container neu starten.")

INTERESTS_FILE = "app/interests.json"
PROMPT_FILE = "app/prompt.yml"

# Initialisiere den PromptManager einmalig
prompt_manager = PromptManager(PROMPT_FILE)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# Static & Templates mounten
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/interests", response_class=HTMLResponse)
async def interests_page(request: Request):
    return templates.TemplateResponse("interests.html", {"request": request})

@app.get("/api/interests")
async def get_interests():
    with open(INTERESTS_FILE) as f:
        return json.load(f)

@app.post("/api/interests")
async def save_interests(interests: dict):
    with open(INTERESTS_FILE, "w") as f:
        json.dump(interests, f, indent=2)
    return {"status": "saved"}

@app.get("/api/daily-brief")
async def daily_brief():
    """Generiert das tägliche Briefing basierend auf den Nutzerinteressen."""

    briefing = DailyBrief(
        title="Tägliches KI-Briefing",
        briefing_text="Kein Briefing geladen...",
        timestamp=datetime.now().isoformat(),
        status="error",
    )

    try:
        with open(INTERESTS_FILE) as f:
            interests = json.load(f)
        prompt = prompt_manager.create_prompt(interests)

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "Du verfasst tägliche Briefings im Markdown-Format."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 400,
                    "response_format": {"type": "text"}
                }
            )
        data = resp.json()
        print("DEBUG API RESPONSE:", data)

        if "choices" in data:
            briefing.briefing_text = data["choices"][0]["message"]["content"]
            briefing.status = "success"
            briefing.error_message = None
        else:
            briefing.error_message = f"Fehler: {data.get('error', data)}"

    except httpx.ReadTimeout:
        briefing.error_message = "Fehler: Anfrage an OpenAI hat zu lange gedauert (Timeout)"
    except Exception as e:
        briefing.error_message = f"Unerwarteter Fehler: {str(e)}"

    return briefing.dict()
