from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class ThoughtRecord(Document):
    user_id: Indexed(str)
    situation: str
    automatic_thought: str
    emotion: str
    emotion_intensity: int  # 1-10
    cognitive_distortions: Optional[list[str]] = None
    reframe: Optional[str] = None
    reframe_believability: Optional[int] = None
    conversation_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "thought_records"
