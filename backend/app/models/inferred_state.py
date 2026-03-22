"""Stores passively inferred psychological state from each user message."""

from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class InferredStateRecord(Document):
    user_id: Indexed(str)
    conversation_id: Optional[str] = None
    message_content: str = ""  # Intentionally empty for privacy — mood scores suffice

    # Core dimensions
    mood_valence: Optional[float] = None  # 1-10
    energy_level: Optional[float] = None  # 1-10
    motivation_level: Optional[float] = None  # 1-10

    # Emotions detected by LLM
    emotions: list[str] = Field(default_factory=list)

    # Linguistic markers
    absolutist_count: int = 0
    first_person_ratio: float = 0.0
    word_count: int = 0

    # MI classification
    change_talk_score: float = 0.0
    sustain_talk_score: float = 0.0

    # Stage of change + risk
    stage_signals: dict = Field(default_factory=dict)

    # Themes detected
    themes: list[str] = Field(default_factory=list)

    confidence: float = 0.0
    created_at: Indexed(datetime, index_type=1) = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "inferred_states"
        indexes = [
            [("user_id", 1), ("created_at", -1)],  # Compound index for dashboard queries
        ]
