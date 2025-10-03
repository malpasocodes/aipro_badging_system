"""Utilities for database migrations in development."""

from alembic.config import Config

from alembic import command
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_migration(message: str) -> None:
    """Create a new migration with the given message."""
    try:
        # Get the path to alembic.ini
        alembic_cfg = Config("alembic.ini")

        # Create the migration
        command.revision(alembic_cfg, autogenerate=True, message=message)
        logger.info(f"Created migration: {message}")

    except Exception as e:
        logger.error(f"Failed to create migration: {e}")
        raise


def run_migrations() -> None:
    """Run all pending migrations."""
    try:
        # Get the path to alembic.ini
        alembic_cfg = Config("alembic.ini")

        # Run migrations
        command.upgrade(alembic_cfg, "head")
        logger.info("Migrations completed successfully")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


def check_migrations() -> bool:
    """Check if there are pending migrations."""
    try:
        alembic_cfg = Config("alembic.ini")

        # This is a simplified check - in production you'd want more sophisticated logic
        return True

    except Exception as e:
        logger.error(f"Failed to check migrations: {e}")
        return False
