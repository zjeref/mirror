from datetime import datetime, timezone

from beanie.operators import In
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.dependencies import get_current_user
from app.models.homework import Homework
from app.models.protocol import ProtocolEnrollment, ProtocolSession
from app.models.user import User

router = APIRouter()


class CompleteHomeworkRequest(BaseModel):
    user_response: str = ""


@router.get("/protocols/current")
async def current_protocol(user: User = Depends(get_current_user)):
    """Return the user's active enrollment (enrolled/active/paused), or None."""
    enrollment = await ProtocolEnrollment.find_one(
        ProtocolEnrollment.user_id == str(user.id),
        In(ProtocolEnrollment.status, ["enrolled", "active", "paused"]),
    )
    if not enrollment:
        return None

    return {
        "id": str(enrollment.id),
        "protocol_id": enrollment.protocol_id,
        "current_session_number": enrollment.current_session_number,
        "status": enrollment.status,
        "entry_screening_id": enrollment.entry_screening_id,
        "screening_scores": enrollment.screening_scores,
        "start_date": enrollment.start_date.isoformat(),
        "end_date": enrollment.end_date.isoformat() if enrollment.end_date else None,
        "consecutive_homework_misses": enrollment.consecutive_homework_misses,
    }


@router.get("/protocols/history")
async def protocol_history(user: User = Depends(get_current_user)):
    """Return all enrollments sorted by start_date desc."""
    enrollments = await ProtocolEnrollment.find(
        ProtocolEnrollment.user_id == str(user.id),
    ).sort("-start_date").to_list()

    return [
        {
            "id": str(e.id),
            "protocol_id": e.protocol_id,
            "current_session_number": e.current_session_number,
            "status": e.status,
            "start_date": e.start_date.isoformat(),
            "end_date": e.end_date.isoformat() if e.end_date else None,
        }
        for e in enrollments
    ]


@router.get("/protocols/{enrollment_id}/sessions")
async def enrollment_sessions(
    enrollment_id: str, user: User = Depends(get_current_user)
):
    """Return sessions for an enrollment, verifying user ownership."""
    enrollment = await ProtocolEnrollment.get(enrollment_id)
    if not enrollment or enrollment.user_id != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found",
        )

    sessions = await ProtocolSession.find(
        ProtocolSession.enrollment_id == enrollment_id,
    ).sort("session_number").to_list()

    return [
        {
            "id": str(s.id),
            "session_number": s.session_number,
            "goals": s.goals,
            "activities_completed": s.activities_completed,
            "session_notes": s.session_notes,
            "outcome": s.outcome,
            "started_at": s.started_at.isoformat(),
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        }
        for s in sessions
    ]


@router.get("/homework/pending")
async def pending_homework(user: User = Depends(get_current_user)):
    """Return current pending homework (assigned/reminded)."""
    homework = await Homework.find_one(
        Homework.user_id == str(user.id),
        In(Homework.status, ["assigned", "reminded"]),
    )
    if not homework:
        return None

    return {
        "id": str(homework.id),
        "enrollment_id": homework.enrollment_id,
        "session_number": homework.session_number,
        "description": homework.description,
        "adaptive_tier": homework.adaptive_tier,
        "due_date": homework.due_date.isoformat() if homework.due_date else None,
        "status": homework.status,
        "reminder_count": homework.reminder_count,
    }


@router.post("/homework/{homework_id}/complete")
async def complete_homework(
    homework_id: str,
    body: CompleteHomeworkRequest,
    user: User = Depends(get_current_user),
):
    """Mark homework as complete and reset consecutive misses."""
    homework = await Homework.get(homework_id)
    if not homework or homework.user_id != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Homework not found",
        )

    if homework.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Homework already completed",
        )

    homework.status = "completed"
    homework.user_response = body.user_response
    homework.completed_at = datetime.now(timezone.utc)
    await homework.save()

    # Reset consecutive misses on the enrollment
    enrollment = await ProtocolEnrollment.get(homework.enrollment_id)
    if enrollment:
        enrollment.consecutive_homework_misses = 0
        await enrollment.save()

    return {
        "id": str(homework.id),
        "status": homework.status,
        "completed_at": homework.completed_at.isoformat(),
    }
