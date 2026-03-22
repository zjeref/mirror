from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class Suggestion(Document):
    user_id: Indexed(str)
    strategy_type: str  # cbt_reframe | tiny_habit | mva | pattern_insight
    life_area: str
    content: str
    rationale: Optional[str] = None
    energy_required: int  # 1-10
    status: str = "pending"  # pending | accepted | rejected | completed
    effectiveness_rating: Optional[int] = None  # 1-5
    responded_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "suggestions"
