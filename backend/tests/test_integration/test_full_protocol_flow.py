"""End-to-end integration test: low mood → screening → protocol enrollment.

Scenario:
  3 days low mood → screening triggered → PHQ-9 moderate →
  CBT protocol offered → user enrolls → session 1 greeting
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.chat.flows.base import UserContext
from app.models.inferred_state import InferredStateRecord
from app.models.notification import PendingAction
from app.models.screening import ScreeningResult
from app.models.protocol import ProtocolEnrollment
from app.psychology.severity import SeverityRouter
from app.sessions.engine import SessionEngine
from app.tasks.screening_triggers import check_screening_triggers


# PHQ-9 response labels (index = score value)
_SCORE_LABELS = {
    0: "Not at all",
    1: "Several days",
    2: "More than half the days",
    3: "Nearly every day",
}

# 9 answers totalling 12 (moderate range 10-14)
_PHQ9_SCORES = [2, 1, 1, 1, 2, 1, 1, 2, 1]


@pytest.mark.asyncio
async def test_full_protocol_flow(test_user):
    """3 days low mood → PHQ-9 screening → moderate → CBT enroll → session 1."""
    user_id = str(test_user.id)
    context = UserContext(user_id=user_id, user_name=test_user.name)

    # ------------------------------------------------------------------
    # Step 1: Create 3 InferredStateRecords with low mood over 3 days
    # ------------------------------------------------------------------
    now = datetime.now(timezone.utc)
    for day_offset in range(3):
        record = InferredStateRecord(
            user_id=user_id,
            mood_valence=2.5,
            confidence=0.8,
            themes=[],
            created_at=now - timedelta(days=day_offset, hours=1),
        )
        await record.insert()

    # ------------------------------------------------------------------
    # Step 2: check_screening_triggers → should return "phq9"
    # ------------------------------------------------------------------
    instrument = await check_screening_triggers(user_id)
    assert instrument == "phq9", f"Expected 'phq9', got {instrument!r}"

    # ------------------------------------------------------------------
    # Step 3: Verify PendingAction created for screening_due
    # ------------------------------------------------------------------
    action = await PendingAction.find_one(
        PendingAction.user_id == user_id,
        PendingAction.action_type == "screening_due",
        PendingAction.dismissed == False,  # noqa: E712
    )
    assert action is not None, "PendingAction for screening_due not created"
    assert action.data["instrument"] == "phq9"

    # ------------------------------------------------------------------
    # Step 4: SessionEngine.handle_session_start → starts screening flow
    # ------------------------------------------------------------------
    engine = SessionEngine(test_user)
    start_response = await engine.handle_session_start(context)

    assert start_response is not None, "handle_session_start returned None"
    assert start_response["source"] == "session_engine"
    assert "PHQ-9" in start_response["message"]
    # The screening flow should now be active
    assert engine._active_screening_flow is not None
    assert not engine._active_screening_flow.is_complete

    # PendingAction should now be dismissed
    action = await PendingAction.find_one(
        PendingAction.user_id == user_id,
        PendingAction.action_type == "screening_due",
    )
    assert action.dismissed is True

    # ------------------------------------------------------------------
    # Step 5: Complete PHQ-9 — process 9 answers one at a time
    # ------------------------------------------------------------------
    for i, score_val in enumerate(_PHQ9_SCORES):
        answer = _SCORE_LABELS[score_val]
        response = await engine.try_handle(answer, context)
        assert response is not None, f"try_handle returned None on item {i}"

        if i < 8:
            # Not the last question — flow should still be active
            assert engine._active_screening_flow is not None or i == 8
        # On the last answer (i=8), try_handle calls _on_screening_complete
        # internally because the flow becomes complete

    # ------------------------------------------------------------------
    # Step 6: Verify ScreeningResult saved correctly
    # ------------------------------------------------------------------
    screening = await ScreeningResult.find_one(
        ScreeningResult.user_id == user_id,
        ScreeningResult.instrument == "phq9",
        ScreeningResult.status == "completed",
    )
    assert screening is not None, "ScreeningResult not saved"
    assert screening.total_score == 12, f"Expected total 12, got {screening.total_score}"
    assert screening.severity_tier == "moderate"
    assert screening.item_scores == _PHQ9_SCORES
    assert screening.completed_at is not None

    # ------------------------------------------------------------------
    # Step 7: SeverityRouter confirms moderate → recommend_protocol
    # ------------------------------------------------------------------
    decision = SeverityRouter.route("phq9", 12)
    assert decision.action == "recommend_protocol"
    assert "cbt_depression" in decision.eligible_protocols
    assert decision.tier == "moderate"
    assert decision.referral_required is False

    # ------------------------------------------------------------------
    # Step 8: Enroll in CBT depression protocol
    # ------------------------------------------------------------------
    enrollment = await engine.enroll("cbt_depression", str(screening.id))
    assert enrollment is not None, "Enrollment returned None (blocked?)"
    assert isinstance(enrollment, ProtocolEnrollment)
    assert enrollment.protocol_id == "cbt_depression"
    assert enrollment.status == "enrolled"
    assert enrollment.entry_screening_id == str(screening.id)
    assert enrollment.current_session_number == 0

    # ------------------------------------------------------------------
    # Step 9: handle_session_start again → session 1 greeting
    # ------------------------------------------------------------------
    engine2 = SessionEngine(test_user)
    session_response = await engine2.handle_session_start(context)

    assert session_response is not None, "Session start returned None"
    assert "Session 1" in session_response["message"]
    assert "Psychoeducation" in session_response["message"]
