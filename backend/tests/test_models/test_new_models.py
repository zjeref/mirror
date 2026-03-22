import pytest
from datetime import datetime, timezone, timedelta

from beanie.operators import In

from app.models.screening import ScreeningResult
from app.models.protocol import ProtocolEnrollment, ProtocolSession
from app.models.homework import Homework
from app.models.notification import PendingAction


class TestScreeningResult:
    @pytest.mark.asyncio
    async def test_create_screening_result(self):
        sr = ScreeningResult(
            user_id="user-1",
            instrument="phq9",
            item_scores=[1, 2, 1, 0, 3, 2, 1, 0, 1],
            total_score=11,
            severity_tier="moderate",
            status="completed",
            current_item=9,
        )
        await sr.insert()
        found = await ScreeningResult.get(sr.id)
        assert found.instrument == "phq9"
        assert found.total_score == 11
        assert found.severity_tier == "moderate"

    @pytest.mark.asyncio
    async def test_in_progress_screening(self):
        sr = ScreeningResult(
            user_id="user-1",
            instrument="gad7",
            item_scores=[2, 1],
            total_score=3,
            severity_tier="",
            status="in_progress",
            current_item=2,
        )
        await sr.insert()
        found = await ScreeningResult.get(sr.id)
        assert found.status == "in_progress"
        assert found.current_item == 2

    @pytest.mark.asyncio
    async def test_find_user_screenings(self):
        for i in range(3):
            await ScreeningResult(
                user_id="user-1",
                instrument="phq9",
                item_scores=[1] * 9,
                total_score=9,
                severity_tier="mild",
                status="completed",
                current_item=9,
            ).insert()
        results = await ScreeningResult.find(
            ScreeningResult.user_id == "user-1"
        ).to_list()
        assert len(results) == 3


class TestProtocolEnrollment:
    @pytest.mark.asyncio
    async def test_create_enrollment(self):
        pe = ProtocolEnrollment(
            user_id="user-1",
            protocol_id="cbt_depression",
            current_session_number=1,
            status="enrolled",
        )
        await pe.insert()
        found = await ProtocolEnrollment.get(pe.id)
        assert found.protocol_id == "cbt_depression"
        assert found.status == "enrolled"

    @pytest.mark.asyncio
    async def test_find_active_enrollment(self):
        await ProtocolEnrollment(
            user_id="user-1",
            protocol_id="cbt_depression",
            current_session_number=3,
            status="active",
        ).insert()
        active = await ProtocolEnrollment.find_one(
            ProtocolEnrollment.user_id == "user-1",
            In(ProtocolEnrollment.status, ["enrolled", "active", "paused"]),
        )
        assert active is not None
        assert active.status == "active"


class TestHomework:
    @pytest.mark.asyncio
    async def test_create_homework(self):
        hw = Homework(
            user_id="user-1",
            enrollment_id="enroll-1",
            session_number=1,
            description="Mood monitoring for 3 days",
            adaptive_tier="structured",
        )
        await hw.insert()
        found = await Homework.get(hw.id)
        assert found.adaptive_tier == "structured"
        assert found.status == "assigned"


class TestPendingAction:
    @pytest.mark.asyncio
    async def test_create_pending_action(self):
        pa = PendingAction(
            user_id="user-1",
            action_type="screening_due",
            priority=3,
            data={"instrument": "phq9"},
        )
        await pa.insert()
        found = await PendingAction.get(pa.id)
        assert found.action_type == "screening_due"
