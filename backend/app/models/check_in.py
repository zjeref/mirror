from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class CheckIn(Document):
    user_id: Indexed(str)
    check_in_type: str  # morning | evening | ad_hoc
    mood_score: int  # 1-10
    energy_score: int  # 1-10
    mood_tags: Optional[list[str]] = None
    sleep_quality: Optional[int] = None
    top_intention: Optional[str] = None
    blocker: Optional[str] = None
    wins: Optional[str] = None
    conversation_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "check_ins"
