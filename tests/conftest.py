"""Shared test fixtures and configuration."""

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture(scope="function")
def test_engine():
    """
    Create an in-memory SQLite database for testing.

    This fixture creates a fresh database for each test function,
    ensuring test isolation.
    """
    # Create in-memory database with StaticPool to persist across connections
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    SQLModel.metadata.create_all(engine)

    yield engine

    # Cleanup
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_session(test_engine):
    """
    Create a test database session.

    This fixture provides a session connected to the test database.
    """
    with Session(test_engine) as session:
        yield session


@pytest.fixture(scope="function", autouse=True)
def override_get_engine(test_engine, monkeypatch):
    """
    Override the get_engine function to use the test database.

    This fixture automatically runs for every test and ensures
    all database operations use the test database instead of
    the production database.
    """
    def _get_test_engine():
        return test_engine

    monkeypatch.setattr("app.core.database.get_engine", _get_test_engine)
    monkeypatch.setattr("app.services.request_service.get_engine", _get_test_engine)
    monkeypatch.setattr("app.services.audit_service.get_engine", _get_test_engine)
    monkeypatch.setattr("app.services.roster_service.get_engine", _get_test_engine)
