from typing import Optional

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, make_uuid


class ThoughtRecord(Base, TimestampMixin):
    __tablename__ = "thought_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    situation: Mapped[str] = mapped_column(Text)
    automatic_thought: Mapped[str] = mapped_column(Text)
    emotion: Mapped[str] = mapped_column(String(50))
    emotion_intensity: Mapped[int] = mapped_column(Integer)  # 1-10
    cognitive_distortions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    reframe: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reframe_believability: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-10
    conversation_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("conversations.id"), nullable=True
    )

    def __repr__(self) -> str:
        return f"<ThoughtRecord '{self.automatic_thought[:30]}'>"
