from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class PendingAction(Document):
    user_id: Indexed(str)
    action_type: str
    priority: int = 5
    data: dict = Field(default_factory=dict)
    dismissed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    class Settings:
        name = "pending_actions"
        indexes = [
            [("user_id", 1), ("dismissed", 1), ("priority", 1)],
        ]
