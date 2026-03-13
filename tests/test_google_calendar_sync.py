"""Tests for Google Calendar sync service (mocked)."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from zoneinfo import ZoneInfo

from app.models.event import Event
from app.models.calendar_sync import CalendarSync
from app.services.google_calendar_service import GoogleCalendarService


class TestGoogleCalendarSync:
    """Test sync operations with mocked Google API."""

    @patch.object(GoogleCalendarService, "_get_calendar_service")
    def test_push_event_creates_google_event(self, mock_get_service, app, db, user_a, sample_event):
        """Push should create a Google Calendar event and save sync record."""
        with app.app_context():
            mock_service = MagicMock()
            mock_service.events.return_value.insert.return_value.execute.return_value = {
                "id": "google-event-123",
                "etag": '"abc123"',
            }
            mock_get_service.return_value = mock_service

            gc_service = GoogleCalendarService()
            sync = gc_service.push_event(user_a, sample_event)

            assert sync.google_event_id == "google-event-123"
            assert sync.sync_status == "synced"
            assert sync.etag == '"abc123"'

    @patch.object(GoogleCalendarService, "_get_calendar_service")
    def test_push_event_handles_error(self, mock_get_service, app, db, user_a, sample_event):
        """Push should record error without corrupting local data."""
        with app.app_context():
            mock_get_service.side_effect = Exception("API error")

            gc_service = GoogleCalendarService()
            sync = gc_service.push_event(user_a, sample_event)

            assert sync.sync_status == "error"
            assert "API error" in sync.sync_error
            # Local event should be untouched
            assert sample_event.status == "active"

    @patch.object(GoogleCalendarService, "_get_calendar_service")
    def test_delete_event_from_google(self, mock_get_service, app, db, user_a, sample_event):
        """Delete should remove event from Google Calendar."""
        with app.app_context():
            # Create sync record first
            sync = CalendarSync(
                event_id=sample_event.id,
                user_id=user_a.id,
                google_calendar_id="primary",
                google_event_id="google-event-to-delete",
                sync_status="synced",
            )
            db.session.add(sync)
            db.session.commit()

            mock_service = MagicMock()
            mock_service.events.return_value.delete.return_value.execute.return_value = None
            mock_get_service.return_value = mock_service

            gc_service = GoogleCalendarService()
            gc_service.delete_event(user_a, sample_event)

            # Verify delete was called
            mock_service.events.return_value.delete.assert_called_once()
