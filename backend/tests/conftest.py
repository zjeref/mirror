import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.service import create_access_token, hash_password
from app.models.base import Base, get_session
from app.models.user import User

# Import all models to ensure they're registered with Base.metadata
import app.models.conversation  # noqa: F401
import app.models.check_in  # noqa: F401
import app.models.thought_record  # noqa: F401
import app.models.habit  # noqa: F401
import app.models.suggestion  # noqa: F401
import app.models.life_area  # noqa: F401
import app.models.pattern  # noqa: F401
import app.models.energy  # noqa: F401


# Create a test engine that all tests share
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    session = TestSession()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def override_get_session():
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    # Patch init_db to use test engine
    import app.models.base as base_mod
    original_init = base_mod.init_db
    base_mod.init_db = lambda engine=None: None  # no-op, setup_db handles it

    from app.main import create_app
    test_app = create_app()
    test_app.dependency_overrides[get_session] = override_get_session

    with TestClient(test_app) as c:
        yield c

    test_app.dependency_overrides.clear()
    base_mod.init_db = original_init


@pytest.fixture
def test_user(db: Session) -> User:
    user = User(
        email="test@mirror.app",
        name="Test User",
        password_hash=hash_password("testpassword123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_client(client, auth_headers):
    client.headers.update(auth_headers)
    return client
