"""Activity tracking REST endpoints for Behavioral Activation."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.dependencies import get_current_user
from app.models.activity import Activity, UserValues
from app.models.user import User

router = APIRouter(prefix="/activities")


class ActivityCreate(BaseModel):
    name: str
    description: Optional[str] = None
    life_area: Optional[str] = None
    linked_value: Optional[str] = None
    mood_before: Optional[float] = None
    scheduled_for: Optional[datetime] = None


class ActivityComplete(BaseModel):
    mood_after: Optional[float] = None
    pleasure: Optional[float] = None
    mastery: Optional[float] = None


class ActivitySkip(BaseModel):
    reason: Optional[str] = None  # avoidance, practical_barrier, low_energy, forgot


@router.post("")
async def create_activity(body: ActivityCreate, user: User = Depends(get_current_user)):
    activity = Activity(
        user_id=str(user.id),
        name=body.name,
        description=body.description,
        life_area=body.life_area,
        linked_value=body.linked_value,
        mood_before=body.mood_before,
        scheduled_for=body.scheduled_for,
    )
    await activity.insert()
    return {"id": str(activity.id), "name": activity.name}


@router.post("/{activity_id}/complete")
async def complete_activity(
    activity_id: str, body: ActivityComplete, user: User = Depends(get_current_user)
):
    activity = await Activity.get(activity_id)
    if not activity or activity.user_id != str(user.id):
        return {"error": "Activity not found"}

    activity.completed = True
    activity.completed_at = datetime.now(timezone.utc)
    activity.mood_after = body.mood_after
    activity.pleasure = body.pleasure
    activity.mastery = body.mastery
    await activity.save()

    # Calculate mood delta for response
    mood_delta = None
    if activity.mood_before and activity.mood_after:
        mood_delta = activity.mood_after - activity.mood_before

    return {
        "id": str(activity.id),
        "completed": True,
        "mood_delta": mood_delta,
        "message": "Nice. Logged." + (
            f" Your mood went {'up' if mood_delta > 0 else 'down'} by {abs(mood_delta):.1f}."
            if mood_delta else ""
        ),
    }


@router.post("/{activity_id}/skip")
async def skip_activity(
    activity_id: str, body: ActivitySkip, user: User = Depends(get_current_user)
):
    activity = await Activity.get(activity_id)
    if not activity or activity.user_id != str(user.id):
        return {"error": "Activity not found"}

    activity.skipped = True
    activity.skip_reason = body.reason
    await activity.save()
    return {"id": str(activity.id), "skipped": True}


@router.get("")
async def list_activities(
    limit: int = 20, completed_only: bool = False,
    user: User = Depends(get_current_user),
):
    query = Activity.find(Activity.user_id == str(user.id))
    if completed_only:
        query = query.find(Activity.completed == True)

    activities = await query.sort("-created_at").limit(limit).to_list()
    return {
        "activities": [
            {
                "id": str(a.id),
                "name": a.name,
                "life_area": a.life_area,
                "mood_before": a.mood_before,
                "mood_after": a.mood_after,
                "pleasure": a.pleasure,
                "mastery": a.mastery,
                "completed": a.completed,
                "skipped": a.skipped,
                "linked_value": a.linked_value,
                "created_at": a.created_at.isoformat(),
            }
            for a in activities
        ],
    }


@router.get("/insights")
async def activity_insights(user: User = Depends(get_current_user)):
    """Get BA insights: which activities improve mood the most."""
    completed = await Activity.find(
        Activity.user_id == str(user.id),
        Activity.completed == True,
        Activity.mood_before != None,
        Activity.mood_after != None,
    ).sort("-created_at").limit(50).to_list()

    if len(completed) < 3:
        return {"message": "Need more completed activities to show insights.", "insights": []}

    # Calculate average mood delta per activity name
    by_name: dict[str, list[float]] = {}
    for a in completed:
        delta = a.mood_after - a.mood_before
        by_name.setdefault(a.name, []).append(delta)

    insights = []
    for name, deltas in sorted(by_name.items(), key=lambda x: sum(x[1]) / len(x[1]), reverse=True):
        avg = sum(deltas) / len(deltas)
        insights.append({
            "activity": name,
            "avg_mood_change": round(avg, 1),
            "times_done": len(deltas),
            "direction": "improves" if avg > 0 else "worsens",
        })

    # Overall stats
    all_deltas = [a.mood_after - a.mood_before for a in completed]
    avg_overall = sum(all_deltas) / len(all_deltas) if all_deltas else 0

    return {
        "total_activities": len(completed),
        "avg_mood_improvement": round(avg_overall, 1),
        "insights": insights[:10],
        "message": f"Across {len(completed)} activities, your mood changes by {avg_overall:+.1f} on average.",
    }


@router.get("/values")
async def get_values(user: User = Depends(get_current_user)):
    uv = await UserValues.find_one(UserValues.user_id == str(user.id))
    return {"values": uv.values if uv else {}}
