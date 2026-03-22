from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from app.models.homework import Homework
from app.models.protocol import ProtocolEnrollment, ProtocolSession
from app.models.user import User
from app.auth.service import hash_password


@pytest_asyncio.fixture
async def reminder_user() -> User:
    user = User(
        email="reminder@mirror.app",
        name="Reminder User",
        password_hash=hash_password("testpassword123"),
        notification_enabled=True,
        push_subscription={
            "endpoint": "https://push.example.com/sub/456",
            "keys": {"p256dh": "fake", "auth": "fake"},
        },
    )
    await user.insert()
    return user


class TestCheckHomeworkReminders:
    async def test_increments_count_and_changes_status(self, reminder_user: User):
        hw = Homework(
            user_id=str(reminder_user.id),
            enrollment_id="enroll-1",
            session_number=1,
            description="Practice gratitude",
            due_date=datetime.now(timezone.utc) - timedelta(hours=2),
            status="assigned",
            reminder_count=0,
        )
        await hw.insert()

        with patch(
            "app.tasks.reminders.NotificationService.send_push",
            new_callable=AsyncMock,
            return_value=True,
        ):
            from app.tasks.reminders import check_homework_reminders

            await check_homework_reminders()

        updated = await Homework.get(hw.id)
        assert updated.reminder_count == 1
        assert updated.status == "reminded"

    async def test_skips_completed_homework(self, reminder_user: User):
        hw = Homework(
            user_id=str(reminder_user.id),
            enrollment_id="enroll-1",
            session_number=1,
            description="Already done",
            due_date=datetime.now(timezone.utc) - timedelta(hours=2),
            status="completed",
            reminder_count=0,
        )
        await hw.insert()

        with patch(
            "app.tasks.reminders.NotificationService.send_push",
            new_callable=AsyncMock,
            return_value=True,
        ):
            from app.tasks.reminders import check_homework_reminders

            await check_homework_reminders()

        updated = await Homework.get(hw.id)
        assert updated.reminder_count == 0
        assert updated.status == "completed"


class TestCheckReengagement:
    async def test_pauses_after_14_days_inactive(self, reminder_user: User):
        enrollment = ProtocolEnrollment(
            user_id=str(reminder_user.id),
            protocol_id="cbt-depression",
            status="enrolled",
            current_session_number=2,
        )
        await enrollment.insert()

        # Last session was 15 days ago
        session = ProtocolSession(
            enrollment_id=str(enrollment.id),
            user_id=str(reminder_user.id),
            session_number=2,
            started_at=datetime.now(timezone.utc) - timedelta(days=15),
            completed_at=datetime.now(timezone.utc) - timedelta(days=15),
        )
        await session.insert()

        with patch(
            "app.tasks.reminders.NotificationService.send_push",
            new_callable=AsyncMock,
            return_value=True,
        ):
            from app.tasks.reminders import check_reengagement

            await check_reengagement()

        updated = await ProtocolEnrollment.get(enrollment.id)
        assert updated.status == "paused"

    async def test_sends_nudge_at_7_days(self, reminder_user: User):
        enrollment = ProtocolEnrollment(
            user_id=str(reminder_user.id),
            protocol_id="cbt-depression",
            status="enrolled",
            current_session_number=1,
        )
        await enrollment.insert()

        session = ProtocolSession(
            enrollment_id=str(enrollment.id),
            user_id=str(reminder_user.id),
            session_number=1,
            started_at=datetime.now(timezone.utc) - timedelta(days=8),
            completed_at=datetime.now(timezone.utc) - timedelta(days=8),
        )
        await session.insert()

        mock_push = AsyncMock(return_value=True)
        with patch(
            "app.tasks.reminders.NotificationService.send_push",
            mock_push,
        ):
            from app.tasks.reminders import check_reengagement

            await check_reengagement()

        # Should NOT be paused (only 8 days)
        updated = await ProtocolEnrollment.get(enrollment.id)
        assert updated.status == "enrolled"
        # Should have sent a nudge
        mock_push.assert_called()

    async def test_sends_session_ready_at_3_days(self, reminder_user: User):
        enrollment = ProtocolEnrollment(
            user_id=str(reminder_user.id),
            protocol_id="cbt-depression",
            status="enrolled",
            current_session_number=1,
        )
        await enrollment.insert()

        session = ProtocolSession(
            enrollment_id=str(enrollment.id),
            user_id=str(reminder_user.id),
            session_number=1,
            started_at=datetime.now(timezone.utc) - timedelta(days=4),
            completed_at=datetime.now(timezone.utc) - timedelta(days=4),
        )
        await session.insert()

        mock_push = AsyncMock(return_value=True)
        with patch(
            "app.tasks.reminders.NotificationService.send_push",
            mock_push,
        ):
            from app.tasks.reminders import check_reengagement

            await check_reengagement()

        updated = await ProtocolEnrollment.get(enrollment.id)
        assert updated.status == "enrolled"
        mock_push.assert_called()
