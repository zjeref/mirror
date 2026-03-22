from fastapi import APIRouter, Depends, Query

from app.dashboard.schemas import DashboardSummary, HabitSummary, MoodTrendResponse, PatternSummary
from app.dashboard.service import get_dashboard_summary, get_mood_trend
from app.dependencies import get_current_user
from app.models.habit import Habit
from app.models.pattern import DetectedPattern
from app.models.user import User
from app.psychology.life_areas import calculate_life_area_scores

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(user: User = Depends(get_current_user)):
    return await get_dashboard_summary(user)


@router.get("/mood-trends", response_model=MoodTrendResponse)
async def mood_trends(days: int = Query(default=30, le=365), user: User = Depends(get_current_user)):
    return await get_mood_trend(str(user.id), days=days)


@router.get("/life-areas")
async def life_areas(user: User = Depends(get_current_user)):
    return await calculate_life_area_scores(str(user.id))


@router.get("/patterns", response_model=list[PatternSummary])
async def patterns(user: User = Depends(get_current_user)):
    results = await DetectedPattern.find(
        DetectedPattern.user_id == str(user.id), DetectedPattern.is_active == True
    ).sort("-confidence").to_list()
    return [
        PatternSummary(
            id=str(p.id), pattern_type=p.pattern_type, description=p.description,
            confidence=p.confidence,
            actionable_insight=p.evidence.get("actionable_insight") if p.evidence else None,
            created_at=p.created_at,
        )
        for p in results
    ]


@router.get("/habits", response_model=list[HabitSummary])
async def habits(user: User = Depends(get_current_user)):
    results = await Habit.find(
        Habit.user_id == str(user.id), Habit.is_active == True
    ).sort("-current_streak").to_list()
    return [
        HabitSummary(id=str(h.id), name=h.name, streak=h.current_streak,
                     total_completions=h.total_completions, is_active=h.is_active)
        for h in results
    ]
