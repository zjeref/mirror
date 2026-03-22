"""MongoDB connection and document initialization via Beanie."""

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

_client = None


async def init_db():
    """Initialize MongoDB connection and Beanie ODM."""
    global _client

    from app.models.user import User
    from app.models.conversation import Conversation, Message
    from app.models.check_in import CheckIn
    from app.models.thought_record import ThoughtRecord
    from app.models.habit import Habit, HabitLog
    from app.models.suggestion import Suggestion
    from app.models.life_area import LifeAreaScore
    from app.models.pattern import DetectedPattern
    from app.models.energy import EnergyReading
    from app.models.inferred_state import InferredStateRecord
    from app.models.journal import JournalEntry
    from app.models.activity import Activity, UserValues
    from app.models.program import ProgramEnrollment
    from app.models.screening import ScreeningResult
    from app.models.protocol import ProtocolEnrollment, ProtocolSession
    from app.models.homework import Homework
    from app.models.notification import PendingAction

    _client = AsyncIOMotorClient(settings.mongodb_url)
    db = _client[settings.mongodb_db_name]

    await init_beanie(
        database=db,
        document_models=[
            User,
            Conversation,
            Message,
            CheckIn,
            ThoughtRecord,
            Habit,
            HabitLog,
            Suggestion,
            LifeAreaScore,
            DetectedPattern,
            EnergyReading,
            InferredStateRecord,
            JournalEntry,
            Activity,
            UserValues,
            ProgramEnrollment,
            ScreeningResult,
            ProtocolEnrollment,
            ProtocolSession,
            Homework,
            PendingAction,
        ],
    )


async def close_db():
    global _client
    if _client:
        _client.close()
        _client = None
