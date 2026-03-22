from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class EnergyReading(Document):
    user_id: Indexed(str)
    level: int  # 1-10
    context: Optional[str] = None
    recorded_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "energy_readings"
