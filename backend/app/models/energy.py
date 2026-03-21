from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, make_uuid


class EnergyReading(Base, TimestampMixin):
    __tablename__ = "energy_readings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    level: Mapped[int] = mapped_column(Integer)  # 1-10
    context: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime)

    def __repr__(self) -> str:
        return f"<EnergyReading level={self.level}>"
