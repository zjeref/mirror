"""Tests for mid-protocol re-screening and protocol switching."""

import pytest
import pytest_asyncio

from app.models.protocol import ProtocolEnrollment
from app.models.user import User
from app.sessions.engine import SessionEngine


class TestCheckMidProtocolScreening:
    """check_mid_protocol_screening detects when re-screening is due."""

    @pytest.mark.asyncio
    async def test_returns_true_at_mid_screening_session(self, test_user):
        """CBT mid_screening_session=4, so session 4 should trigger."""
        enrollment = ProtocolEnrollment(
            user_id=str(test_user.id),
            protocol_id="cbt_depression",
            current_session_number=4,
            status="active",
        )
        await enrollment.insert()

        engine = SessionEngine(test_user)
        result = await engine.check_mid_protocol_screening(enrollment)
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_at_non_screening_session(self, test_user):
        """Session 2 is not the mid-screening point for CBT."""
        enrollment = ProtocolEnrollment(
            user_id=str(test_user.id),
            protocol_id="cbt_depression",
            current_session_number=2,
            status="active",
        )
        await enrollment.insert()

        engine = SessionEngine(test_user)
        result = await engine.check_mid_protocol_screening(enrollment)
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_for_unknown_protocol(self, test_user):
        """Unknown protocol_id should return False."""
        enrollment = ProtocolEnrollment(
            user_id=str(test_user.id),
            protocol_id="nonexistent",
            current_session_number=4,
            status="active",
        )
        await enrollment.insert()

        engine = SessionEngine(test_user)
        result = await engine.check_mid_protocol_screening(enrollment)
        assert result is False


class TestSwitchProtocol:
    """switch_protocol transitions enrollment from one protocol to another."""

    @pytest.mark.asyncio
    async def test_switch_cbt_to_ba_skips_sessions(self, test_user):
        """Switching CBT->BA should skip sessions 1,2 and start at 3."""
        old_enrollment = ProtocolEnrollment(
            user_id=str(test_user.id),
            protocol_id="cbt_depression",
            current_session_number=4,
            status="active",
            entry_screening_id="scr_123",
            screening_scores=[{"instrument": "phq9", "score": 14}],
        )
        await old_enrollment.insert()

        engine = SessionEngine(test_user)
        new_enrollment = await engine.switch_protocol(
            old_enrollment, "behavioral_activation"
        )

        # New enrollment exists and starts at session 3
        assert new_enrollment is not None
        assert new_enrollment.protocol_id == "behavioral_activation"
        assert new_enrollment.current_session_number == 3
        assert new_enrollment.status == "enrolled"
        assert new_enrollment.user_id == str(test_user.id)
        assert new_enrollment.entry_screening_id == "scr_123"
        assert new_enrollment.screening_scores == [
            {"instrument": "phq9", "score": 14}
        ]

        # Old enrollment is marked as switched
        await old_enrollment.sync()
        assert old_enrollment.status == "switched"
        assert old_enrollment.switched_to_enrollment_id == str(new_enrollment.id)
        assert old_enrollment.end_date is not None

    @pytest.mark.asyncio
    async def test_switch_to_unknown_protocol_returns_none(self, test_user):
        """Switching to a nonexistent protocol returns None."""
        enrollment = ProtocolEnrollment(
            user_id=str(test_user.id),
            protocol_id="cbt_depression",
            current_session_number=4,
            status="active",
        )
        await enrollment.insert()

        engine = SessionEngine(test_user)
        result = await engine.switch_protocol(enrollment, "nonexistent")
        assert result is None

        # Original enrollment unchanged
        await enrollment.sync()
        assert enrollment.status == "active"
