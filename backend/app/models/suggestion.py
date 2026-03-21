from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, make_uuid


class Suggestion(Base, TimestampMixin):
    __tablename__ = "suggestions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    strategy_type: Mapped[str] = mapped_column(String(50))  # cbt_reframe | tiny_habit | mva | pattern_insight
    life_area: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    energy_required: Mapped[int] = mapped_column(Integer)  # 1-10
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | accepted | rejected | completed
    effectiveness_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Suggestion [{self.strategy_type}] energy={self.energy_required}>"
