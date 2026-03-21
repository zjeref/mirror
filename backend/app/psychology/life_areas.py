"""Life area tracking - multi-dimensional scoring across life domains."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy.orm import Session

from app.models.check_in import CheckIn
from app.models.life_area import LifeAreaScore


class LifeArea(str, Enum):
    PHYSICAL = "physical"
    MENTAL = "mental"
    CAREER = "career"
    HABITS = "habits"


@dataclass
class AreaSnapshot:
    area: str
    score: float
    trend: str  # improving | stable | declining
    data_points: int


def calculate_life_area_scores(
    db: Session, user_id: str, days: int = 30
) -> list[AreaSnapshot]:
    """Calculate current life area scores from recent check-ins and data."""
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    check_ins = (
        db.query(CheckIn)
        .filter(CheckIn.user_id == user_id, CheckIn.created_at >= cutoff)
        .order_by(CheckIn.created_at.desc())
        .all()
    )

    if not check_ins:
        return [
            AreaSnapshot(area=area.value, score=5.0, trend="stable", data_points=0)
            for area in LifeArea
        ]

    # Physical: derived from energy scores
    energy_scores = [c.energy_score for c in check_ins if c.energy_score]
    physical_score = sum(energy_scores) / len(energy_scores) if energy_scores else 5.0

    # Mental: derived from mood scores
    mood_scores = [c.mood_score for c in check_ins if c.mood_score]
    mental_score = sum(mood_scores) / len(mood_scores) if mood_scores else 5.0

    # Career/Habits: inferred from check-in frequency and intentions
    checkin_freq = len(check_ins) / max(days, 1) * 7  # check-ins per week
    habits_score = min(10, checkin_freq * 2)  # More check-ins = better habit score
    career_score = 5.0  # Default until we have career-specific data

    # Calculate trends (compare last 7 days vs previous 7)
    recent_cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    results = []
    for area, score, metric_scores in [
        (LifeArea.PHYSICAL, physical_score, energy_scores),
        (LifeArea.MENTAL, mental_score, mood_scores),
        (LifeArea.CAREER, career_score, []),
        (LifeArea.HABITS, habits_score, []),
    ]:
        trend = _calculate_trend(metric_scores, len(metric_scores) // 2)
        results.append(AreaSnapshot(
            area=area.value,
            score=round(score, 1),
            trend=trend,
            data_points=len(metric_scores),
        ))

    return results


def _calculate_trend(scores: list[float], split_point: int) -> str:
    """Calculate trend by comparing recent vs older scores."""
    if len(scores) < 4:
        return "stable"

    recent = scores[:split_point] if split_point > 0 else scores[:len(scores) // 2]
    older = scores[split_point:] if split_point > 0 else scores[len(scores) // 2:]

    if not recent or not older:
        return "stable"

    recent_avg = sum(recent) / len(recent)
    older_avg = sum(older) / len(older)
    diff = recent_avg - older_avg

    if diff >= 0.5:
        return "improving"
    elif diff <= -0.5:
        return "declining"
    return "stable"
