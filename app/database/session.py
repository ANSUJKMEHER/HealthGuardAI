"""
HealthGuard AI — Database Session Management
Connection pooling, session factory, and database initialization.
Supports both SQLite (local dev) and PostgreSQL (production/Neon).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from app.config import settings
from app.database.models import Base

import structlog

logger = structlog.get_logger(__name__)


def _build_engine():
    """Create SQLAlchemy engine based on DATABASE_URL."""
    url = settings.database_url

    # SQLite needs special args
    if url.startswith("sqlite"):
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=False,
        )
    else:
        # PostgreSQL with connection pooling
        engine = create_engine(
            url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=300,    # Recycle connections every 5 min
            echo=False,
        )

    return engine


# Module-level engine and session factory
engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db():
    """Create all tables. Called once at application startup."""
    Base.metadata.create_all(bind=engine)
    logger.info("database_initialized", url=settings.database_url.split("@")[-1] if "@" in settings.database_url else settings.database_url)


@contextmanager
def get_db() -> Session:
    """
    Context manager for database sessions.
    Automatically commits on success, rolls back on error, and closes.

    Usage:
        with get_db() as db:
            db.add(incident)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db_dependency():
    """
    FastAPI dependency for database sessions.

    Usage:
        @app.get("/incidents")
        def get_incidents(db: Session = Depends(get_db_dependency)):
            ...
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
