import logging
from datetime import datetime, timezone

from beanie.operators import In

from app.models.homework import Homework
from app.models.protocol import ProtocolEnrollment, ProtocolSession
from app.models.user import User
from app.notifications.service import NotificationService

logger = logging.getLogger(__name__)


async def check_homework_reminders():
    """Find overdue homework and send reminders."""
    now = datetime.now(timezone.utc)
    svc = NotificationService()

    overdue = await Homework.find(
        In(Homework.status, ["assigned", "reminded"]),
        Homework.due_date <= now,
    ).to_list()

    for hw in overdue:
        user = await User.get(hw.user_id)
        if not user:
            continue

        hw.reminder_count += 1
        hw.status = "reminded"
        await hw.save()

        await svc.send_push(
            user,
            title="Homework reminder",
            body=f"Don't forget: {hw.description}",
        )
        logger.info("Sent homework reminder for hw=%s user=%s", hw.id, hw.user_id)


async def check_reengagement():
    """Check active enrollments for inactivity and send nudges or pause."""
    now = datetime.now(timezone.utc)
    svc = NotificationService()

    enrollments = await ProtocolEnrollment.find(
        ProtocolEnrollment.status == "enrolled",
    ).to_list()

    for enrollment in enrollments:
        user = await User.get(enrollment.user_id)
        if not user:
            continue

        # Find the most recent session
        last_session = await ProtocolSession.find(
            ProtocolSession.enrollment_id == str(enrollment.id),
        ).sort("-started_at").first_or_none()

        if not last_session:
            continue

        last_activity = last_session.completed_at or last_session.started_at
        # Ensure timezone-aware comparison
        if last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=timezone.utc)
        days_inactive = (now - last_activity).days

        if days_inactive >= 14:
            enrollment.status = "paused"
            await enrollment.save()
            await svc.send_push(
                user,
                title="We've paused your program",
                body="No rush. When you're ready, we'll pick up where you left off.",
            )
            logger.info("Paused enrollment=%s after %d days inactive", enrollment.id, days_inactive)
        elif days_inactive >= 7:
            await svc.send_push(
                user,
                title="We miss you",
                body="It's been a while. A small step forward is still a step.",
            )
            logger.info("Sent gentle nudge for enrollment=%s", enrollment.id)
        elif days_inactive >= 3:
            await svc.send_push(
                user,
                title="Your next session is ready",
                body="Ready to continue? Your next session is waiting for you.",
            )
            logger.info("Sent session-ready nudge for enrollment=%s", enrollment.id)
