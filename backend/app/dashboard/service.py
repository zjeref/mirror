"""Dashboard service - aggregation queries for dashboard data."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dashboard.schemas import (
    DashboardSummary,
    HabitSummary,
    LifeAreaPoint,
    MoodPoint,
    MoodTrendResponse,
    PatternSummary,
    SuggestionSummary,
)
from app.models.check_in import CheckIn
from app.models.habit import Habit
from app.models.pattern import DetectedPattern
from app.models.suggestion import Suggestion
from app.models.user import User
from app.psychology.life_areas import calculate_life_area_scores


def get_dashboard_summary(db: Session, user: User) -> DashboardSummary:
    """Build the complete dashboard summary for a user."""
    now = datetime.now(timezone.utc)

    # Latest check-in
    latest_checkin = (
        db.query(CheckIn)
        .filter(CheckIn.user_id == user.id)
        .order_by(CheckIn.created_at.desc())
        .first()
    )

    # Mood data points (last 30 days)
    mood_data = get_mood_trend(db, user.id, days=30)

    # Energy average (7 days)
    week_ago = now - timedelta(days=7)
    recent_checkins = (
        db.query(CheckIn)
        .filter(CheckIn.user_id == user.id, CheckIn.created_at >= week_ago)
        .all()
    )
    energy_scores = [c.energy_score for c in recent_checkins if c.energy_score]
    avg_energy = round(sum(energy_scores) / len(energy_scores), 1) if energy_scores else None

    # Life area scores
    area_snapshots = calculate_life_area_scores(db, user.id)
    life_areas = [
        LifeAreaPoint(
            area=s.area,
            score=s.score,
            trend=s.trend,
            data_points=s.data_points,
        )
        for s in area_snapshots
    ]

    # Active habits
    habits = (
        db.query(Habit)
        .filter(Habit.user_id == user.id, Habit.is_active == True)
        .all()
    )
    habit_summaries = [
        HabitSummary(
            id=h.id,
            name=h.name,
            streak=h.current_streak,
            total_completions=h.total_completions,
            is_active=h.is_active,
        )
        for h in habits
    ]

    # Recent patterns
    patterns = (
        db.query(DetectedPattern)
        .filter(DetectedPattern.user_id == user.id, DetectedPattern.is_active == True)
        .order_by(DetectedPattern.confidence.desc())
        .limit(5)
        .all()
    )
    pattern_summaries = [
        PatternSummary(
            id=p.id,
            pattern_type=p.pattern_type,
            description=p.description,
            confidence=p.confidence,
            actionable_insight=p.evidence.get("actionable_insight") if p.evidence else None,
            created_at=p.created_at,
        )
        for p in patterns
    ]

    # Pending suggestions
    pending = (
        db.query(Suggestion)
        .filter(Suggestion.user_id == user.id, Suggestion.status == "pending")
        .order_by(Suggestion.created_at.desc())
        .limit(3)
        .all()
    )
    suggestion_summaries = [
        SuggestionSummary(
            id=s.id,
            content=s.content,
            strategy_type=s.strategy_type,
            life_area=s.life_area,
            energy_required=s.energy_required,
            status=s.status,
            effectiveness_rating=s.effectiveness_rating,
            created_at=s.created_at,
        )
        for s in pending
    ]

    # Suggestion effectiveness (% of completed suggestions rated 3+/5)
    completed_suggestions = (
        db.query(Suggestion)
        .filter(
            Suggestion.user_id == user.id,
            Suggestion.status == "completed",
            Suggestion.effectiveness_rating.isnot(None),
        )
        .all()
    )
    if completed_suggestions:
        good = sum(1 for s in completed_suggestions if s.effectiveness_rating >= 3)
        effectiveness = round(good / len(completed_suggestions), 2)
    else:
        effectiveness = None

    # Days active
    first_checkin = (
        db.query(CheckIn)
        .filter(CheckIn.user_id == user.id)
        .order_by(CheckIn.created_at.asc())
        .first()
    )
    days_active = 0
    if first_checkin:
        days_active = (now - first_checkin.created_at.replace(tzinfo=timezone.utc)).days + 1

    total_checkins = db.query(CheckIn).filter(CheckIn.user_id == user.id).count()

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


def get_mood_trend(db: Session, user_id: str, days: int = 30) -> MoodTrendResponse:
    """Get mood trend data for charting."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    check_ins = (
        db.query(CheckIn)
        .filter(CheckIn.user_id == user_id, CheckIn.created_at >= cutoff)
        .order_by(CheckIn.created_at.asc())
        .all()
    )

    data_points = [
        MoodPoint(
            date=c.created_at.strftime("%Y-%m-%d"),
            score=c.mood_score,
        )
        for c in check_ins
    ]

    scores = [c.mood_score for c in check_ins]
    average = round(sum(scores) / len(scores), 1) if scores else None

    # Trend: compare first half vs second half
    trend = None
    if len(scores) >= 4:
        mid = len(scores) // 2
        first_half = sum(scores[:mid]) / mid
        second_half = sum(scores[mid:]) / (len(scores) - mid)
        diff = second_half - first_half
        if diff >= 0.5:
            trend = "improving"
        elif diff <= -0.5:
            trend = "declining"
        else:
            trend = "stable"

    return MoodTrendResponse(
        data_points=data_points,
        period_days=days,
        average=average,
        trend=trend,
    )
