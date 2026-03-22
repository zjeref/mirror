import json
import logging
from typing import Optional

from app.models.notification import PendingAction
from app.models.user import User

logger = logging.getLogger(__name__)


class NotificationService:
    async def get_top_pending_action(self, user_id: str) -> Optional[PendingAction]:
        """Return the undismissed action with the highest priority (lowest number)."""
        return await PendingAction.find(
            PendingAction.user_id == user_id,
            PendingAction.dismissed == False,  # noqa: E712
        ).sort("+priority").first_or_none()

    async def create_action(
        self,
        user_id: str,
        action_type: str,
        priority: int = 5,
        data: Optional[dict] = None,
    ) -> PendingAction:
        action = PendingAction(
            user_id=user_id,
            action_type=action_type,
            priority=priority,
            data=data or {},
        )
        await action.insert()
        return action

    @staticmethod
    def is_quiet_hours(current_hour: int, quiet_start: str, quiet_end: str) -> bool:
        """Check if current_hour falls within quiet hours. Handles midnight crossing."""
        start = int(quiet_start.split(":")[0])
        end = int(quiet_end.split(":")[0])

        if start <= end:
            # No midnight crossing (e.g., 13:00 - 15:00)
            return start <= current_hour < end
        else:
            # Midnight crossing (e.g., 22:00 - 08:00)
            return current_hour >= start or current_hour < end

    async def send_push(self, user: User, title: str, body: str) -> bool:
        """Send a web push notification. Returns False if no subscription or error."""
        if not user.notification_enabled:
            return False
        if not user.push_subscription:
            return False

        try:
            from pywebpush import webpush
            from app.config import settings

            webpush(
                subscription_info=user.push_subscription,
                data=json.dumps({"title": title, "body": body}),
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": f"mailto:{settings.vapid_email}"},
            )
            return True
        except Exception:
            logger.exception("Failed to send push notification to user %s", user.id)
            return False
