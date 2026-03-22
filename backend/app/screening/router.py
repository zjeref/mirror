from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.models.screening import ScreeningResult
from app.models.user import User

router = APIRouter()


@router.get("/history")
async def screening_history(user: User = Depends(get_current_user)):
    """Return user's completed screening results, sorted by date desc."""
    results = await ScreeningResult.find(
        ScreeningResult.user_id == str(user.id),
        ScreeningResult.status == "completed",
    ).sort("-created_at").to_list()

    return [
        {
            "id": str(r.id),
            "instrument": r.instrument,
            "total_score": r.total_score,
            "severity_tier": r.severity_tier,
            "created_at": r.created_at.isoformat(),
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "linked_enrollment_id": r.linked_enrollment_id,
        }
        for r in results
    ]


@router.get("/{screening_id}")
async def get_screening(screening_id: str, user: User = Depends(get_current_user)):
    """Return a single screening detail, verifying user ownership."""
    result = await ScreeningResult.get(screening_id)
    if not result or result.user_id != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screening result not found",
        )

    return {
        "id": str(result.id),
        "instrument": result.instrument,
        "item_scores": result.item_scores,
        "total_score": result.total_score,
        "severity_tier": result.severity_tier,
        "status": result.status,
        "current_item": result.current_item,
        "linked_enrollment_id": result.linked_enrollment_id,
        "created_at": result.created_at.isoformat(),
        "completed_at": result.completed_at.isoformat() if result.completed_at else None,
    }
