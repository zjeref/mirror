"""Life area tracking - multi-dimensional scoring across life domains."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

from app.models.check_in import CheckIn


class LifeArea(str, Enum):
    PHYSICAL = "physical"
    MENTAL = "mental"
    CAREER = "career"
    HABITS = "habits"


@dataclass
class AreaSnapshot:
    area: str
    score: float
    trend: str
    data_points: int


async def calculate_life_area_scores(user_id: str, days: int = 30) -> list[AreaSnapshot]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    check_ins = await CheckIn.find(
        CheckIn.user_id == user_id,
        CheckIn.created_at >= cutoff,
    ).sort("-created_at").to_list()

    if not check_ins:
        return [
            AreaSnapshot(area=area.value, score=5.0, trend="stable", data_points=0)
            for area in LifeArea
        ]

    energy_scores = [c.energy_score for c in check_ins if c.energy_score]
    physical_score = sum(energy_scores) / len(energy_scores) if energy_scores else 5.0

    mood_scores = [c.mood_score for c in check_ins if c.mood_score]
    mental_score = sum(mood_scores) / len(mood_scores) if mood_scores else 5.0

    checkin_freq = len(check_ins) / max(days, 1) * 7
    habits_score = min(10, checkin_freq * 2)
    career_score = 5.0

    results = []
    for area, score, metric_scores in [
        (LifeArea.PHYSICAL, physical_score, energy_scores),
        (LifeArea.MENTAL, mental_score, mood_scores),
        (LifeArea.CAREER, career_score, []),
        (LifeArea.HABITS, habits_score, []),
    ]:
        trend = _calculate_trend(metric_scores, len(metric_scores) // 2)
        results.append(AreaSnapshot(
            area=area.value, score=round(score, 1), trend=trend,
            data_points=len(metric_scores),
        ))
    return results


def _calculate_trend(scores: list[float], split_point: int) -> str:
    if len(scores) < 4:
        return "stable"
    recent = scores[:split_point] if split_point > 0 else scores[:len(scores) // 2]
    older = scores[split_point:] if split_point > 0 else scores[len(scores) // 2:]
    if not recent or not older:
        return "stable"
    diff = sum(recent) / len(recent) - sum(older) / len(older)
    if diff >= 0.5:
        return "improving"
    elif diff <= -0.5:
        return "declining"
    return "stable"
