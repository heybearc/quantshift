"""Database connection and session management."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from quantshift_core.config import get_settings


class DatabaseManager:
    """Manage database connections and sessions."""

    def __init__(self) -> None:
        """Initialize database manager."""
        settings = get_settings()
        self._engine = create_engine(
            str(settings.database_url),
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
        )

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Provide a transactional scope for database operations."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


_db_manager: DatabaseManager | None = None


def get_db() -> DatabaseManager:
    """Get singleton database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
