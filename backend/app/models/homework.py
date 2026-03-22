from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class Homework(Document):
    user_id: Indexed(str)
    enrollment_id: str
    session_number: int
    description: str
    adaptive_tier: str = "structured"
    due_date: Optional[datetime] = None
    status: str = "assigned"
    user_response: Optional[str] = None
    completed_at: Optional[datetime] = None
    reminder_count: int = 0

    class Settings:
        name = "homework"
        indexes = [
            [("user_id", 1), ("status", 1)],
            [("enrollment_id", 1), ("session_number", 1)],
        ]
