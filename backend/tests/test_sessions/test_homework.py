"""Tests for the adaptive homework system."""

from datetime import datetime, timezone

import pytest
import pytest_asyncio

from app.models.homework import Homework
from app.models.protocol import ProtocolEnrollment
from app.sessions.homework import HomeworkManager


# ---------------------------------------------------------------------------
# Mock protocol for testing (satisfies BaseProtocol interface)
# ---------------------------------------------------------------------------


class MockProtocol:
    """Fake protocol that returns tier-specific homework descriptions."""

    def get_homework(self, session_number: int, tier: str) -> str:
        return f"Session {session_number} homework ({tier})"


# ---------------------------------------------------------------------------
# Pure logic tests (no DB needed)
# ---------------------------------------------------------------------------


class TestDetermineTier:
    def test_zero_misses_returns_structured(self):
        assert HomeworkManager.determine_tier(0) == "structured"

    def test_one_miss_returns_gentle(self):
        assert HomeworkManager.determine_tier(1) == "gentle"

    def test_two_misses_returns_minimal(self):
        assert HomeworkManager.determine_tier(2) == "minimal"

    def test_three_misses_still_minimal(self):
        assert HomeworkManager.determine_tier(3) == "minimal"

    def test_large_number_returns_minimal(self):
        assert HomeworkManager.determine_tier(10) == "minimal"


class TestShouldPause:
    def test_two_misses_no_pause(self):
        assert HomeworkManager.should_pause(2) is False

    def test_three_misses_pause(self):
        assert HomeworkManager.should_pause(3) is True

    def test_four_misses_pause(self):
        assert HomeworkManager.should_pause(4) is True

    def test_zero_misses_no_pause(self):
        assert HomeworkManager.should_pause(0) is False


# ---------------------------------------------------------------------------
# DB integration tests
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def enrollment(test_user):
    """Create a ProtocolEnrollment for the test user."""
    e = ProtocolEnrollment(
        user_id=str(test_user.id),
        protocol_id="cbt_depression_v1",
        current_session_number=1,
        consecutive_homework_misses=0,
    )
    await e.insert()
    return e


@pytest.fixture
def protocol():
    return MockProtocol()


class TestAssign:
    @pytest.mark.asyncio
    async def test_assign_structured_tier(self, test_user, enrollment, protocol):
        enrollment.consecutive_homework_misses = 0
        hw = await HomeworkManager.assign(enrollment, protocol, session_number=1)

        assert hw.id is not None
        assert hw.user_id == str(test_user.id)
        assert hw.enrollment_id == str(enrollment.id)
        assert hw.session_number == 1
        assert hw.adaptive_tier == "structured"
        assert hw.status == "assigned"
        assert "structured" in hw.description

    @pytest.mark.asyncio
    async def test_assign_gentle_tier(self, test_user, enrollment, protocol):
        enrollment.consecutive_homework_misses = 1
        hw = await HomeworkManager.assign(enrollment, protocol, session_number=2)

        assert hw.adaptive_tier == "gentle"
        assert "gentle" in hw.description

    @pytest.mark.asyncio
    async def test_assign_minimal_tier(self, test_user, enrollment, protocol):
        enrollment.consecutive_homework_misses = 2
        hw = await HomeworkManager.assign(enrollment, protocol, session_number=3)

        assert hw.adaptive_tier == "minimal"
        assert "minimal" in hw.description


class TestComplete:
    @pytest.mark.asyncio
    async def test_complete_marks_homework(self, test_user, enrollment, protocol):
        hw = await HomeworkManager.assign(enrollment, protocol, session_number=1)
        completed = await HomeworkManager.complete(hw, user_response="I did the exercise")

        assert completed.status == "completed"
        assert completed.user_response == "I did the exercise"
        assert completed.completed_at is not None


class TestSkip:
    @pytest.mark.asyncio
    async def test_skip_increments_misses(self, test_user, enrollment, protocol):
        hw = await HomeworkManager.assign(enrollment, protocol, session_number=1)
        should_pause = await HomeworkManager.skip(hw, enrollment)

        assert hw.status == "skipped"
        # Reload enrollment from DB
        updated = await ProtocolEnrollment.get(enrollment.id)
        assert updated.consecutive_homework_misses == 1
        assert should_pause is False

    @pytest.mark.asyncio
    async def test_skip_triggers_pause_at_three(self, test_user, enrollment, protocol):
        enrollment.consecutive_homework_misses = 2
        await enrollment.save()

        hw = await HomeworkManager.assign(enrollment, protocol, session_number=1)
        should_pause = await HomeworkManager.skip(hw, enrollment)

        updated = await ProtocolEnrollment.get(enrollment.id)
        assert updated.consecutive_homework_misses == 3
        assert should_pause is True


class TestGetPending:
    @pytest.mark.asyncio
    async def test_get_pending_returns_assigned(self, test_user, enrollment, protocol):
        hw = await HomeworkManager.assign(enrollment, protocol, session_number=1)
        pending = await HomeworkManager.get_pending(str(test_user.id))

        assert pending is not None
        assert pending.id == hw.id

    @pytest.mark.asyncio
    async def test_get_pending_returns_none_when_completed(
        self, test_user, enrollment, protocol
    ):
        hw = await HomeworkManager.assign(enrollment, protocol, session_number=1)
        await HomeworkManager.complete(hw, "done")

        pending = await HomeworkManager.get_pending(str(test_user.id))
        assert pending is None

    @pytest.mark.asyncio
    async def test_get_pending_returns_none_when_no_homework(self, test_user):
        pending = await HomeworkManager.get_pending(str(test_user.id))
        assert pending is None
