from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, make_uuid


class DetectedPattern(Base, TimestampMixin):
    __tablename__ = "detected_patterns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    pattern_type: Mapped[str] = mapped_column(String(50))  # temporal | mood_trigger | behavior_chain | energy_cycle
    description: Mapped[str] = mapped_column(Text)
    evidence: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float)  # 0.0 - 1.0
    times_confirmed: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    acknowledged_by_user: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<Pattern '{self.description[:40]}' conf={self.confidence}>"
