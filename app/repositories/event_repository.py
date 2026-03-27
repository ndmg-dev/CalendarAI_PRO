"""Event repository — data access layer for events."""

import logging
from datetime import datetime

from sqlalchemy import and_

from app.extensions import db
from app.models.event import Event

logger = logging.getLogger(__name__)


class EventRepository:
    """Data access for Event model. All queries enforce user isolation."""

    @staticmethod
    def create(
        user_id: str,
        title: str,
        start_datetime: datetime,
        end_datetime: datetime,
        timezone: str = "America/Sao_Paulo",
        description: str | None = None,
    ) -> Event:
        """Create a new event for the given user."""
        event = Event(
            user_id=user_id,
            title=title,
            description=description,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            timezone=timezone,
            status="active",
        )
        db.session.add(event)
        db.session.commit()
        logger.info("Event created: '%s' for user %s", title, user_id)
        return event

    @staticmethod
    def get_by_id(event_id: str, user_id: str) -> Event | None:
        """Get a single event by ID, scoped to the user."""
        return db.session.query(Event).filter(
            and_(Event.id == event_id, Event.user_id == user_id)
        ).first()

    @staticmethod
    def list_events(
        user_id: str,
        start: datetime | None = None,
        end: datetime | None = None,
        status: str = "active",
        keyword: str | None = None,
    ) -> list[Event]:
        """List events for a user, with optional date range and keyword filter."""
        query = db.session.query(Event).filter(
            and_(Event.user_id == user_id, Event.status == status)
        )

        if start:
            # Event ends after or on query start
            query = query.filter(Event.end_datetime >= start)
        if end:
            # Event starts before or on query end
            query = query.filter(Event.start_datetime <= end)
        if keyword:
            like_pattern = f"%{keyword}%"
            query = query.filter(
                Event.title.ilike(like_pattern) | Event.description.ilike(like_pattern)
            )

        return query.order_by(Event.start_datetime.asc()).all()

    @staticmethod
    def update(
        event_id: str,
        user_id: str,
        **kwargs,
    ) -> Event | None:
        """Update event fields. Only updates fields present in kwargs."""
        event = EventRepository.get_by_id(event_id, user_id)
        if not event:
            return None

        allowed_fields = {"title", "description", "start_datetime", "end_datetime", "timezone", "status"}
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(event, key, value)

        db.session.commit()
        logger.info("Event updated: '%s' (%s)", event.title, event_id)
        return event

    @staticmethod
    def cancel(event_id: str, user_id: str) -> Event | None:
        """Cancel an event (soft delete by setting status to 'cancelled')."""
        event = EventRepository.get_by_id(event_id, user_id)
        if not event:
            return None

        event.status = "cancelled"
        db.session.commit()
        logger.info("Event cancelled: '%s' (%s)", event.title, event_id)
        return event
