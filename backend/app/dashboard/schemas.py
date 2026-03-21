from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MoodPoint(BaseModel):
    date: str
    score: int


class LifeAreaPoint(BaseModel):
    area: str
    score: float
    trend: str  # improving | stable | declining
    data_points: int


class HabitSummary(BaseModel):
    id: str
    name: str
    streak: int
    total_completions: int
    is_active: bool


class PatternSummary(BaseModel):
    id: str
    pattern_type: str
    description: str
    confidence: float
    actionable_insight: Optional[str] = None
    created_at: datetime


class SuggestionSummary(BaseModel):
    id: str
    content: str
    strategy_type: str
    life_area: str
    energy_required: int
    status: str
    effectiveness_rating: Optional[int] = None
    created_at: datetime


class DashboardSummary(BaseModel):
    # Mood
    current_mood: Optional[int] = None
    mood_trend: Optional[str] = None  # improving | stable | declining
    mood_data_points: list[MoodPoint] = []

    # Energy
    current_energy: Optional[int] = None
    avg_energy_7d: Optional[float] = None

    # Life Areas
    life_area_scores: list[LifeAreaPoint] = []

    # Habits
    active_habits: list[HabitSummary] = []

    # Patterns
    recent_patterns: list[PatternSummary] = []

    # Suggestions
    pending_suggestions: list[SuggestionSummary] = []
    suggestion_effectiveness: Optional[float] = None

    # Meta
    days_active: int = 0
    total_check_ins: int = 0
    last_check_in: Optional[datetime] = None


class MoodTrendResponse(BaseModel):
    data_points: list[MoodPoint]
    period_days: int
    average: Optional[float] = None
    trend: Optional[str] = None
