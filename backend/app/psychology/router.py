"""REST endpoints for suggestion feedback and habit logging."""

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies import get_current_user, get_db
from app.models.habit import Habit, HabitLog
from app.models.suggestion import Suggestion
from app.models.user import User

router = APIRouter()


class SuggestionFeedback(BaseModel):
    status: str  # accepted | rejected | completed
    effectiveness_rating: Optional[int] = None  # 1-5, only for completed


class HabitLogRequest(BaseModel):
    completed: bool
    version_done: Optional[str] = None  # tiny | full
    note: Optional[str] = None


class CreateHabitRequest(BaseModel):
    name: str
    anchor: str
    tiny_behavior: str
    full_behavior: Optional[str] = None
    celebration: Optional[str] = None
    life_area: str


@router.post("/suggestions/{suggestion_id}/feedback")
def suggestion_feedback(
    suggestion_id: str,
    feedback: SuggestionFeedback,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record feedback on a suggestion."""
    suggestion = (
        db.query(Suggestion)
        .filter(Suggestion.id == suggestion_id, Suggestion.user_id == user.id)
        .first()
    )
    if not suggestion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion not found")

    if feedback.status not in ("accepted", "rejected", "completed"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

    suggestion.status = feedback.status
    suggestion.responded_at = datetime.now(timezone.utc)

    if feedback.effectiveness_rating is not None:
        suggestion.effectiveness_rating = max(1, min(5, feedback.effectiveness_rating))

    db.commit()
    return {"status": "ok", "suggestion_id": suggestion_id}


@router.post("/habits", status_code=status.HTTP_201_CREATED)
def create_habit(
    request: CreateHabitRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new habit."""
    habit = Habit(
        user_id=user.id,
        name=request.name,
        anchor=request.anchor,
        tiny_behavior=request.tiny_behavior,
        full_behavior=request.full_behavior,
        celebration=request.celebration,
        life_area=request.life_area,
    )
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return {"id": habit.id, "name": habit.name}


@router.post("/habits/{habit_id}/log")
def log_habit(
    habit_id: str,
    request: HabitLogRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Log a habit completion for today."""
    habit = (
        db.query(Habit)
        .filter(Habit.id == habit_id, Habit.user_id == user.id)
        .first()
    )
    if not habit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")

    today = date.today()

    # Check for existing log today
    existing = (
        db.query(HabitLog)
        .filter(HabitLog.habit_id == habit_id, HabitLog.logged_date == today)
        .first()
    )
    if existing:
        existing.completed = request.completed
        existing.version_done = request.version_done
        existing.note = request.note
    else:
        log = HabitLog(
            habit_id=habit_id,
            completed=request.completed,
            version_done=request.version_done,
            note=request.note,
            logged_date=today,
        )
        db.add(log)

    # Update streak
    if request.completed:
        habit.total_completions += 1
        habit.current_streak += 1
        if habit.current_streak > habit.longest_streak:
            habit.longest_streak = habit.current_streak
    else:
        habit.current_streak = 0

    db.commit()
    return {
        "status": "ok",
        "habit_id": habit_id,
        "streak": habit.current_streak,
        "total_completions": habit.total_completions,
    }
