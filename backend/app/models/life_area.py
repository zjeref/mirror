from datetime import datetime, timezone

from beanie import Document, Indexed
from pydantic import Field


class LifeAreaScore(Document):
    user_id: Indexed(str)
    area: str  # physical | mental | career | habits
    score: float  # 0.0 - 10.0
    scored_at: datetime
    source: str  # check_in | self_assessment | inferred
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "life_area_scores"
