"""Tests for SchedulingService — CRUD, validation, date parsing."""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.services.scheduling_service import SchedulingService, SchedulingError


class TestCreateEvent:
    """Test event creation via SchedulingService."""

    def test_create_event_basic(self, app, db, user_a):
        with app.app_context():
            tz = ZoneInfo("America/Sao_Paulo")
            start = datetime(2026, 3, 20, 14, 0, tzinfo=tz)
            event = SchedulingService.create_event(
                user_id=user_a.id,
                title="Reunião importante",
                start_datetime=start,
            )
            assert event.id is not None
            assert event.title == "Reunião importante"
            assert event.status == "active"
            # SQLite stores naive datetimes; compare components
            expected_end = start + timedelta(hours=1)
            assert event.end_datetime.hour == expected_end.hour
            assert event.end_datetime.day == expected_end.day

    def test_create_event_with_end(self, app, db, user_a):
        with app.app_context():
            tz = ZoneInfo("America/Sao_Paulo")
            start = datetime(2026, 3, 20, 14, 0, tzinfo=tz)
            end = datetime(2026, 3, 20, 16, 30, tzinfo=tz)
            event = SchedulingService.create_event(
                user_id=user_a.id,
                title="Workshop",
                start_datetime=start,
                end_datetime=end,
                description="Workshop de Python",
            )
            # SQLite stores naive datetimes; compare components
            assert event.end_datetime.hour == end.hour
            assert event.end_datetime.minute == end.minute
            assert event.description == "Workshop de Python"

    def test_create_event_no_title_fails(self, app, db, user_a):
        with app.app_context():
            tz = ZoneInfo("America/Sao_Paulo")
            with pytest.raises(SchedulingError, match="título"):
                SchedulingService.create_event(
                    user_id=user_a.id,
                    title="",
                    start_datetime=datetime(2026, 3, 20, 14, 0, tzinfo=tz),
                )

    def test_create_event_end_before_start_fails(self, app, db, user_a):
        with app.app_context():
            tz = ZoneInfo("America/Sao_Paulo")
            with pytest.raises(SchedulingError, match="término"):
                SchedulingService.create_event(
                    user_id=user_a.id,
                    title="Evento inválido",
                    start_datetime=datetime(2026, 3, 20, 15, 0, tzinfo=tz),
                    end_datetime=datetime(2026, 3, 20, 14, 0, tzinfo=tz),
                )


class TestListEvents:
    """Test event listing and filtering."""

    def test_list_events_empty(self, app, db, user_a):
        with app.app_context():
            events = SchedulingService.list_events(user_id=user_a.id)
            assert events == []

    def test_list_events_returns_user_events(self, app, db, user_a, sample_event):
        with app.app_context():
            events = SchedulingService.list_events(user_id=user_a.id)
            assert len(events) == 1
            assert events[0].title == "Reunião de teste"

    def test_list_events_with_date_filter(self, app, db, user_a, sample_event):
        with app.app_context():
            tz = ZoneInfo("America/Sao_Paulo")
            # Filter for period that includes the event
            events = SchedulingService.list_events(
                user_id=user_a.id,
                start=datetime(2026, 3, 15, 0, 0, tzinfo=tz),
                end=datetime(2026, 3, 15, 23, 59, tzinfo=tz),
            )
            assert len(events) == 1

            # Filter for period that excludes the event
            events = SchedulingService.list_events(
                user_id=user_a.id,
                start=datetime(2026, 3, 16, 0, 0, tzinfo=tz),
            )
            assert len(events) == 0

    def test_list_events_with_keyword(self, app, db, user_a, sample_event):
        with app.app_context():
            events = SchedulingService.list_events(
                user_id=user_a.id, keyword="reunião"
            )
            assert len(events) == 1

            events = SchedulingService.list_events(
                user_id=user_a.id, keyword="inexistente"
            )
            assert len(events) == 0


class TestUpdateEvent:
    """Test event updates."""

    def test_update_title(self, app, db, user_a, sample_event):
        with app.app_context():
            updated = SchedulingService.update_event(
                user_id=user_a.id,
                event_id=sample_event.id,
                title="Título atualizado",
            )
            assert updated.title == "Título atualizado"

    def test_update_nonexistent_fails(self, app, db, user_a):
        with app.app_context():
            with pytest.raises(SchedulingError, match="não encontrado"):
                SchedulingService.update_event(
                    user_id=user_a.id,
                    event_id="00000000-0000-0000-0000-000000000000",
                    title="Nope",
                )


class TestCancelEvent:
    """Test event cancellation."""

    def test_cancel_event(self, app, db, user_a, sample_event):
        with app.app_context():
            cancelled = SchedulingService.cancel_event(
                user_id=user_a.id,
                event_id=sample_event.id,
            )
            assert cancelled.status == "cancelled"

    def test_cancel_already_cancelled_fails(self, app, db, user_a, sample_event):
        with app.app_context():
            SchedulingService.cancel_event(user_a.id, sample_event.id)
            with pytest.raises(SchedulingError, match="já está cancelado"):
                SchedulingService.cancel_event(user_a.id, sample_event.id)


class TestDateParsing:
    """Test safe date parsing."""

    def test_parse_iso_format(self, app):
        with app.app_context():
            dt = SchedulingService.parse_datetime_safe("2026-03-15T14:00:00")
            assert dt.hour == 14
            assert dt.month == 3

    def test_parse_brazilian_format(self, app):
        with app.app_context():
            dt = SchedulingService.parse_datetime_safe("15/03/2026 14:00")
            assert dt.day == 15
            assert dt.hour == 14

    def test_parse_invalid_raises(self, app):
        with app.app_context():
            with pytest.raises(SchedulingError, match="interpretar"):
                SchedulingService.parse_datetime_safe("isso não é uma data")
