import pytest
from datetime import datetime, timezone

from app.models.screening import ScreeningResult


@pytest.mark.asyncio
async def test_screening_history_with_one_completed(auth_client, test_user):
    """GET /api/screening/history with one completed screening returns list of 1."""
    screening = ScreeningResult(
        user_id=str(test_user.id),
        instrument="PHQ-9",
        item_scores=[1, 2, 1, 0, 3, 2, 1, 0, 1],
        total_score=11,
        severity_tier="moderate",
        status="completed",
        current_item=9,
        completed_at=datetime.now(timezone.utc),
    )
    await screening.insert()

    resp = await auth_client.get("/api/screening/history")
    assert resp.status_code == 200

    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["instrument"] == "PHQ-9"
    assert data[0]["total_score"] == 11
    assert data[0]["severity_tier"] == "moderate"
    assert data[0]["completed_at"] is not None


@pytest.mark.asyncio
async def test_screening_history_empty(auth_client, test_user):
    """GET /api/screening/history with no data returns empty list."""
    resp = await auth_client.get("/api/screening/history")
    assert resp.status_code == 200

    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_screening_history_excludes_in_progress(auth_client, test_user):
    """GET /api/screening/history excludes non-completed screenings."""
    screening = ScreeningResult(
        user_id=str(test_user.id),
        instrument="GAD-7",
        status="in_progress",
        current_item=3,
    )
    await screening.insert()

    resp = await auth_client.get("/api/screening/history")
    assert resp.status_code == 200
    assert len(resp.json()) == 0
