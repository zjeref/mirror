"""Dashboard service - aggregation queries for MongoDB."""

from datetime import datetime, timedelta, timezone

from app.dashboard.schemas import (
    DashboardSummary, HabitSummary, LifeAreaPoint,
    MoodPoint, MoodTrendResponse, PatternSummary, SuggestionSummary,
)
from app.models.check_in import CheckIn
from app.models.habit import Habit
from app.models.pattern import DetectedPattern
from app.models.suggestion import Suggestion
from app.models.user import User
from app.psychology.life_areas import calculate_life_area_scores


async def get_dashboard_summary(user: User) -> DashboardSummary:
    now = datetime.now(timezone.utc)
    user_id = str(user.id)

    latest_checkin = await CheckIn.find(
        CheckIn.user_id == user_id
    ).sort("-created_at").first_or_none()

    mood_data = await get_mood_trend(user_id, days=30)

    week_ago = now - timedelta(days=7)
    recent_checkins = await CheckIn.find(
        CheckIn.user_id == user_id,
        CheckIn.created_at >= week_ago,
    ).to_list()

    energy_scores = [c.energy_score for c in recent_checkins if c.energy_score]
    avg_energy = round(sum(energy_scores) / len(energy_scores), 1) if energy_scores else None

    area_snapshots = await calculate_life_area_scores(user_id)
    life_areas = [
        LifeAreaPoint(area=s.area, score=s.score, trend=s.trend, data_points=s.data_points)
        for s in area_snapshots
    ]

    habits = await Habit.find(Habit.user_id == user_id, Habit.is_active == True).to_list()
    habit_summaries = [
        HabitSummary(id=str(h.id), name=h.name, streak=h.current_streak,
                     total_completions=h.total_completions, is_active=h.is_active)
        for h in habits
    ]

    patterns = await DetectedPattern.find(
        DetectedPattern.user_id == user_id, DetectedPattern.is_active == True
    ).sort("-confidence").limit(5).to_list()
    pattern_summaries = [
        PatternSummary(
            id=str(p.id), pattern_type=p.pattern_type, description=p.description,
            confidence=p.confidence,
            actionable_insight=p.evidence.get("actionable_insight") if p.evidence else None,
            created_at=p.created_at,
        )
        for p in patterns
    ]

    pending = await Suggestion.find(
        Suggestion.user_id == user_id, Suggestion.status == "pending"
    ).sort("-created_at").limit(3).to_list()
    suggestion_summaries = [
        SuggestionSummary(
            id=str(s.id), content=s.content, strategy_type=s.strategy_type,
            life_area=s.life_area, energy_required=s.energy_required,
            status=s.status, effectiveness_rating=s.effectiveness_rating,
            created_at=s.created_at,
        )
        for s in pending
    ]

    completed_suggestions = await Suggestion.find(
        Suggestion.user_id == user_id,
        Suggestion.status == "completed",
        Suggestion.effectiveness_rating != None,
    ).to_list()
    effectiveness = None
    if completed_suggestions:
        good = sum(1 for s in completed_suggestions if s.effectiveness_rating >= 3)
        effectiveness = round(good / len(completed_suggestions), 2)

    first_checkin = await CheckIn.find(
        CheckIn.user_id == user_id
    ).sort("created_at").first_or_none()
    days_active = 0
    if first_checkin:
        days_active = (now - first_checkin.created_at.replace(tzinfo=timezone.utc)).days + 1

    total_checkins = await CheckIn.find(CheckIn.user_id == user_id).count()

    return DashboardSummary(
        current_mood=latest_checkin.mood_score if latest_checkin else None,
        mood_trend=mood_data.trend,
        mood_data_points=mood_data.data_points,
        current_energy=latest_checkin.energy_score if latest_checkin else None,
        avg_energy_7d=avg_energy,
        life_area_scores=life_areas,
        active_habits=habit_summaries,
        recent_patterns=pattern_summaries,
        pending_suggestions=suggestion_summaries,
        suggestion_effectiveness=effectiveness,
        days_active=days_active,
        total_check_ins=total_checkins,
        last_check_in=latest_checkin.created_at if latest_checkin else None,
    )


async def get_mood_trend(user_id: str, days: int = 30) -> MoodTrendResponse:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    check_ins = await CheckIn.find(
        CheckIn.user_id == user_id,
        CheckIn.created_at >= cutoff,
    ).sort("created_at").to_list()

    data_points = [
        MoodPoint(date=c.created_at.strftime("%Y-%m-%d"), score=c.mood_score)
        for c in check_ins
    ]

    scores = [c.mood_score for c in check_ins]
    average = round(sum(scores) / len(scores), 1) if scores else None

    trend = None
    if len(scores) >= 4:
        mid = len(scores) // 2
        first_half = sum(scores[:mid]) / mid
        second_half = sum(scores[mid:]) / (len(scores) - mid)
        diff = second_half - first_half
        trend = "improving" if diff >= 0.5 else "declining" if diff <= -0.5 else "stable"

    return MoodTrendResponse(data_points=data_points, period_days=days, average=average, trend=trend)
