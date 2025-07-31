from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, json, httpx
from dotenv import load_dotenv

# .env laden
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # <-- Key aus Environment

if not OPENAI_API_KEY:
    print("❌ WARNUNG: Kein OPENAI_API_KEY in .env gefunden! Bitte eintragen und Container neu starten.")

INTERESTS_FILE = "app/interests.json"

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
    try:
        # Anfrage an OpenAI schicken
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "Erstelle ein kurzes tägliches Briefing"}],
                    "max_tokens": 150
                }
            )
            data = resp.json()
            print("DEBUG API RESPONSE:", data)

            if "choices" in data:
                return {"brief": data["choices"][0]["message"]["content"]}
            else:
                return {"brief": f"Fehler: {data.get('error', data)}"}

    except httpx.ReadTimeout:
        return {"brief": "Fehler: Anfrage an OpenAI hat zu lange gedauert (Timeout)"}
    except Exception as e:
        return {"brief": f"Unerwarteter Fehler: {str(e)}"}
