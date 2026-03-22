"""Activity tracking for Behavioral Activation.

Each activity records what the user did, how they felt before/after,
and pleasure + mastery scores. This is the core BA data model.
"""

from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class Activity(Document):
    user_id: Indexed(str)
    conversation_id: Optional[str] = None

    # What they did
    name: str
    description: Optional[str] = None
    life_area: Optional[str] = None  # physical, mental, career, habits, relationships, creativity

    # Value alignment
    linked_value: Optional[str] = None  # e.g., "being a present parent"

    # Mood before/after (the core BA proof mechanism)
    mood_before: Optional[float] = None  # 1-10
    mood_after: Optional[float] = None  # 1-10

    # Pleasure and Mastery ratings (BA standard)
    pleasure: Optional[float] = None  # 1-10 how enjoyable
    mastery: Optional[float] = None  # 1-10 sense of accomplishment

    # Scheduling
    scheduled_for: Optional[datetime] = None
    completed: bool = False
    skipped: bool = False
    skip_reason: Optional[str] = None  # avoidance, practical_barrier, low_energy, forgot

    # Source
    source: str = "chat"  # chat, check_in, self_reported, suggested

    created_at: Indexed(datetime, index_type=1) = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: Optional[datetime] = None

    class Settings:
        name = "activities"
        indexes = [
            [("user_id", 1), ("created_at", -1)],
            [("user_id", 1), ("completed", 1)],
        ]


class UserValues(Document):
    """Stores the user's identified core values across life areas."""
    user_id: Indexed(str, unique=True)
    values: dict = Field(default_factory=dict)
    # Format: {"relationships": ["being a present parent", "showing up for friends"],
    #          "health": ["taking care of my body"], ...}
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "user_values"
