from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, make_uuid


class CheckIn(Base, TimestampMixin):
    __tablename__ = "check_ins"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    check_in_type: Mapped[str] = mapped_column(String(20))  # morning | evening | ad_hoc
    mood_score: Mapped[int] = mapped_column(Integer)  # 1-10
    energy_score: Mapped[int] = mapped_column(Integer)  # 1-10
    mood_tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    sleep_quality: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-10
    top_intention: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    blocker: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    wins: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conversation_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("conversations.id"), nullable=True
    )

    def __repr__(self) -> str:
        return f"<CheckIn mood={self.mood_score} energy={self.energy_score}>"
