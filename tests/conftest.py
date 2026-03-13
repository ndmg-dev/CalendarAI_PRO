"""Test fixtures and shared configuration for CalendAI PRO tests."""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app import create_app
from app.extensions import db as _db
from app.models.user import User
from app.models.event import Event
from app.models.calendar_sync import CalendarSync


@pytest.fixture(scope="session")
def app():
    """Create Flask application for testing."""
    app = create_app("testing")

    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app):
    """Provide a clean database session for each test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        # Clean up all tables
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def user_a(db):
    """Create test user A."""
    user = User(
        google_id="google-user-a-123",
        email="alice@example.com",
        display_name="Alice",
        avatar_url="https://example.com/alice.jpg",
        domain="example.com",
        timezone="America/Sao_Paulo",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def user_b(db):
    """Create test user B (for isolation tests)."""
    user = User(
        google_id="google-user-b-456",
        email="bob@example.com",
        display_name="Bob",
        timezone="America/Sao_Paulo",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sample_event(db, user_a):
    """Create a sample event for user A."""
    tz = ZoneInfo("America/Sao_Paulo")
    event = Event(
        user_id=user_a.id,
        title="Reunião de teste",
        description="Descrição do evento",
        start_datetime=datetime(2026, 3, 15, 14, 0, tzinfo=tz),
        end_datetime=datetime(2026, 3, 15, 15, 0, tzinfo=tz),
        timezone="America/Sao_Paulo",
        status="active",
    )
    db.session.add(event)
    db.session.commit()
    return event


@pytest.fixture
def authenticated_client(client, user_a, app):
    """Test client with user_a authenticated (simulates Flask-Login session)."""
    with client.session_transaction() as sess:
        sess["_user_id"] = user_a.id
    return client
