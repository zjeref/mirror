from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class ProtocolEnrollment(Document):
    user_id: Indexed(str)
    protocol_id: str
    current_session_number: int = 0
    status: str = "enrolled"
    entry_screening_id: Optional[str] = None
    screening_scores: list[dict] = Field(default_factory=list)
    switched_to_enrollment_id: Optional[str] = None
    start_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_date: Optional[datetime] = None
    consecutive_homework_misses: int = 0

    class Settings:
        name = "protocol_enrollments"
        indexes = [
            [("user_id", 1), ("status", 1)],
        ]


class ProtocolSession(Document):
    enrollment_id: Indexed(str)
    user_id: str
    session_number: int
    goals: list[str] = Field(default_factory=list)
    activities_completed: list[str] = Field(default_factory=list)
    session_notes: str = ""
    outcome: str = ""
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    class Settings:
        name = "protocol_sessions"
        indexes = [
            [("enrollment_id", 1), ("session_number", 1)],
        ]
