"""Tests for SessionEngine orchestration layer."""

import pytest
import pytest_asyncio

from app.chat.flows.base import UserContext
from app.models.homework import Homework
from app.models.notification import PendingAction
from app.models.protocol import ProtocolEnrollment
from app.models.program import ProgramEnrollment
from app.models.screening import ScreeningResult
from app.models.user import User
from app.sessions.engine import SessionEngine


@pytest.fixture
def user_context(test_user: User) -> UserContext:
    return UserContext(user_id=str(test_user.id), user_name=test_user.name)


class TestTryHandle:
    """try_handle falls through when nothing active."""

    @pytest.mark.asyncio
    async def test_no_active_protocol_returns_none(self, test_user, user_context):
        engine = SessionEngine(test_user)
        result = await engine.try_handle("hello", user_context)
        assert result is None

    @pytest.mark.asyncio
    async def test_active_protocol_returns_none(self, test_user, user_context):
        """Active protocol enrollment still returns None (LLM handles content)."""
        await ProtocolEnrollment(
            user_id=str(test_user.id),
            protocol_id="cbt_depression",
            status="active",
        ).insert()

        engine = SessionEngine(test_user)
        result = await engine.try_handle("hello", user_context)
        assert result is None

    @pytest.mark.asyncio
    async def test_active_screening_flow_processes_input(self, test_user, user_context):
        """When a screening flow is active, input routes through it."""
        engine = SessionEngine(test_user)

        # Create a pending screening action and start session to init the flow
        await PendingAction(
            user_id=str(test_user.id),
            action_type="screening_due",
            data={"instrument": "phq9"},
        ).insert()

        # Start session to pick up the screening action
        start_result = await engine.handle_session_start(user_context)
        assert start_result is not None
        assert engine._active_screening_flow is not None

        # Now try_handle should route through the screening flow
        result = await engine.try_handle("Not at all", user_context)
        assert result is not None
        assert "message" in result


class TestHandleSessionStart:
    """handle_session_start returns proactive greetings."""

    @pytest.mark.asyncio
    async def test_pending_homework_returns_greeting(self, test_user, user_context):
        enrollment = await ProtocolEnrollment(
            user_id=str(test_user.id),
            protocol_id="cbt_depression",
            status="active",
        ).insert()

        await Homework(
            user_id=str(test_user.id),
            enrollment_id=str(enrollment.id),
            session_number=1,
            description="Write down three automatic thoughts",
            status="assigned",
        ).insert()

        engine = SessionEngine(test_user)
        result = await engine.handle_session_start(user_context)

        assert result is not None
        assert "Write down three automatic thoughts" in result["message"]

    @pytest.mark.asyncio
    async def test_pending_screening_action_starts_screening(
        self, test_user, user_context
    ):
        await PendingAction(
            user_id=str(test_user.id),
            action_type="screening_due",
            data={"instrument": "phq9"},
        ).insert()

        engine = SessionEngine(test_user)
        result = await engine.handle_session_start(user_context)

        assert result is not None
        assert engine._active_screening_flow is not None

        # Action should be dismissed
        action = await PendingAction.find_one(
            PendingAction.user_id == str(test_user.id),
            PendingAction.action_type == "screening_due",
        )
        assert action.dismissed is True

    @pytest.mark.asyncio
    async def test_active_protocol_next_session_ready(
        self, test_user, user_context
    ):
        await ProtocolEnrollment(
            user_id=str(test_user.id),
            protocol_id="cbt_depression",
            status="active",
            current_session_number=1,
        ).insert()

        engine = SessionEngine(test_user)
        result = await engine.handle_session_start(user_context)

        assert result is not None
        assert "session" in result["message"].lower() or "Session" in result["message"]

    @pytest.mark.asyncio
    async def test_nothing_pending_returns_none(self, test_user, user_context):
        engine = SessionEngine(test_user)
        result = await engine.handle_session_start(user_context)
        assert result is None


class TestEnroll:
    """enroll creates enrollment or blocks if conflicting."""

    @pytest.mark.asyncio
    async def test_enroll_creates_enrollment(self, test_user):
        engine = SessionEngine(test_user)
        enrollment = await engine.enroll("cbt_depression", "screening_123")

        assert enrollment is not None
        assert enrollment.protocol_id == "cbt_depression"
        assert enrollment.user_id == str(test_user.id)
        assert enrollment.entry_screening_id == "screening_123"
        assert enrollment.status == "enrolled"

    @pytest.mark.asyncio
    async def test_enroll_blocked_by_active_program(self, test_user):
        await ProgramEnrollment(
            user_id=str(test_user.id),
            program_id="belief_reset_7d",
            is_active=True,
        ).insert()

        engine = SessionEngine(test_user)
        enrollment = await engine.enroll("cbt_depression", "screening_123")
        assert enrollment is None

    @pytest.mark.asyncio
    async def test_enroll_blocked_by_active_protocol(self, test_user):
        await ProtocolEnrollment(
            user_id=str(test_user.id),
            protocol_id="anxiety",
            status="active",
        ).insert()

        engine = SessionEngine(test_user)
        enrollment = await engine.enroll("cbt_depression", "screening_123")
        assert enrollment is None

    @pytest.mark.asyncio
    async def test_enroll_allowed_if_program_inactive(self, test_user):
        await ProgramEnrollment(
            user_id=str(test_user.id),
            program_id="belief_reset_7d",
            is_active=False,
        ).insert()

        engine = SessionEngine(test_user)
        enrollment = await engine.enroll("cbt_depression", "screening_123")
        assert enrollment is not None


class TestOnScreeningComplete:
    """_on_screening_complete saves result and routes."""

    @pytest.mark.asyncio
    async def test_screening_complete_saves_result(self, test_user, user_context):
        engine = SessionEngine(test_user)

        # Start a screening via pending action
        await PendingAction(
            user_id=str(test_user.id),
            action_type="screening_due",
            data={"instrument": "phq9"},
        ).insert()

        await engine.handle_session_start(user_context)
        assert engine._active_screening_flow is not None

        # Answer all 9 PHQ-9 questions with "Not at all" (score 0 each)
        for i in range(9):
            result = await engine.try_handle("Not at all", user_context)
            assert result is not None

        # After 9 answers the screening should be complete
        # Check that a ScreeningResult was saved
        sr = await ScreeningResult.find_one(
            ScreeningResult.user_id == str(test_user.id)
        )
        assert sr is not None
        assert sr.instrument == "phq9"
        assert sr.status == "completed"
