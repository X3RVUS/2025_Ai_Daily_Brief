import feedparser
import httpx
import os
from datetime import datetime
from typing import Dict, List

class KnowledgeScraper:
    """
    Holt tagesaktuelle Themen aus frei verfügbaren Quellen (RSS),
    basierend auf einer Interessen-Liste.
    """

    FREE_FEEDS = {
        "News": [
            "https://rss.dw.com/rdf/rss-en-ger",           # DW Deutschland
            "https://feeds.bbci.co.uk/news/world/rss.xml", # BBC World
        ],
        "Technology": [
            "https://www.heise.de/rss/heise-top-atom.xml", # Heise IT
            "https://www.theverge.com/rss/index.xml",      # The Verge
        ],
        "Science": [
            "https://www.sciencenews.org/feed",            # Science News
        ],
    }

    def __init__(self, interests: Dict[str, bool], openai_api_key: str):
        self.interests = interests
        self.api_key = openai_api_key

    def fetch_latest(self, interest: str, limit: int = 5) -> List[Dict]:
        """Holt die neuesten Einträge für ein Interesse."""
        results = []
        feeds = self.FREE_FEEDS.get(interest, [])
        for feed_url in feeds:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:limit]:
                results.append({
                    "title": entry.get("title"),
                    "link": entry.get("link")
                })
        return results[:limit]

    async def generate_daily_brief(self, interest: str, items: List[Dict]) -> str:
        """Erstellt ein Markdown-Briefing via OpenAI für ein bestimmtes Interesse."""
        if not items:
            return f"### {interest}\nKeine aktuellen Themen gefunden."

        context = "\n".join([f"- {item['title']} ({item['link']})" for item in items])
        prompt = f"""
Erstelle ein kompaktes Markdown-Briefing zu den folgenden aktuellen Themen für '{interest}'.
Fasse die wichtigsten Punkte in 2-3 Sätzen pro Meldung zusammen, mit Link:
{context}
"""

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "Du erstellst kurze, tagesaktuelle Markdown-Briefings."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 400,
                }
            )
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")


# --- Beispiel-Main ---
if __name__ == "__main__":
    import asyncio, json

    # Beispiel-Interessen
    interests = {
        "News": True,
        "Technology": True,
        "Science": False
    }

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    scraper = KnowledgeScraper(interests, OPENAI_API_KEY)

    async def main():
        for interest, active in interests.items():
            if not active:
                continue

            print(f"\n=== Hole aktuelle Themen für {interest} ===")
            latest = scraper.fetch_latest(interest)
            for i, item in enumerate(latest, 1):
                print(f"{i}. {item['title']}")

            print("\n=== Erstelle Daily Brief ===")
            brief = await scraper.generate_daily_brief(interest, latest)
            print(brief)

    asyncio.run(main())
