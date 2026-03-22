"""Journal entry model for daily diary feature."""

from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class JournalEntry(Document):
    user_id: Indexed(str)
    date: Indexed(str)  # "2026-03-22" format
    content: str = ""
    mood_score: Optional[int] = None  # 1-10
    energy_score: Optional[int] = None  # 1-10
    tags: list[str] = Field(default_factory=list)
    wins: list[str] = Field(default_factory=list)
    ai_reflection: Optional[str] = None
    word_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "journal_entries"
        indexes = [
            [("user_id", 1), ("date", -1)],
        ]
