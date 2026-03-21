from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, make_uuid


class Habit(Base, TimestampMixin):
    __tablename__ = "habits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    anchor: Mapped[str] = mapped_column(Text)  # "After I pour my morning coffee"
    tiny_behavior: Mapped[str] = mapped_column(Text)  # "I will do 2 pushups"
    full_behavior: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    celebration: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    life_area: Mapped[str] = mapped_column(String(50))  # physical | mental | career | habits
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    total_completions: Mapped[int] = mapped_column(Integer, default=0)

    logs = relationship("HabitLog", back_populates="habit", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Habit '{self.name}' streak={self.current_streak}>"


class HabitLog(Base, TimestampMixin):
    __tablename__ = "habit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_uuid)
    habit_id: Mapped[str] = mapped_column(String(36), ForeignKey("habits.id"), index=True)
    completed: Mapped[bool] = mapped_column(Boolean)
    version_done: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # tiny | full
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logged_date: Mapped[date] = mapped_column(Date, index=True)

    habit = relationship("Habit", back_populates="logs")

    def __repr__(self) -> str:
        return f"<HabitLog {self.logged_date} completed={self.completed}>"
