# app/value.py

from pydantic import BaseModel
from typing import Optional

class DailyBrief(BaseModel):
    """
    Ein ValueObject für das tägliche Briefing.
    Stellt sicher, dass die Datenstruktur konsistent ist.
    """
    title: str
    briefing_text: str
    timestamp: str
    status: str
    error_message: Optional[str] = None