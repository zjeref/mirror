import pytest
from datetime import datetime, timezone

from app.models.protocol import ProtocolEnrollment
from app.models.homework import Homework


@pytest.mark.asyncio
async def test_current_protocol_none(auth_client, test_user):
    """GET /api/protocols/current with no active protocol returns null."""
    resp = await auth_client.get("/api/protocols/current")
    assert resp.status_code == 200
    assert resp.json() is None


@pytest.mark.asyncio
async def test_current_protocol_with_active_enrollment(auth_client, test_user):
    """GET /api/protocols/current with active enrollment returns enrollment data."""
    enrollment = ProtocolEnrollment(
        user_id=str(test_user.id),
        protocol_id="ba_protocol_v1",
        current_session_number=2,
        status="active",
        entry_screening_id="some-screening-id",
        screening_scores=[{"instrument": "PHQ-9", "score": 14}],
        consecutive_homework_misses=1,
    )
    await enrollment.insert()

    resp = await auth_client.get("/api/protocols/current")
    assert resp.status_code == 200

    data = resp.json()
    assert data is not None
    assert data["protocol_id"] == "ba_protocol_v1"
    assert data["current_session_number"] == 2
    assert data["status"] == "active"
    assert data["entry_screening_id"] == "some-screening-id"
    assert data["consecutive_homework_misses"] == 1
    assert data["start_date"] is not None


@pytest.mark.asyncio
async def test_current_protocol_ignores_completed(auth_client, test_user):
    """GET /api/protocols/current ignores completed enrollments."""
    enrollment = ProtocolEnrollment(
        user_id=str(test_user.id),
        protocol_id="ba_protocol_v1",
        status="completed",
        end_date=datetime.now(timezone.utc),
    )
    await enrollment.insert()

    resp = await auth_client.get("/api/protocols/current")
    assert resp.status_code == 200
    assert resp.json() is None


@pytest.mark.asyncio
async def test_complete_homework(auth_client, test_user):
    """POST /api/homework/{id}/complete marks homework completed and resets miss counter."""
    enrollment = ProtocolEnrollment(
        user_id=str(test_user.id),
        protocol_id="ba_protocol_v1",
        status="active",
        consecutive_homework_misses=2,
    )
    await enrollment.insert()

    homework = Homework(
        user_id=str(test_user.id),
        enrollment_id=str(enrollment.id),
        session_number=1,
        description="Practice deep breathing for 5 minutes",
        status="assigned",
    )
    await homework.insert()

    resp = await auth_client.post(
        f"/api/homework/{homework.id}/complete",
        json={"user_response": "Did the breathing exercise, felt calmer."},
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data["status"] == "completed"
    assert data["completed_at"] is not None

    # Verify enrollment miss counter was reset
    updated_enrollment = await ProtocolEnrollment.get(enrollment.id)
    assert updated_enrollment.consecutive_homework_misses == 0


@pytest.mark.asyncio
async def test_complete_homework_not_found(auth_client, test_user):
    """POST /api/homework/{id}/complete with invalid id returns 404."""
    resp = await auth_client.post(
        "/api/homework/000000000000000000000000/complete",
        json={},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_complete_homework_already_completed(auth_client, test_user):
    """POST /api/homework/{id}/complete on already completed homework returns 400."""
    enrollment = ProtocolEnrollment(
        user_id=str(test_user.id),
        protocol_id="ba_protocol_v1",
        status="active",
    )
    await enrollment.insert()

    homework = Homework(
        user_id=str(test_user.id),
        enrollment_id=str(enrollment.id),
        session_number=1,
        description="Journal entry",
        status="completed",
        completed_at=datetime.now(timezone.utc),
    )
    await homework.insert()

    resp = await auth_client.post(
        f"/api/homework/{homework.id}/complete",
        json={},
    )
    assert resp.status_code == 400
