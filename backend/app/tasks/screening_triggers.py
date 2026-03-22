"""Pattern-based screening triggers from inferred state history.

Analyzes recent InferredStateRecords to detect when a user may benefit
from a validated screening instrument (PHQ-9, GAD-7, PCL-5).
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from app.models.inferred_state import InferredStateRecord
from app.models.notification import PendingAction
from app.models.screening import ScreeningResult


async def check_screening_triggers(user_id: str) -> Optional[str]:
    """Check if user needs screening based on inferred state patterns.

    Returns instrument name ('phq9', 'gad7', 'pcl5') or None.
    """
    # 1. Skip if screening completed in last 14 days
    cutoff_14d = datetime.now(timezone.utc) - timedelta(days=14)
    recent_screening = await ScreeningResult.find_one(
        ScreeningResult.user_id == user_id,
        ScreeningResult.status == "completed",
        ScreeningResult.completed_at >= cutoff_14d,
    )
    if recent_screening is not None:
        return None

    # 2. Skip if undismissed PendingAction for screening_due already exists
    existing_action = await PendingAction.find_one(
        PendingAction.user_id == user_id,
        PendingAction.action_type == "screening_due",
        PendingAction.dismissed == False,  # noqa: E712
    )
    if existing_action is not None:
        return None

    # 3. Get records from last 7 days with confidence >= 0.3
    cutoff_7d = datetime.now(timezone.utc) - timedelta(days=7)
    records = await InferredStateRecord.find(
        InferredStateRecord.user_id == user_id,
        InferredStateRecord.confidence >= 0.3,
        InferredStateRecord.created_at >= cutoff_7d,
    ).sort("-created_at").to_list()

    # 4. Need at least 3 records
    if len(records) < 3:
        return None

    # 9. Check trauma BEFORE grouping by day (uses message count, not day count)
    trauma_count = sum(1 for r in records if "trauma" in r.themes)
    if trauma_count >= 2:
        return await _create_trigger(user_id, "pcl5")

    # 5. Group by day — keep most recent per day, sorted by date desc
    by_day: dict[str, InferredStateRecord] = {}
    for record in records:
        day_key = record.created_at.strftime("%Y-%m-%d")
        if day_key not in by_day:
            by_day[day_key] = record  # already sorted desc, first is most recent

    daily_records = sorted(by_day.values(), key=lambda r: r.created_at, reverse=True)

    # 6. Check consecutive low mood streak: mood_valence <= 3 for 3+ consecutive days
    streak = 0
    for rec in daily_records:
        if rec.mood_valence is not None and rec.mood_valence <= 3:
            streak += 1
            if streak >= 3:
                return await _create_trigger(user_id, "phq9")
        else:
            streak = 0

    # 7. Check anxiety theme: "anxiety" in themes for 3+ of last 7 days
    anxiety_days = sum(1 for r in daily_records if "anxiety" in r.themes)
    if anxiety_days >= 3:
        return await _create_trigger(user_id, "gad7")

    # 8. Check absolutist language: absolutist_count >= 3 for 3+ of last 7 days
    absolutist_days = sum(1 for r in daily_records if r.absolutist_count >= 3)
    if absolutist_days >= 3:
        return await _create_trigger(user_id, "phq9")

    return None


async def _create_trigger(user_id: str, instrument: str) -> str:
    """Create a PendingAction for the screening trigger."""
    action = PendingAction(
        user_id=user_id,
        action_type="screening_due",
        priority=3,
        data={"instrument": instrument},
    )
    await action.insert()
    return instrument
