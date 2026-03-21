from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, make_uuid


class LifeAreaScore(Base, TimestampMixin):
    __tablename__ = "life_area_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    area: Mapped[str] = mapped_column(String(50))  # physical | mental | career | habits
    score: Mapped[float] = mapped_column(Float)  # 0.0 - 10.0
    scored_at: Mapped[datetime] = mapped_column(DateTime)
    source: Mapped[str] = mapped_column(String(50))  # check_in | self_assessment | inferred

    def __repr__(self) -> str:
        return f"<LifeAreaScore {self.area}={self.score}>"
