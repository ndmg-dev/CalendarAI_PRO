"""Scheduling service — business logic for event management."""

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dateutil import parser as dateutil_parser

from app.extensions import db
from app.repositories.event_repository import EventRepository
from app.models.event import Event
from app.models.user import User
from app.services.google_calendar_service import GoogleCalendarService

logger = logging.getLogger(__name__)


class SchedulingError(Exception):
    """Raised when a scheduling operation fails due to business rule violation."""
    pass


class SchedulingService:
    """Business-level operations for event management.

    All methods receive user_id to enforce isolation.
    This is the entry point for AI tools — tools call these methods,
    not the repository directly.
    """

    @staticmethod
    def create_event(
        user_id: str,
        title: str,
        start_datetime: datetime,
        end_datetime: datetime | None = None,
        timezone: str = "America/Sao_Paulo",
        description: str | None = None,
    ) -> Event:
        """Create a new event with business validation.

        Raises:
            SchedulingError: If validation fails.
        """
        # ── Validation ──────────────────────────────────
        if not title or not title.strip():
            raise SchedulingError("O título do evento é obrigatório.")

        if not start_datetime:
            raise SchedulingError("A data/hora de início é obrigatória.")

        # Default end = start + 1 hour
        if end_datetime is None:
            end_datetime = start_datetime + timedelta(hours=1)

        if end_datetime <= start_datetime:
            raise SchedulingError(
                "A data/hora de término deve ser posterior ao início."
            )

        # Ensure timezone-aware datetimes
        tz = ZoneInfo(timezone)
        if start_datetime.tzinfo is None:
            start_datetime = start_datetime.replace(tzinfo=tz)
        if end_datetime.tzinfo is None:
            end_datetime = end_datetime.replace(tzinfo=tz)

        # ── Persist ─────────────────────────────────────
        event = EventRepository.create(
            user_id=user_id,
            title=title.strip(),
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            timezone=timezone,
            description=description.strip() if description else None,
        )

        logger.info("SchedulingService: created event '%s' (%s)", event.title, event.id)
        
        # ── Google Calendar Sync ───────────────────────────
        try:
            user = db.session.get(User, user_id)
            if user and user.calendar_sync_enabled:
                gcal = GoogleCalendarService()
                gcal.push_event(user, event)
        except Exception as e:
            logger.warning("Auto-sync creation failed for user %s: %s", user_id, str(e))

        return event

    @staticmethod
    def list_events(
        user_id: str,
        start: datetime | None = None,
        end: datetime | None = None,
        keyword: str | None = None,
    ) -> list[Event]:
        """List active events for a user."""
        return EventRepository.list_events(
            user_id=user_id,
            start=start,
            end=end,
            keyword=keyword,
            status="active",
        )

    @staticmethod
    def get_event(user_id: str, event_id: str) -> Event:
        """Get a specific event.

        Raises:
            SchedulingError: If event not found or doesn't belong to user.
        """
        event = EventRepository.get_by_id(event_id, user_id)
        if not event:
            raise SchedulingError("Evento não encontrado.")
        return event

    @staticmethod
    def update_event(
        user_id: str,
        event_id: str,
        title: str | None = None,
        description: str | None = None,
        start_datetime: datetime | None = None,
        end_datetime: datetime | None = None,
        timezone: str | None = None,
    ) -> Event:
        """Update an existing event.

        Raises:
            SchedulingError: If event not found or validation fails.
        """
        event = EventRepository.get_by_id(event_id, user_id)
        if not event:
            raise SchedulingError("Evento não encontrado.")

        if event.status == "cancelled":
            raise SchedulingError("Não é possível atualizar um evento cancelado.")

        # Validate datetime consistency
        new_start = start_datetime or event.start_datetime
        new_end = end_datetime or event.end_datetime

        if new_end <= new_start:
            raise SchedulingError(
                "A data/hora de término deve ser posterior ao início."
            )

        updated = EventRepository.update(
            event_id=event_id,
            user_id=user_id,
            title=title.strip() if title else None,
            description=description.strip() if description else None,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            timezone=timezone,
        )

        # ── Google Calendar Sync ───────────────────────────
        try:
            user = db.session.get(User, user_id)
            if user and user.calendar_sync_enabled:
                gcal = GoogleCalendarService()
                gcal.push_event(user, updated)
        except Exception as e:
            logger.warning("Auto-sync update failed for user %s: %s", user_id, str(e))

        return updated

    @staticmethod
    def cancel_event(user_id: str, event_id: str) -> Event:
        """Cancel an event (soft delete).

        Raises:
            SchedulingError: If event not found or already cancelled.
        """
        event = EventRepository.get_by_id(event_id, user_id)
        if not event:
            raise SchedulingError("Evento não encontrado.")

        if event.status == "cancelled":
            raise SchedulingError("Este evento já está cancelado.")

        cancelled = EventRepository.cancel(event_id, user_id)
        logger.info("SchedulingService: cancelled event '%s' (%s)", cancelled.title, cancelled.id)
        
        # ── Google Calendar Sync ───────────────────────────
        try:
            user = db.session.get(User, user_id)
            if user and user.calendar_sync_enabled:
                gcal = GoogleCalendarService()
                gcal.delete_event(user, cancelled)
        except Exception as e:
            logger.warning("Auto-sync cancellation failed for user %s: %s", user_id, str(e))

        return cancelled

    @staticmethod
    def parse_datetime_safe(
        date_str: str,
        timezone: str = "America/Sao_Paulo",
        reference: datetime | None = None,
    ) -> datetime:
        """Parse a date/time string into a timezone-aware datetime.

        Uses dateutil.parser for flexible parsing.

        Args:
            date_str: Date/time string to parse.
            timezone: Target timezone name.
            reference: Reference datetime for relative parsing.

        Raises:
            SchedulingError: If parsing fails.
        """
        tz = ZoneInfo(timezone)

        if reference is None:
            reference = datetime.now(tz)

        try:
            parsed = dateutil_parser.parse(date_str, dayfirst=True, default=reference)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=tz)
            return parsed
        except (ValueError, OverflowError) as e:
            raise SchedulingError(
                f"Não foi possível interpretar a data/hora: '{date_str}'. "
                "Use um formato como '15/03/2026 14:00' ou 'amanhã às 14h'."
            ) from e
