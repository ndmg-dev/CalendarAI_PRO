"""Tests for auth flow and route protection."""

import pytest


class TestAuthRoutes:
    """Test authentication routes."""

    def test_login_page_accessible(self, client):
        """Login page should be accessible without authentication."""
        response = client.get("/auth/login")
        assert response.status_code == 200
        assert b"Entrar com Google" in response.data

    def test_chat_requires_auth(self, client):
        """Chat page should redirect unauthenticated users."""
        response = client.get("/chat/", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.headers.get("Location", "")

    def test_agenda_requires_auth(self, client):
        """Agenda page should redirect unauthenticated users."""
        response = client.get("/agenda/", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.headers.get("Location", "")

    def test_health_check(self, client):
        """Health check should always be accessible."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["app"] == "CalendAI PRO"


class TestAuthenticatedAccess:
    """Test that authenticated users can access protected pages."""

    def test_chat_page_loads(self, authenticated_client):
        """Authenticated user should access chat page."""
        response = authenticated_client.get("/chat/")
        assert response.status_code == 200
        assert b"chat-container" in response.data

    def test_agenda_page_loads(self, authenticated_client):
        """Authenticated user should access agenda page."""
        response = authenticated_client.get("/agenda/")
        assert response.status_code == 200
        assert b"agenda-container" in response.data

    def test_events_api_returns_json(self, authenticated_client):
        """Events API should return JSON array."""
        response = authenticated_client.get("/agenda/events")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
