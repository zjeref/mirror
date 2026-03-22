import os
import asyncio

import pytest
import pytest_asyncio
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient
from httpx import AsyncClient, ASGITransport

from app.auth.service import create_access_token, hash_password
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
from app.models.screening import ScreeningResult
from app.models.protocol import ProtocolEnrollment, ProtocolSession
from app.models.homework import Homework
from app.models.notification import PendingAction
from app.models.program import ProgramEnrollment
from app.models.activity import UserValues

ALL_MODELS = [
    User, Conversation, Message, CheckIn, ThoughtRecord,
    Habit, HabitLog, Suggestion, LifeAreaScore, DetectedPattern, EnergyReading,
    InferredStateRecord, ScreeningResult, ProtocolEnrollment, ProtocolSession,
    Homework, PendingAction, ProgramEnrollment, UserValues,
]


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Initialize Beanie with mongomock for each test."""
    # Disable LLM in tests
    from app.config import settings
    settings.anthropic_api_key = ""

    client = AsyncMongoMockClient()
    db = client["mirror_test"]
    await init_beanie(database=db, document_models=ALL_MODELS)
    yield
    # Drop all collections after test
    for model in ALL_MODELS:
        await model.find_all().delete()
    client.close()


@pytest_asyncio.fixture
async def test_user() -> User:
    user = User(
        email="test@mirror.app",
        name="Test User",
        password_hash=hash_password("testpassword123"),
    )
    await user.insert()
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    token = create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def client():
    """Async test client with mongomock DB."""
    import app.models.base as base_mod

    # Patch init_db/close_db to no-op (setup_db handles it)
    original_init = base_mod.init_db
    original_close = base_mod.close_db
    base_mod.init_db = lambda: asyncio.sleep(0)
    base_mod.close_db = lambda: asyncio.sleep(0)

    from app.main import create_app
    test_app = create_app()

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    base_mod.init_db = original_init
    base_mod.close_db = original_close


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient, test_user: User):
    token = create_access_token(str(test_user.id))
    client.headers["Authorization"] = f"Bearer {token}"
    return client
