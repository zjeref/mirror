"""Tests for SessionEngine orchestration layer."""

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio

from app.chat.flows.base import UserContext
from app.models.conversation import Conversation, Message
from app.models.homework import Homework
from app.models.inferred_state import InferredStateRecord
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
    async def test_nothing_pending_returns_onboarding(self, test_user, user_context):
        """With no conversations, returns onboarding greeting (never None)."""
        engine = SessionEngine(test_user)
        result = await engine.handle_session_start(user_context)
        assert result is not None
        assert "Welcome to Mirror" in result["message"]


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


class TestProactiveOpener:
    """Tests for proactive conversation opener (priorities 4-7)."""

    @pytest.mark.asyncio
    async def test_session_start_pattern_alert_low_mood(self, test_user, user_context):
        """3 days of low mood_valence triggers direct mood alert."""
        now = datetime.now(timezone.utc)
        for i in range(3):
            await InferredStateRecord(
                user_id=str(test_user.id),
                mood_valence=2.5,
                confidence=0.5,
                created_at=now - timedelta(days=i),
            ).insert()

        # Need at least one conversation so it doesn't trigger onboarding
        conv = await Conversation(
            user_id=str(test_user.id), title="test"
        ).insert()
        await Message(
            conversation_id=str(conv.id),
            role="user",
            content="hello",
            created_at=now,
        ).insert()

        engine = SessionEngine(test_user)
        result = await engine.handle_session_start(user_context)

        assert result is not None
        assert "mood has been lower" in result["message"]
        assert "check in on" in result["message"]

    @pytest.mark.asyncio
    async def test_session_start_positive_trend(self, test_user, user_context):
        """3 days of improving mood triggers warm positive message."""
        now = datetime.now(timezone.utc)
        moods = [4.0, 5.5, 7.0]
        for i, mood in enumerate(moods):
            await InferredStateRecord(
                user_id=str(test_user.id),
                mood_valence=mood,
                confidence=0.5,
                created_at=now - timedelta(days=2 - i),  # oldest first
            ).insert()

        conv = await Conversation(
            user_id=str(test_user.id), title="test"
        ).insert()
        await Message(
            conversation_id=str(conv.id),
            role="user",
            content="hello",
            created_at=now,
        ).insert()

        engine = SessionEngine(test_user)
        result = await engine.handle_session_start(user_context)

        assert result is not None
        assert "good direction" in result["message"]

    @pytest.mark.asyncio
    async def test_session_start_contextual_same_day(self, test_user, user_context):
        """Message from today yields 'Hey again' greeting."""
        now = datetime.now(timezone.utc)
        conv = await Conversation(
            user_id=str(test_user.id), title="test"
        ).insert()
        await Message(
            conversation_id=str(conv.id),
            role="user",
            content="hello",
            created_at=now,
        ).insert()

        engine = SessionEngine(test_user)
        result = await engine.handle_session_start(user_context)

        assert result is not None
        assert "Hey again" in result["message"]

    @pytest.mark.asyncio
    async def test_session_start_contextual_week_away(self, test_user, user_context):
        """Message from 8 days ago yields 'been a while' greeting."""
        now = datetime.now(timezone.utc)
        conv = await Conversation(
            user_id=str(test_user.id), title="test"
        ).insert()
        await Message(
            conversation_id=str(conv.id),
            role="user",
            content="hello",
            created_at=now - timedelta(days=8),
        ).insert()

        engine = SessionEngine(test_user)
        result = await engine.handle_session_start(user_context)

        assert result is not None
        assert "been a while" in result["message"]

    @pytest.mark.asyncio
    async def test_session_start_onboarding_new_user(self, test_user, user_context):
        """User with no conversations gets welcome message + onboarding flag."""
        engine = SessionEngine(test_user)
        result = await engine.handle_session_start(user_context)

        assert result is not None
        assert "Welcome to Mirror" in result["message"]
        assert "5 minutes" in result["message"]
        assert engine._onboarding_pending is True

    @pytest.mark.asyncio
    async def test_onboarding_triggers_screening(self, test_user, user_context):
        """After onboarding greeting, next try_handle starts PHQ-9 screening."""
        engine = SessionEngine(test_user)

        # First: session start sends onboarding
        await engine.handle_session_start(user_context)
        assert engine._onboarding_pending is True

        # Second: user replies → triggers PHQ-9
        result = await engine.try_handle("Sure, let's do it", user_context)

        assert result is not None
        assert engine._onboarding_pending is False
        assert engine._active_screening_flow is not None
        assert engine._active_screening_flow.instrument.name == "phq9"

    @pytest.mark.asyncio
    async def test_session_start_never_returns_none(self, test_user, user_context):
        """handle_session_start never returns None for any user state."""
        # Case 1: New user (no conversations)
        engine = SessionEngine(test_user)
        result = await engine.handle_session_start(user_context)
        assert result is not None

        # Case 2: Returning user with conversation
        conv = await Conversation(
            user_id=str(test_user.id), title="test"
        ).insert()
        await Message(
            conversation_id=str(conv.id),
            role="user",
            content="hello",
            created_at=datetime.now(timezone.utc),
        ).insert()

        engine2 = SessionEngine(test_user)
        result2 = await engine2.handle_session_start(user_context)
        assert result2 is not None
