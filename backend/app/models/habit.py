from datetime import date, datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class Habit(Document):
    user_id: Indexed(str)
    name: str
    anchor: str
    tiny_behavior: str
    full_behavior: Optional[str] = None
    celebration: Optional[str] = None
    life_area: str
    is_active: bool = True
    current_streak: int = 0
    longest_streak: int = 0
    total_completions: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "habits"


class HabitLog(Document):
    habit_id: Indexed(str)
    completed: bool
    version_done: Optional[str] = None  # tiny | full
    note: Optional[str] = None
    logged_date: date
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "habit_logs"
