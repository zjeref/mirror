from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.dependencies import get_current_user
from app.models.habit import Habit, HabitLog
from app.models.suggestion import Suggestion
from app.models.user import User

router = APIRouter()


class SuggestionFeedback(BaseModel):
    status: str
    effectiveness_rating: Optional[int] = None


class HabitLogRequest(BaseModel):
    completed: bool
    version_done: Optional[str] = None
    note: Optional[str] = None


class CreateHabitRequest(BaseModel):
    name: str
    anchor: str
    tiny_behavior: str
    full_behavior: Optional[str] = None
    celebration: Optional[str] = None
    life_area: str


@router.post("/suggestions/{suggestion_id}/feedback")
async def suggestion_feedback(
    suggestion_id: str,
    feedback: SuggestionFeedback,
    user: User = Depends(get_current_user),
):
    suggestion = await Suggestion.get(suggestion_id)
    if not suggestion or suggestion.user_id != str(user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion not found")

    if feedback.status not in ("accepted", "rejected", "completed"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

    suggestion.status = feedback.status
    suggestion.responded_at = datetime.now(timezone.utc)
    if feedback.effectiveness_rating is not None:
        suggestion.effectiveness_rating = max(1, min(5, feedback.effectiveness_rating))
    await suggestion.save()

    return {"status": "ok", "suggestion_id": suggestion_id}


@router.post("/habits", status_code=status.HTTP_201_CREATED)
async def create_habit(request: CreateHabitRequest, user: User = Depends(get_current_user)):
    habit = Habit(
        user_id=str(user.id),
        name=request.name,
        anchor=request.anchor,
        tiny_behavior=request.tiny_behavior,
        full_behavior=request.full_behavior,
        celebration=request.celebration,
        life_area=request.life_area,
    )
    await habit.insert()
    return {"id": str(habit.id), "name": habit.name}


@router.post("/habits/{habit_id}/log")
async def log_habit(
    habit_id: str,
    request: HabitLogRequest,
    user: User = Depends(get_current_user),
):
    habit = await Habit.get(habit_id)
    if not habit or habit.user_id != str(user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")

    today = date.today()
    existing = await HabitLog.find_one(HabitLog.habit_id == str(habit.id), HabitLog.logged_date == today)

    if existing:
        existing.completed = request.completed
        existing.version_done = request.version_done
        existing.note = request.note
        await existing.save()
    else:
        log = HabitLog(
            habit_id=str(habit.id),
            completed=request.completed,
            version_done=request.version_done,
            note=request.note,
            logged_date=today,
        )
        await log.insert()

    if request.completed:
        habit.total_completions += 1
        habit.current_streak += 1
        if habit.current_streak > habit.longest_streak:
            habit.longest_streak = habit.current_streak
    else:
        habit.current_streak = 0
    await habit.save()

    return {
        "status": "ok",
        "habit_id": habit_id,
        "streak": habit.current_streak,
        "total_completions": habit.total_completions,
    }
