from datetime import datetime, timezone

import pytest
import pytest_asyncio

from app.models.notification import PendingAction
from app.models.user import User
from app.notifications.service import NotificationService


@pytest_asyncio.fixture
async def user_with_push(test_user: User) -> User:
    test_user.notification_enabled = True
    test_user.push_subscription = {
        "endpoint": "https://push.example.com/sub/123",
        "keys": {"p256dh": "fake-p256dh", "auth": "fake-auth"},
    }
    await test_user.save()
    return test_user


class TestGetTopPendingAction:
    async def test_returns_highest_priority(self, test_user: User):
        svc = NotificationService()
        await PendingAction(
            user_id=str(test_user.id), action_type="homework", priority=5
        ).insert()
        await PendingAction(
            user_id=str(test_user.id), action_type="session_ready", priority=2
        ).insert()
        await PendingAction(
            user_id=str(test_user.id), action_type="nudge", priority=8
        ).insert()

        result = await svc.get_top_pending_action(str(test_user.id))
        assert result is not None
        assert result.action_type == "session_ready"
        assert result.priority == 2

    async def test_dismissed_actions_excluded(self, test_user: User):
        svc = NotificationService()
        await PendingAction(
            user_id=str(test_user.id), action_type="session_ready", priority=1, dismissed=True
        ).insert()
        await PendingAction(
            user_id=str(test_user.id), action_type="nudge", priority=5, dismissed=False
        ).insert()

        result = await svc.get_top_pending_action(str(test_user.id))
        assert result is not None
        assert result.action_type == "nudge"

    async def test_returns_none_when_empty(self, test_user: User):
        svc = NotificationService()
        result = await svc.get_top_pending_action(str(test_user.id))
        assert result is None


class TestCreateAction:
    async def test_creates_action(self, test_user: User):
        svc = NotificationService()
        action = await svc.create_action(
            user_id=str(test_user.id),
            action_type="homework",
            priority=3,
            data={"description": "Practice CBT reframe"},
        )
        assert action.action_type == "homework"
        assert action.priority == 3
        assert action.data["description"] == "Practice CBT reframe"
        assert action.dismissed is False


class TestIsQuietHours:
    def test_normal_range(self):
        svc = NotificationService()
        # Quiet hours 22:00 - 08:00
        assert svc.is_quiet_hours(23, "22:00", "08:00") is True
        assert svc.is_quiet_hours(3, "22:00", "08:00") is True
        assert svc.is_quiet_hours(12, "22:00", "08:00") is False
        assert svc.is_quiet_hours(8, "22:00", "08:00") is False
        assert svc.is_quiet_hours(22, "22:00", "08:00") is True

    def test_midnight_crossing(self):
        svc = NotificationService()
        # Quiet hours 23:00 - 06:00
        assert svc.is_quiet_hours(0, "23:00", "06:00") is True
        assert svc.is_quiet_hours(5, "23:00", "06:00") is True
        assert svc.is_quiet_hours(6, "23:00", "06:00") is False
        assert svc.is_quiet_hours(10, "23:00", "06:00") is False
        assert svc.is_quiet_hours(23, "23:00", "06:00") is True

    def test_no_crossing(self):
        svc = NotificationService()
        # Quiet hours 13:00 - 15:00 (daytime quiet)
        assert svc.is_quiet_hours(14, "13:00", "15:00") is True
        assert svc.is_quiet_hours(12, "13:00", "15:00") is False
        assert svc.is_quiet_hours(15, "13:00", "15:00") is False


class TestSendPush:
    async def test_returns_false_without_subscription(self, test_user: User):
        svc = NotificationService()
        result = await svc.send_push(test_user, "Title", "Body")
        assert result is False

    async def test_returns_false_when_notifications_disabled(self, user_with_push: User):
        svc = NotificationService()
        user_with_push.notification_enabled = False
        await user_with_push.save()
        result = await svc.send_push(user_with_push, "Title", "Body")
        assert result is False
