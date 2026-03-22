from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class User(Document):
    email: Indexed(str, unique=True)
    name: str
    password_hash: str
    preferences: dict = Field(default_factory=dict)
    energy_profile: dict = Field(default_factory=dict)
    preferred_session_time: str = "evening"
    notification_enabled: bool = False
    max_notifications_per_day: int = 2
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"
    push_subscription: Optional[dict] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"

    def __repr__(self) -> str:
        return f"<User {self.email}>"
