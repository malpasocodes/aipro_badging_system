"""Database configuration and connection management."""

from sqlmodel import SQLModel, create_engine, Session
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_engine():
    """Get database engine with connection pooling."""
    settings = get_settings()
    
    if not settings.database_url:
        raise ValueError("DATABASE_URL not configured")
    
    # For Phase 2A, we use a simple engine configuration
    engine = create_engine(
        settings.database_url,
        echo=settings.debug,  # Log SQL queries in debug mode
        pool_pre_ping=True,   # Verify connections before use
    )
    
    return engine


def get_session():
    """Get database session."""
    engine = get_engine()
    with Session(engine) as session:
        yield session


def create_tables():
    """Create all tables (for development setup)."""
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created")


def check_database_connection():
    """Check if database is accessible."""
    try:
        engine = get_engine()
        with Session(engine) as session:
            session.exec("SELECT 1")
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        return False