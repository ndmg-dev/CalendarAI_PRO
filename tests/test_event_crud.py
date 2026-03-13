"""Tests for event CRUD via API endpoints."""

import pytest
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.scheduling_service import SchedulingService


class TestEventCRUD:
    """Test event CRUD operations via routes."""

    def test_events_endpoint_returns_user_events(self, app, authenticated_client, db, user_a):
        """GET /agenda/events should return events for authenticated user."""
        with app.app_context():
            tz = ZoneInfo("America/Sao_Paulo")
            SchedulingService.create_event(
                user_id=user_a.id,
                title="Evento via API",
                start_datetime=datetime(2026, 3, 20, 14, 0, tzinfo=tz),
            )

            response = authenticated_client.get("/agenda/events")
            assert response.status_code == 200
            data = response.get_json()
            assert len(data) == 1
            assert data[0]["title"] == "Evento via API"

    def test_events_endpoint_empty(self, authenticated_client):
        """GET /agenda/events should return empty list when no events."""
        response = authenticated_client.get("/agenda/events")
        assert response.status_code == 200
        data = response.get_json()
        assert data == []

    def test_chat_send_requires_message(self, authenticated_client):
        """POST /chat/send should reject empty messages."""
        response = authenticated_client.post(
            "/chat/send",
            data=json.dumps({"message": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_chat_send_requires_json(self, authenticated_client):
        """POST /chat/send should reject non-JSON requests."""
        response = authenticated_client.post(
            "/chat/send",
            data="not json",
            content_type="text/plain",
        )
        assert response.status_code == 400
