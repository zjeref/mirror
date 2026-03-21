"""Dashboard REST endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dashboard.schemas import DashboardSummary, HabitSummary, MoodTrendResponse, PatternSummary
from app.dashboard.service import get_dashboard_summary, get_mood_trend
from app.dependencies import get_current_user, get_db
from app.models.habit import Habit
from app.models.pattern import DetectedPattern
from app.models.user import User

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get complete dashboard summary."""
    return get_dashboard_summary(db, user)


@router.get("/mood-trends", response_model=MoodTrendResponse)
def mood_trends(
    days: int = Query(default=30, le=365),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get mood trend data for charting."""
    return get_mood_trend(db, user.id, days=days)


@router.get("/life-areas")
def life_areas(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current life area scores."""
    from app.psychology.life_areas import calculate_life_area_scores

    return calculate_life_area_scores(db, user.id)


@router.get("/patterns", response_model=list[PatternSummary])
def patterns(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detected patterns."""
    results = (
        db.query(DetectedPattern)
        .filter(DetectedPattern.user_id == user.id, DetectedPattern.is_active == True)
        .order_by(DetectedPattern.confidence.desc())
        .all()
    )
    return [
        PatternSummary(
            id=p.id,
            pattern_type=p.pattern_type,
            description=p.description,
            confidence=p.confidence,
            actionable_insight=p.evidence.get("actionable_insight") if p.evidence else None,
            created_at=p.created_at,
        )
        for p in results
    ]


@router.get("/habits", response_model=list[HabitSummary])
def habits(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get active habits with streaks."""
    results = (
        db.query(Habit)
        .filter(Habit.user_id == user.id, Habit.is_active == True)
        .order_by(Habit.current_streak.desc())
        .all()
    )
    return [
        HabitSummary(
            id=h.id,
            name=h.name,
            streak=h.current_streak,
            total_completions=h.total_completions,
            is_active=h.is_active,
        )
        for h in results
    ]
