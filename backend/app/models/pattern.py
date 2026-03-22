from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class DetectedPattern(Document):
    user_id: Indexed(str)
    pattern_type: str  # temporal | mood_trigger | behavior_chain | energy_cycle
    description: str
    evidence: Optional[dict] = None
    confidence: float  # 0.0 - 1.0
    times_confirmed: int = 0
    is_active: bool = True
    acknowledged_by_user: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "detected_patterns"
