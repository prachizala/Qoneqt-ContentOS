import os
import socket
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

def get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/qoneqt_db")
    if "@db:" in url or "@db/" in url:
        try:
            socket.gethostbyname("db")
            return url
        except Exception:
            logger.info("[Database] Host 'db' not reachable. Using local SQLite database fallback.")
            return "sqlite+aiosqlite:///./qoneqt_local.db"
    return url

DATABASE_URL = get_database_url()

class Base(DeclarativeBase):
    pass

engine_kwargs = {
    "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
    "future": True,
}
if "sqlite" in DATABASE_URL:
    engine_kwargs["connect_args"] = {"timeout": 30.0}

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

if "sqlite" in DATABASE_URL:
    from sqlalchemy import event
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=10000;")
        cursor.close()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding async database sessions.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db() -> None:
    """
    Asynchronous database initialization helper.
    Creates all tables defined in Base metadata for development.
    """
    logger.info(f"Initializing database tables using {DATABASE_URL}...")
    from backend.app.models.models import Project, Script, Scene, Asset, Video, QAResult, Publication  # noqa: F401
    from sqlalchemy import text

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            await conn.execute(text("ALTER TABLE projects ADD COLUMN last_heartbeat DATETIME"))
        except Exception:
            pass
    logger.info("Database tables initialized successfully.")
