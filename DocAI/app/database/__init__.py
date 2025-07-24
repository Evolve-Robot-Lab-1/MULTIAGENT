"""
Database initialization and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy.pool import StaticPool

from app.core.config import get_config
from app.core.logging import get_logger


logger = get_logger(__name__)

# Base class for all models
Base = declarative_base()

# Global session factory
_session_factory = None
_engine = None


def init_database(config=None):
    """
    Initialize database connection.
    
    Args:
        config: Application configuration
    """
    global _engine, _session_factory
    
    if config is None:
        config = get_config()
    
    # Create engine
    if config.database.uri.startswith('sqlite'):
        # Special handling for SQLite
        _engine = create_engine(
            config.database.uri,
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
            echo=config.server.debug
        )
    else:
        # PostgreSQL, MySQL, etc.
        _engine = create_engine(
            config.database.uri,
            pool_size=config.database.pool_size,
            max_overflow=config.database.max_overflow,
            pool_timeout=config.database.pool_timeout,
            echo=config.server.debug
        )
    
    # Create session factory
    _session_factory = scoped_session(sessionmaker(
        bind=_engine,
        autocommit=False,
        autoflush=False
    ))
    
    logger.info(f"Database initialized: {config.database.uri}")


def get_session():
    """
    Get database session.
    
    Returns:
        SQLAlchemy session
    """
    if _session_factory is None:
        init_database()
    
    return _session_factory()


def close_session():
    """Close current session."""
    if _session_factory:
        _session_factory.remove()


def create_tables():
    """Create all database tables."""
    if _engine is None:
        init_database()
    
    # Import all models to register them
    from app.database import models
    
    Base.metadata.create_all(bind=_engine)
    logger.info("Database tables created")


def drop_tables():
    """Drop all database tables."""
    if _engine is None:
        init_database()
    
    Base.metadata.drop_all(bind=_engine)
    logger.info("Database tables dropped")


class DatabaseSession:
    """Context manager for database sessions."""
    
    def __enter__(self):
        self.session = get_session()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            try:
                self.session.commit()
            except Exception:
                self.session.rollback()
                raise
        finally:
            close_session()