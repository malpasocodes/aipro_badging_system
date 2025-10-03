"""Database configuration and connection management."""

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_engine():
    """Get database engine with connection pooling."""
    settings = get_settings()

    if not settings.database_url:
        raise ValueError("DATABASE_URL not configured")

    # Convert PostgreSQL URLs to use psycopg3 driver instead of psycopg2
    # Render provides postgresql:// URLs, but we use psycopg[binary] (psycopg3)
    # SQLAlchemy needs postgresql+psycopg:// to use the psycopg3 driver
    database_url = settings.database_url
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    # SQL echo disabled by default for security - SQL queries can contain sensitive data
    # Enable only via DATABASE_ECHO=true in .env for debugging
    engine = create_engine(
        database_url,
        echo=settings.database_echo,  # SQL logging (disabled by default)
        pool_pre_ping=True,            # Verify connections before use
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
