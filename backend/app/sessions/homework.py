"""Adaptive homework assignment and tracking system.

Homework difficulty adapts based on consecutive misses:
- 0 misses  → "structured" (full homework)
- 1 miss    → "gentle" (lighter version)
- 2+ misses → "minimal" (bare minimum)
- 3+ misses → pause homework entirely
"""

from datetime import datetime, timezone

from app.models.homework import Homework
from app.models.protocol import ProtocolEnrollment


class HomeworkManager:
    """Static methods for adaptive homework management."""

    @staticmethod
    def determine_tier(consecutive_misses: int) -> str:
        """Map consecutive misses to an adaptive tier.

        0 → "structured", 1 → "gentle", 2+ → "minimal"
        """
        if consecutive_misses == 0:
            return "structured"
        elif consecutive_misses == 1:
            return "gentle"
        else:
            return "minimal"

    @staticmethod
    def should_pause(consecutive_misses: int) -> bool:
        """Return True if homework should be paused (>= 3 misses)."""
        return consecutive_misses >= 3

    @staticmethod
    async def assign(
        enrollment: ProtocolEnrollment,
        protocol,
        session_number: int,
    ) -> Homework:
        """Create and save homework with adaptive tier based on enrollment history.

        Args:
            enrollment: The user's protocol enrollment.
            protocol: A protocol object with get_homework(session_number, tier).
            session_number: Which session this homework belongs to.

        Returns:
            The saved Homework document.
        """
        tier = HomeworkManager.determine_tier(enrollment.consecutive_homework_misses)
        description = protocol.get_homework(session_number, tier)
        if description is None:
            description = f"Session {session_number} homework"

        homework = Homework(
            user_id=enrollment.user_id,
            enrollment_id=str(enrollment.id),
            session_number=session_number,
            description=description,
            adaptive_tier=tier,
            status="assigned",
        )
        await homework.insert()
        return homework

    @staticmethod
    async def complete(homework: Homework, user_response: str) -> Homework:
        """Mark homework as completed with the user's response.

        Args:
            homework: The Homework document to complete.
            user_response: The user's response/reflection.

        Returns:
            The updated Homework document.
        """
        homework.status = "completed"
        homework.user_response = user_response
        homework.completed_at = datetime.now(timezone.utc)
        await homework.save()
        return homework

    @staticmethod
    async def skip(homework: Homework, enrollment: ProtocolEnrollment) -> bool:
        """Mark homework as skipped and increment enrollment miss counter.

        Args:
            homework: The Homework document to skip.
            enrollment: The user's protocol enrollment.

        Returns:
            True if homework should be paused (>= 3 consecutive misses).
        """
        homework.status = "skipped"
        await homework.save()

        enrollment.consecutive_homework_misses += 1
        await enrollment.save()

        return HomeworkManager.should_pause(enrollment.consecutive_homework_misses)

    @staticmethod
    async def get_pending(user_id: str) -> Homework | None:
        """Find the most recent assigned or reminded homework for a user.

        Args:
            user_id: The user's ID.

        Returns:
            A Homework document if one is pending, otherwise None.
        """
        return await Homework.find_one(
            Homework.user_id == user_id,
            {"$or": [{"status": "assigned"}, {"status": "reminded"}]},
        )
