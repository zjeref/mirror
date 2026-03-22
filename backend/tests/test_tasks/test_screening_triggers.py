"""Tests for pattern-based screening triggers."""

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio

from app.models.inferred_state import InferredStateRecord
from app.models.notification import PendingAction
from app.models.screening import ScreeningResult
from app.models.user import User
from app.tasks.screening_triggers import check_screening_triggers


def _days_ago(n: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=n)


async def _create_state(
    user_id: str,
    days_ago: int,
    mood_valence: float = 5.0,
    themes: list[str] | None = None,
    absolutist_count: int = 0,
    confidence: float = 0.7,
) -> InferredStateRecord:
    record = InferredStateRecord(
        user_id=user_id,
        mood_valence=mood_valence,
        themes=themes or [],
        absolutist_count=absolutist_count,
        confidence=confidence,
        created_at=_days_ago(days_ago),
    )
    await record.insert()
    return record


@pytest.mark.asyncio
async def test_low_mood_streak_triggers_phq9(test_user: User):
    """3 consecutive days of low mood should trigger PHQ-9."""
    uid = str(test_user.id)
    for day in range(3):
        await _create_state(uid, days_ago=day, mood_valence=2.0)

    result = await check_screening_triggers(uid)

    assert result == "phq9"
    action = await PendingAction.find_one(
        PendingAction.user_id == uid,
        PendingAction.action_type == "screening_due",
    )
    assert action is not None
    assert action.data["instrument"] == "phq9"
    assert action.priority == 3


@pytest.mark.asyncio
async def test_anxiety_theme_triggers_gad7(test_user: User):
    """3+ days with anxiety theme in last 7 days should trigger GAD-7."""
    uid = str(test_user.id)
    for day in range(4):
        await _create_state(uid, days_ago=day, themes=["anxiety"])

    result = await check_screening_triggers(uid)

    assert result == "gad7"


@pytest.mark.asyncio
async def test_absolutist_language_triggers_phq9(test_user: User):
    """3+ days with absolutist_count >= 3 should trigger PHQ-9."""
    uid = str(test_user.id)
    for day in range(3):
        await _create_state(uid, days_ago=day, absolutist_count=4)

    result = await check_screening_triggers(uid)

    assert result == "phq9"


@pytest.mark.asyncio
async def test_trauma_theme_triggers_pcl5(test_user: User):
    """2+ messages (not days) with trauma theme should trigger PCL-5."""
    uid = str(test_user.id)
    # Two messages on the same day with trauma theme
    await _create_state(uid, days_ago=0, themes=["trauma"])
    await _create_state(uid, days_ago=0, themes=["trauma"])
    # Need a 3rd record to meet the minimum-3-records requirement
    await _create_state(uid, days_ago=1, themes=[])

    result = await check_screening_triggers(uid)

    assert result == "pcl5"


@pytest.mark.asyncio
async def test_no_trigger_if_screening_completed_recently(test_user: User):
    """No trigger if screening completed in last 14 days."""
    uid = str(test_user.id)
    # Create a recent completed screening
    screening = ScreeningResult(
        user_id=uid,
        instrument="phq9",
        status="completed",
        completed_at=_days_ago(5),
        created_at=_days_ago(5),
    )
    await screening.insert()

    # Create low mood streak that would normally trigger
    for day in range(3):
        await _create_state(uid, days_ago=day, mood_valence=2.0)

    result = await check_screening_triggers(uid)

    assert result is None


@pytest.mark.asyncio
async def test_no_trigger_with_only_2_days_low_mood(test_user: User):
    """Only 2 days of low mood is not enough to trigger."""
    uid = str(test_user.id)
    for day in range(2):
        await _create_state(uid, days_ago=day, mood_valence=2.0)
    # Add a 3rd record with normal mood to meet min-records threshold
    await _create_state(uid, days_ago=3, mood_valence=7.0)

    result = await check_screening_triggers(uid)

    assert result is None


@pytest.mark.asyncio
async def test_no_trigger_if_pending_action_exists(test_user: User):
    """No trigger if undismissed PendingAction for screening_due exists."""
    uid = str(test_user.id)
    action = PendingAction(
        user_id=uid,
        action_type="screening_due",
        data={"instrument": "phq9"},
        dismissed=False,
    )
    await action.insert()

    for day in range(3):
        await _create_state(uid, days_ago=day, mood_valence=2.0)

    result = await check_screening_triggers(uid)

    assert result is None


@pytest.mark.asyncio
async def test_no_trigger_with_insufficient_records(test_user: User):
    """Need at least 3 records to trigger anything."""
    uid = str(test_user.id)
    await _create_state(uid, days_ago=0, mood_valence=2.0)
    await _create_state(uid, days_ago=1, mood_valence=2.0)

    result = await check_screening_triggers(uid)

    assert result is None


@pytest.mark.asyncio
async def test_low_confidence_records_excluded(test_user: User):
    """Records with confidence < 0.3 are excluded."""
    uid = str(test_user.id)
    for day in range(3):
        await _create_state(uid, days_ago=day, mood_valence=2.0, confidence=0.1)

    result = await check_screening_triggers(uid)

    assert result is None
