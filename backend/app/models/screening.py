from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class ScreeningResult(Document):
    user_id: Indexed(str)
    instrument: str
    item_scores: list[int] = Field(default_factory=list)
    total_score: int = 0
    severity_tier: str = ""
    status: str = "in_progress"
    current_item: int = 0
    linked_enrollment_id: Optional[str] = None
    created_at: Indexed(datetime) = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    class Settings:
        name = "screening_results"
        indexes = [
            [("user_id", 1), ("created_at", -1)],
            [("user_id", 1), ("instrument", 1), ("status", 1)],
        ]
