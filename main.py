import google.generativeai as genai
import os
import datetime
import random
from dotenv import load_dotenv # Importiere load_dotenv

# Lade Umgebungsvariablen aus der .env-Datei
load_dotenv()

# --- Konfiguration ---
# API-Schlüssel aus Umgebungsvariablen laden
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("Fehler: GEMINI_API_KEY nicht in der .env-Datei gefunden oder nicht gesetzt.")
    print("Bitte erstellen Sie eine .env-Datei im selben Verzeichnis mit dem Inhalt: GEMINI_API_KEY='IHR_API_SCHLUESSEL'")
    exit() # Beende das Programm, wenn der Schlüssel fehlt

genai.configure(api_key=API_KEY)

# Das zu verwendende Gemini-Modell
MODEL_NAME = "gemini-1.5-flash" # Oder gemini-1.5-pro für komplexere Anfragen, beachte die Kosten.

# Dateiname für die Interessen
INTERESTS_FILE = "News_Interessen.txt"

# --- Hilfsfunktionen ---

def read_interests_from_file(filepath):
    """
    Liest Interessen aus einer Textdatei, jede Zeile ein Interesse.
    Leere Zeilen und Kommentare (#) werden ignoriert.
    """
    interests = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith('#'):
                    interests.append(stripped_line)
    except FileNotFoundError:
        print(f"Fehler: Die Datei '{filepath}' wurde nicht gefunden.")
        print("Bitte erstellen Sie eine Datei namens 'News_Interessen.txt' im selben Verzeichnis")
        print("und tragen Sie Ihre Interessen, jeweils eine pro Zeile, ein.")
    except Exception as e:
        print(f"Fehler beim Lesen der Datei '{filepath}': {e}")
    return interests

# --- Funktionen für die App-Features ---

def get_daily_overview():
    """
    Erstellt eine kurze Tagesübersicht.
    HINWEIS: Diese Funktion verwendet weiterhin 'google_search', was in einer lokalen IDE
    zu einem 'name 'google_search' is not defined' Fehler führen wird.
    Für eine vollständige lokale Ausführbarkeit müsste auch diese Funktion angepasst werden,
    um Daten zu simulieren oder eine andere Web-Such-API zu integrieren.
    """
    model = genai.GenerativeModel(MODEL_NAME)
    today = datetime.date.today().strftime("%Y-%m-%d")

    try:
        print(f"Suche nach Top-Nachrichten für {today}...")
        # Nutzt das google_search Tool (führt zu Fehler in lokaler IDE ohne Tooling-API)
        search_results = google_search.search(queries=[f"Top Nachrichten heute {today} Deutschland", f"Breaking News international {today}"])
        news_snippets = []
        
        # Sicherstellen, dass search_results eine Liste von SearchResults-Objekten ist
        for result_set in search_results:
            if result_set and 'results' in result_set:
                for result in result_set['results']:
                    if 'snippet' in result and result['snippet']:
                        news_snippets.append(result['snippet'])

        if not news_snippets:
            return "Konnte heute keine relevanten Top-Nachrichten finden."

        combined_text = "\n".join(news_snippets[:5]) # Nehmen wir die ersten 5 Snippets

        prompt = (f"Fasse die folgenden Informationen zu den wichtigsten Ereignissen vom {today} kurz und prägnant zusammen (Max. 150 Wörter):\n\n"
                  f"{combined_text}\n\n"
                  f"Fokus auf die wichtigsten Punkte in Deutschland und weltweit.")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Fehler beim Abrufen der Tagesübersicht: {e}"


def summarize_news_by_interests(interests):
    """
    Fasst Nachrichten basierend auf Interessen zusammen.
    Die Informationen werden direkt von Gemini generiert, ohne externe Suche.
    """
    model = genai.GenerativeModel(MODEL_NAME)
    summaries = []
    for interest in interests:
        print(f"Generiere Zusammenfassung für '{interest}' mit Gemini...")
        try:
            # Prompt, um Gemini zu bitten, Nachrichten zu einem Thema zu generieren
            prompt = (f"Gib mir eine kurze, prägnante Zusammenfassung der wichtigsten und aktuellsten Entwicklungen "
                      f"zum Thema '{interest}' (Max. 70 Wörter). Füge einen Hinweis hinzu, wo man mehr erfahren kann "
                      f"(z.B. 'Mehr dazu auf [Nachrichtenseite XY]').")
            
            summary_response = model.generate_content(prompt)
            summary = summary_response.text

            summaries.append(
                f"### {interest}:\n"
                f"{summary}\n"
            )

        except Exception as e:
            summaries.append(f"### {interest}:\nFehler beim Generieren der Nachrichten-Zusammenfassung: {e}\n")
    return "\n".join(summaries)


def get_random_fact(interest):
    """
    Gibt einen zufälligen Fakt zu einem bestimmten Interesse zurück.
    """
    model = genai.GenerativeModel(MODEL_NAME)
    prompt = f"Nenne einen interessanten und wenig bekannten Fakt zum Thema '{interest}'. Max. 50 Wörter."
    response = model.generate_content(prompt)
    return response.text

def learn_about_famous_person():
    """
    Stellt jeden Tag eine berühmte Person vor.
    Die Informationen werden direkt von Gemini generiert, ohne externe Suche.
    """
    model = genai.GenerativeModel(MODEL_NAME)
    try:
        # Prompt, um Gemini zu bitten, eine berühmte Person vorzustellen
        prompt = (f"Stell mir eine berühmte Person vor, die heute oder in der letzten Woche Geburtstag hatte, "
                  f"oder die etwas Besonderes geleistet hat. Nenne den Namen, warum sie berühmt ist "
                  f"und einen interessanten Fakt über sie. Max. 100 Wörter. "
                  f"Formatiere es als 'Name: Grund der Berühmtheit. Interessanter Fakt.'.")
        
        response = model.generate_content(prompt)
        person_info = response.text
        return person_info
    except Exception as e:
        return f"Fehler beim Abrufen der berühmten Person: {e}"


# --- Prototypen-Ausführung ---
if __name__ == "__main__":
    print("--- AI Daily Brief Prototyp ---")

    # Tagesübersicht
    print("\n## Deine Tagesübersicht:")
    overview = get_daily_overview()
    print(overview)

    # Personalisierte Nachrichten aus Datei lesen und zusammenfassen
    user_interests = read_interests_from_file(INTERESTS_FILE)
    if user_interests:
        print(f"\n## Nachrichten für deine Interessen aus '{INTERESTS_FILE}':")
        news_summaries = summarize_news_by_interests(user_interests)
        print(news_summaries)
    else:
        print(f"\nKeine Interessen in '{INTERESTS_FILE}' gefunden. Überspringe personalisierte Nachrichten.")


    # Zufälliger Fakt (nimmt den ersten gefundenen Interesse oder ein Standardthema)
    if user_interests:
        random_fact_interest = user_interests[0]
    else:
        random_fact_interest = "Wissenschaft" # Standardthema, falls keine Interessen definiert

    print(f"\n## Zufälliger Fakt über '{random_fact_interest}':")
    fact = get_random_fact(random_fact_interest)
    print(fact)

    # Berühmte Person
    print("\n## Berühmte Person des Tages:")
    person = learn_about_famous_person()
    print(person)

    print("\n--- Prototyp-Ende ---")
