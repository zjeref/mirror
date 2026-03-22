from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.base import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    if settings.environment != "test":
        from app.tasks.scheduler import start_scheduler, stop_scheduler
        start_scheduler()

    yield

    if settings.environment != "test":
        from app.tasks.scheduler import stop_scheduler
        stop_scheduler()

    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    origins = [o.strip() for o in settings.cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.auth.router import router as auth_router
    from app.chat.router import router as chat_router
    from app.dashboard.router import router as dashboard_router
    from app.psychology.router import router as psychology_router
    from app.journal.router import router as journal_router
    from app.activity.router import router as activity_router
    from app.screening.router import router as screening_router
    from app.sessions.router import router as sessions_router
    from app.notifications.router import router as notifications_router

    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
    app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])
    app.include_router(psychology_router, prefix="/api", tags=["psychology"])
    app.include_router(journal_router, prefix="/api", tags=["journal"])
    app.include_router(activity_router, prefix="/api", tags=["activities"])
    app.include_router(screening_router, prefix="/api/screening", tags=["screening"])
    app.include_router(sessions_router, prefix="/api", tags=["sessions"])
    app.include_router(notifications_router, prefix="/api/notifications", tags=["notifications"])

    return app


app = create_app()
