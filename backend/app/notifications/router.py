from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependencies import get_current_user
from app.models.notification import PendingAction
from app.models.user import User

router = APIRouter()


class UpdatePreferencesRequest(BaseModel):
    preferred_session_time: Optional[str] = None
    notification_enabled: Optional[bool] = None
    max_notifications_per_day: Optional[int] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class PushSubscriptionRequest(BaseModel):
    subscription: dict


@router.get("/preferences")
async def get_preferences(user: User = Depends(get_current_user)):
    """Return user's notification preferences."""
    return {
        "preferred_session_time": user.preferred_session_time,
        "notification_enabled": user.notification_enabled,
        "max_notifications_per_day": user.max_notifications_per_day,
        "quiet_hours_start": user.quiet_hours_start,
        "quiet_hours_end": user.quiet_hours_end,
    }


@router.put("/preferences")
async def update_preferences(
    body: UpdatePreferencesRequest,
    user: User = Depends(get_current_user),
):
    """Update allowed notification preference fields."""
    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    user.updated_at = datetime.now(timezone.utc)
    await user.save()

    return {
        "preferred_session_time": user.preferred_session_time,
        "notification_enabled": user.notification_enabled,
        "max_notifications_per_day": user.max_notifications_per_day,
        "quiet_hours_start": user.quiet_hours_start,
        "quiet_hours_end": user.quiet_hours_end,
    }


@router.post("/subscribe")
async def subscribe_push(
    body: PushSubscriptionRequest,
    user: User = Depends(get_current_user),
):
    """Save web push subscription to user."""
    user.push_subscription = body.subscription
    user.updated_at = datetime.now(timezone.utc)
    await user.save()

    return {"status": "subscribed"}


@router.get("/pending-actions")
async def pending_actions(user: User = Depends(get_current_user)):
    """Return undismissed actions sorted by priority."""
    actions = await PendingAction.find(
        PendingAction.user_id == str(user.id),
        PendingAction.dismissed == False,  # noqa: E712
    ).sort("priority").to_list()

    return [
        {
            "id": str(a.id),
            "action_type": a.action_type,
            "priority": a.priority,
            "data": a.data,
            "created_at": a.created_at.isoformat(),
            "expires_at": a.expires_at.isoformat() if a.expires_at else None,
        }
        for a in actions
    ]
