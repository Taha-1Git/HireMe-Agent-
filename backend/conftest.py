"""Pytest configuration and fixtures."""

import pytest
import os
from sqlmodel import Session, create_engine
from sqlmodel import SQLModel


@pytest.fixture(scope="session")
def test_database():
    """Create test database."""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(test_database):
    """Provide database session for tests."""
    with Session(test_database) as session:
        yield session


@pytest.fixture
def mock_openai_key(monkeypatch):
    """Set mock OpenAI API key for tests."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-12345")
