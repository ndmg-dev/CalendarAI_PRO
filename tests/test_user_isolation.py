"""Tests for user isolation — ensuring users cannot access each other's data."""

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.scheduling_service import SchedulingService, SchedulingError
from app.repositories.event_repository import EventRepository
from app.models.event import Event


class TestUserIsolation:
    """Verify that user A cannot see or modify user B's events."""

    def test_list_only_own_events(self, app, db, user_a, user_b):
        """User A should not see User B's events."""
        with app.app_context():
            tz = ZoneInfo("America/Sao_Paulo")

            # Create event for user A
            SchedulingService.create_event(
                user_id=user_a.id,
                title="Evento de Alice",
                start_datetime=datetime(2026, 3, 20, 14, 0, tzinfo=tz),
            )

            # Create event for user B
            SchedulingService.create_event(
                user_id=user_b.id,
                title="Evento de Bob",
                start_datetime=datetime(2026, 3, 20, 15, 0, tzinfo=tz),
            )

            # User A should only see their own event
            events_a = SchedulingService.list_events(user_id=user_a.id)
            assert len(events_a) == 1
            assert events_a[0].title == "Evento de Alice"

            # User B should only see their own event
            events_b = SchedulingService.list_events(user_id=user_b.id)
            assert len(events_b) == 1
            assert events_b[0].title == "Evento de Bob"

    def test_cannot_get_other_user_event(self, app, db, user_a, user_b):
        """User B cannot get User A's event by ID."""
        with app.app_context():
            tz = ZoneInfo("America/Sao_Paulo")
            event = SchedulingService.create_event(
                user_id=user_a.id,
                title="Evento privado de Alice",
                start_datetime=datetime(2026, 3, 20, 14, 0, tzinfo=tz),
            )

            # User B tries to access User A's event
            result = EventRepository.get_by_id(event.id, user_b.id)
            assert result is None

    def test_cannot_update_other_user_event(self, app, db, user_a, user_b):
        """User B cannot update User A's event."""
        with app.app_context():
            tz = ZoneInfo("America/Sao_Paulo")
            event = SchedulingService.create_event(
                user_id=user_a.id,
                title="Evento de Alice",
                start_datetime=datetime(2026, 3, 20, 14, 0, tzinfo=tz),
            )

            with pytest.raises(SchedulingError, match="não encontrado"):
                SchedulingService.update_event(
                    user_id=user_b.id,
                    event_id=event.id,
                    title="Hackeado por Bob",
                )

    def test_cannot_cancel_other_user_event(self, app, db, user_a, user_b):
        """User B cannot cancel User A's event."""
        with app.app_context():
            tz = ZoneInfo("America/Sao_Paulo")
            event = SchedulingService.create_event(
                user_id=user_a.id,
                title="Evento de Alice",
                start_datetime=datetime(2026, 3, 20, 14, 0, tzinfo=tz),
            )

            with pytest.raises(SchedulingError, match="não encontrado"):
                SchedulingService.cancel_event(
                    user_id=user_b.id,
                    event_id=event.id,
                )

            # Verify event is still active for user A
            original = SchedulingService.get_event(user_a.id, event.id)
            assert original.status == "active"
