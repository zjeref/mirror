import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.tasks.reminders import check_homework_reminders, check_reengagement

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler():
    """Configure and start the APScheduler. Call once at app startup."""
    scheduler.add_job(
        check_homework_reminders,
        trigger=IntervalTrigger(hours=1),
        id="homework_reminders",
        replace_existing=True,
    )
    scheduler.add_job(
        check_reengagement,
        trigger=IntervalTrigger(days=1),
        id="reengagement_check",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started with homework_reminders (1h) and reengagement (1d)")


def stop_scheduler():
    """Shut down the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
